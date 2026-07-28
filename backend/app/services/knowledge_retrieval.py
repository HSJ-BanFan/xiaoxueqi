from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Literal, Optional, Protocol, Sequence

import httpx
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import KnowledgeBase, KnowledgeChunk


logger = logging.getLogger(__name__)

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:[._+%-][a-z0-9]+)*|[\u3400-\u9fff]+", re.IGNORECASE)
_NON_WORD_PATTERN = re.compile(r"[\W_]+", re.UNICODE)
_TITLE_COVERAGE_BOOST = 8.0
_TITLE_EXACT_PHRASE_BOOST = 4.0
_QUERY_SYNONYMS = {
    "低血糖": ("血糖过低",),
    "高血糖": ("血糖过高",),
    "运动": ("身体活动", "体力活动", "健康生活"),
    "锻炼": ("身体活动", "体力活动", "健康生活"),
    "a1c": ("糖化血红蛋白",),
    "糖化": ("a1c", "糖化血红蛋白"),
    "碳水": ("碳水化合物",),
    "确诊": ("测试", "诊断"),
    "筛查": ("测试", "诊断"),
    "复查": ("检查", "测试"),
    "1 型糖尿病": ("类型 1 糖尿病",),
    "1型糖尿病": ("类型 1 糖尿病",),
    "2 型糖尿病": ("类型 2 糖尿病",),
    "2型糖尿病": ("类型 2 糖尿病",),
    "生完孩子": ("宝宝出生后", "产后"),
    "双脚": ("足部", "足部护理"),
    "糖尿病足": ("足部问题", "足部护理"),
    "眼底": ("眼部", "糖尿病眼病"),
}


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    chunk_id: str
    document_id: str
    title: str
    source_key: str
    source_url: Optional[str] = None
    license: Optional[str] = None
    retrieved_at: Optional[str] = None
    text_zh: str
    text_en: Optional[str] = None
    score: float


class RetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citations: List[Citation]
    count: int
    retrieval: Literal["bm25", "bm25+vector"]
    degraded: bool


class Embedder(Protocol):
    def embed(self, text: str) -> List[float]: ...


class EmbeddingClientError(RuntimeError):
    pass


class OpenAIEmbeddingClient:
    """Minimal synchronous OpenAI-compatible embeddings client."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.base_url = (base_url if base_url is not None else settings.EMBEDDING_BASE_URL).rstrip("/")
        self.api_key = settings.EMBEDDING_API_KEY if api_key is None else api_key
        self.model = model if model is not None else settings.EMBEDDING_MODEL
        self.model_name = self.model
        self.timeout_seconds = (
            settings.EMBEDDING_TIMEOUT_SECONDS
            if timeout_seconds is None
            else timeout_seconds
        )
        self.transport = transport

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/embeddings"

    def embed(self, text: str) -> List[float]:
        if not self.base_url or not self.model:
            raise EmbeddingClientError("embedding 服务未配置")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = client.post(
                    self.endpoint,
                    headers=headers,
                    json={"model": self.model, "input": text},
                )
                response.raise_for_status()
                body = response.json()
            vector = body["data"][0]["embedding"]
            if not isinstance(vector, list) or not vector:
                raise TypeError("embedding is not a non-empty list")
            return [float(value) for value in vector]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.info("Embedding request failed at %s: %s", self.endpoint, exc.__class__.__name__)
            raise EmbeddingClientError("embedding 服务暂不可用") from exc


@dataclass(frozen=True)
class _ChunkRecord:
    chunk_id: str
    document_id: str
    title: str
    source_key: str
    source_url: Optional[str]
    license: Optional[str]
    retrieved_at: Optional[datetime]
    text_zh: str
    text_en: Optional[str]
    embedding: Optional[List[float]]
    embedding_model: Optional[str]


class _BM25Index:
    def __init__(self, records: Sequence[_ChunkRecord]) -> None:
        self.records = list(records)
        self.term_frequencies: List[Counter[str]] = []
        self.document_lengths: List[int] = []
        self.postings: Dict[str, List[int]] = defaultdict(list)

        for record_index, record in enumerate(self.records):
            frequencies = Counter(tokenize(record.text_zh))
            frequencies.update(tokenize(record.title) * 4)
            self.term_frequencies.append(frequencies)
            self.document_lengths.append(sum(frequencies.values()))
            for term in frequencies:
                self.postings[term].append(record_index)

    def search(
        self,
        query: str,
        *,
        source_key: Optional[str] = None,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> List[str]:
        query_terms = list(dict.fromkeys(tokenize(query)))
        if not query_terms or not self.records:
            return []

        allowed = {
            index
            for index, record in enumerate(self.records)
            if source_key is None or record.source_key == source_key
        }
        if not allowed:
            return []

        average_length = sum(self.document_lengths[index] for index in allowed) / len(allowed)
        average_length = average_length or 1.0
        scores: Dict[int, float] = defaultdict(float)

        for term in query_terms:
            posting = [index for index in self.postings.get(term, []) if index in allowed]
            if not posting:
                continue
            document_frequency = len(posting)
            inverse_document_frequency = math.log(
                1.0 + (len(allowed) - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            for record_index in posting:
                frequency = self.term_frequencies[record_index][term]
                length = self.document_lengths[record_index]
                denominator = frequency + k1 * (1.0 - b + b * length / average_length)
                scores[record_index] += inverse_document_frequency * (
                    frequency * (k1 + 1.0) / denominator
                )

        query_term_set = set(query_terms)
        normalized_query = _normalize_for_phrase_match(query)
        for record_index in allowed:
            title = self.records[record_index].title
            title_terms = set(tokenize(title))
            if title_terms:
                title_coverage = len(query_term_set & title_terms) / len(title_terms)
                scores[record_index] += _TITLE_COVERAGE_BOOST * title_coverage

            normalized_title = _normalize_for_phrase_match(title)
            if normalized_title and (
                normalized_title in normalized_query or normalized_query in normalized_title
            ):
                scores[record_index] += _TITLE_EXACT_PHRASE_BOOST

        ranked = sorted(
            scores,
            key=lambda index: (-scores[index], self.records[index].chunk_id),
        )
        return [self.records[index].chunk_id for index in ranked if scores[index] > 0]


@dataclass
class _CachedCorpus:
    fingerprint: str
    index: _BM25Index
    by_id: Dict[str, _ChunkRecord]


_CACHE_LOCK = threading.Lock()
_INDEX_CACHE: Optional[_CachedCorpus] = None


def tokenize(text: str) -> List[str]:
    """Tokenize Chinese as character bigrams and retain ASCII words."""
    tokens: List[str] = []
    for match in _TOKEN_PATTERN.finditer((text or "").lower()):
        value = match.group(0)
        if "\u3400" <= value[0] <= "\u9fff":
            if len(value) == 1:
                tokens.append(value)
            else:
                tokens.extend(value[index : index + 2] for index in range(len(value) - 1))
        else:
            tokens.append(value)
    return tokens


def expand_query(query: str) -> str:
    """Append a small, deterministic self-management synonym set for BM25."""
    normalized = (query or "").lower()
    values = [query]
    for trigger, synonyms in _QUERY_SYNONYMS.items():
        if trigger in normalized:
            values.extend(synonyms)
    return " ".join(dict.fromkeys(value for value in values if value))


def _normalize_for_phrase_match(text: str) -> str:
    return _NON_WORD_PATTERN.sub("", (text or "").lower())


def reciprocal_rank_fusion(
    rankings: Iterable[Sequence[str]],
    *,
    rank_constant: int = 60,
) -> Dict[str, float]:
    scores: Dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] += 1.0 / (rank_constant + rank)
    return dict(scores)


def clear_knowledge_index_cache() -> None:
    """Clear the process-local index cache, primarily for tests and reseeding."""
    global _INDEX_CACHE
    with _CACHE_LOCK:
        _INDEX_CACHE = None


class KnowledgeRetriever:
    def __init__(self, db: Session, embedder: Optional[Embedder] = None) -> None:
        self.db = db
        self._vector_requested = embedder is not None or settings.EMBEDDING_ENABLED
        if embedder is not None:
            self.embedder = embedder
        elif settings.EMBEDDING_ENABLED and settings.EMBEDDING_BASE_URL and settings.EMBEDDING_MODEL:
            self.embedder = OpenAIEmbeddingClient()
        else:
            self.embedder = None

    def search(
        self,
        query: str,
        *,
        limit: int = 3,
        source_key: Optional[str] = None,
    ) -> RetrievalResult:
        query = (query or "").strip()
        if not 2 <= len(query) <= 200:
            raise ValueError("query 长度必须在 2 到 200 个字符之间")
        if not 1 <= limit <= 5:
            raise ValueError("limit 必须在 1 到 5 之间")
        if source_key is not None and len(source_key) > 32:
            raise ValueError("source_key 长度不能超过 32")

        corpus = self._load_corpus()
        if not corpus.index.records:
            return RetrievalResult(
                citations=[],
                count=0,
                retrieval="bm25",
                degraded=False,
            )

        bm25_ranking = corpus.index.search(expand_query(query), source_key=source_key)
        vector_ranking: List[str] = []
        degraded = False

        if self._vector_requested:
            if self.embedder is None:
                degraded = True
            else:
                try:
                    vector_ranking = self._vector_search(
                        query,
                        corpus.index.records,
                        source_key=source_key,
                    )
                    if not vector_ranking:
                        degraded = True
                except Exception as exc:
                    logger.info("Knowledge vector search degraded after %s", exc.__class__.__name__)
                    vector_ranking = []
                    degraded = True

        rankings: List[Sequence[str]] = [bm25_ranking]
        retrieval: Literal["bm25", "bm25+vector"] = "bm25"
        if vector_ranking:
            rankings.append(vector_ranking)
            retrieval = "bm25+vector"

        fused_scores = reciprocal_rank_fusion(rankings)
        fused_ranking = sorted(
            fused_scores,
            key=lambda chunk_id: (-fused_scores[chunk_id], chunk_id),
        )
        ranked_ids: List[str] = []
        repeated_chunk_ids: List[str] = []
        seen_documents: set[str] = set()
        for chunk_id in fused_ranking:
            document_id = corpus.by_id[chunk_id].document_id
            if document_id in seen_documents:
                repeated_chunk_ids.append(chunk_id)
                continue
            ranked_ids.append(chunk_id)
            seen_documents.add(document_id)
            if len(ranked_ids) == limit:
                break

        if len(ranked_ids) < limit:
            ranked_ids.extend(repeated_chunk_ids[: limit - len(ranked_ids)])

        citations = [
            self._citation(corpus.by_id[chunk_id], index, fused_scores[chunk_id])
            for index, chunk_id in enumerate(ranked_ids, start=1)
        ]
        return RetrievalResult(
            citations=citations,
            count=len(citations),
            retrieval=retrieval,
            degraded=degraded,
        )

    def _load_corpus(self) -> _CachedCorpus:
        global _INDEX_CACHE
        fingerprint = self._corpus_fingerprint()
        with _CACHE_LOCK:
            if _INDEX_CACHE is not None and _INDEX_CACHE.fingerprint == fingerprint:
                return _INDEX_CACHE

            rows = (
                self.db.query(KnowledgeChunk, KnowledgeBase)
                .join(KnowledgeBase, KnowledgeChunk.document_id == KnowledgeBase.id)
                .order_by(KnowledgeChunk.document_id, KnowledgeChunk.chunk_index)
                .all()
            )
            records = [self._record(chunk, document) for chunk, document in rows]
            _INDEX_CACHE = _CachedCorpus(
                fingerprint=fingerprint,
                index=_BM25Index(records),
                by_id={record.chunk_id: record for record in records},
            )
            return _INDEX_CACHE

    def _corpus_fingerprint(self) -> str:
        rows = (
            self.db.query(
                KnowledgeChunk.id,
                KnowledgeChunk.document_id,
                KnowledgeChunk.created_at,
                KnowledgeBase.content_hash,
                KnowledgeBase.updated_at,
            )
            .join(KnowledgeBase, KnowledgeChunk.document_id == KnowledgeBase.id)
            .order_by(KnowledgeChunk.id)
            .all()
        )
        digest = hashlib.sha256()
        for row in rows:
            digest.update(
                json.dumps(
                    [
                        row.id,
                        row.document_id,
                        _isoformat(row.created_at),
                        row.content_hash,
                        _isoformat(row.updated_at),
                    ],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
        return f"{len(rows)}:{digest.hexdigest()}"

    def _vector_search(
        self,
        query: str,
        records: Sequence[_ChunkRecord],
        *,
        source_key: Optional[str],
    ) -> List[str]:
        if self.embedder is None:
            return []
        query_vector = self.embedder.embed(query)
        if not query_vector:
            raise EmbeddingClientError("query embedding 为空")

        expected_model = getattr(self.embedder, "model_name", None)
        scored: List[tuple[str, float]] = []
        for record in records:
            if source_key is not None and record.source_key != source_key:
                continue
            if not record.embedding or len(record.embedding) != len(query_vector):
                continue
            if expected_model and record.embedding_model and record.embedding_model != expected_model:
                continue
            similarity = _cosine_similarity(query_vector, record.embedding)
            if similarity is not None:
                scored.append((record.chunk_id, similarity))

        scored.sort(key=lambda item: (-item[1], item[0]))
        return [chunk_id for chunk_id, _ in scored]

    @staticmethod
    def _record(chunk: KnowledgeChunk, document: KnowledgeBase) -> _ChunkRecord:
        embedding = None
        if isinstance(chunk.embedding, list):
            try:
                embedding = [float(value) for value in chunk.embedding]
            except (TypeError, ValueError):
                embedding = None
        return _ChunkRecord(
            chunk_id=chunk.id,
            document_id=document.id,
            title=document.title,
            source_key=document.source_key or document.source or "unknown",
            source_url=document.source_url,
            license=document.license,
            retrieved_at=document.retrieved_at,
            text_zh=chunk.text_zh,
            text_en=chunk.text_en,
            embedding=embedding,
            embedding_model=chunk.embedding_model,
        )

    @staticmethod
    def _citation(record: _ChunkRecord, index: int, score: float) -> Citation:
        return Citation(
            index=index,
            chunk_id=record.chunk_id,
            document_id=record.document_id,
            title=record.title,
            source_key=record.source_key,
            source_url=record.source_url,
            license=record.license,
            retrieved_at=_isoformat(record.retrieved_at),
            text_zh=record.text_zh,
            text_en=record.text_en,
            score=round(score, 8),
        )


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> Optional[float]:
    if not left or len(left) != len(right):
        return None
    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return None
    return dot_product / (left_norm * right_norm)


def _isoformat(value: Optional[date | datetime]) -> Optional[str]:
    return value.isoformat() if value is not None else None
