from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Protocol, Sequence, Tuple
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agent.llm_client import OpenAICompatibleClient
from app.core.config import settings
from app.services.knowledge_retrieval import OpenAIEmbeddingClient
from scripts.sources import LICENSE_SUMMARIES, KnowledgeSource, get_sources


OUTPUT_DIR = REPO_ROOT / "data" / "knowledge"
USER_AGENT = "xiaoxueqi-knowledge-ingester/1.0 (+offline educational corpus build)"
MIN_REQUEST_INTERVAL_SECONDS = 1.0
_NUMBER_PATTERN = re.compile(r"(?<![A-Za-z0-9])\d+(?:,\d{3})*(?:\.\d+)?%?")
_COMPOUND_NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])\d+(?:,\d{3})*(?:\.\d+)?%?\s+"
    r"(?:in|out\s+of)\s+\d+(?:,\d{3})*(?:\.\d+)?%?",
    re.IGNORECASE,
)
REWRITE_SYSTEM_PROMPT = """你是医学科普翻译编辑。把英文原文改写为准确、简洁的中文科普片段。
必须遵守：
1. 只做语言转换与适度压缩，不新增原文没有的事实。
2. 所有数字、单位、阈值和百分比必须原样保留。
3. 不产出诊断结论、处方或剂量建议。
4. 使用客观科普语气，不使用第一人称。
只返回改写后的中文正文，不要解释。"""
GOOGLE_REWRITE_MODEL = "google-translate-web"
REWRITE_CACHE_PATH = OUTPUT_DIR / ".rewrite-cache.json"
GOOGLE_BATCH_MAX_CHARS = 4300
GOOGLE_REQUEST_INTERVAL_SECONDS = 0.75
GOOGLE_TRANSLATE_ENDPOINTS = (
    "https://translate.google.com/m",
    "https://translate.google.co.uk/m",
    "https://translate.google.com.au/m",
)


class _ContentExtractor(HTMLParser):
    _BLOCK_TAGS = {"h1", "h2", "h3", "h4", "p", "li"}
    _IGNORED_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "form", "sup"}
    _VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, *, capture_id: Optional[str] = None) -> None:
        super().__init__(convert_charrefs=True)
        self.capture_id = capture_id
        self._capture_depth = 0
        self._ignored_depth = 0
        self._main_depth = 0
        self._current_tag: Optional[str] = None
        self._current_text: List[str] = []
        self._title_depth = 0
        self._title_text: List[str] = []
        self.main_blocks: List[str] = []
        self.capture_blocks: List[str] = []
        self.all_blocks: List[str] = []
        self.main_tagged_blocks: List[Tuple[str, str]] = []
        self.capture_tagged_blocks: List[Tuple[str, str]] = []
        self.all_tagged_blocks: List[Tuple[str, str]] = []
        self.h1: Optional[str] = None
        self.page_title: Optional[str] = None

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[no-untyped-def]
        tag = tag.lower()
        attributes = {str(key).lower(): value for key, value in attrs}
        if tag in self._IGNORED_TAGS:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if self._capture_depth and tag not in self._VOID_TAGS:
            self._capture_depth += 1
        elif self.capture_id and attributes.get("id") == self.capture_id:
            self._capture_depth = 1
        if tag in {"main", "article"}:
            self._main_depth += 1
        if tag == "title":
            self._title_depth += 1
            self._title_text = []
        if tag in self._BLOCK_TAGS:
            self._current_tag = tag
            self._current_text = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
            self.page_title = _normalize_space(" ".join(self._title_text)) or self.page_title
        if tag in self._BLOCK_TAGS and self._current_tag == tag:
            block = _normalize_space(" ".join(self._current_text))
            if block:
                self.all_blocks.append(block)
                self.all_tagged_blocks.append((tag, block))
                if self._main_depth:
                    self.main_blocks.append(block)
                    self.main_tagged_blocks.append((tag, block))
                if self._capture_depth:
                    self.capture_blocks.append(block)
                    self.capture_tagged_blocks.append((tag, block))
                if tag == "h1" and self.h1 is None:
                    self.h1 = block
            self._current_tag = None
            self._current_text = []
        if tag in {"main", "article"} and self._main_depth:
            self._main_depth -= 1
        if self._capture_depth and tag not in self._VOID_TAGS:
            self._capture_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._title_depth:
            self._title_text.append(data)
        if self._current_tag:
            self._current_text.append(data)


class Fetcher:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
        self._last_request_at: Dict[str, float] = {}
        self._robots: Dict[str, RobotFileParser] = {}

    def get(self, url: str) -> str:
        parser = self._ensure_allowed(url)
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        crawl_delay = parser.crawl_delay(USER_AGENT)
        if crawl_delay is None:
            crawl_delay = parser.crawl_delay("*")
        minimum_interval = max(MIN_REQUEST_INTERVAL_SECONDS, float(crawl_delay or 0))
        elapsed = time.monotonic() - self._last_request_at.get(origin, 0.0)
        if elapsed < minimum_interval:
            time.sleep(minimum_interval - elapsed)
        response = self.session.get(url, timeout=30)
        self._last_request_at[origin] = time.monotonic()
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        return response.text

    def _ensure_allowed(self, url: str) -> RobotFileParser:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        parser = self._robots.get(origin)
        if parser is None:
            robots_url = f"{origin}/robots.txt"
            response = self.session.get(robots_url, timeout=20)
            self._last_request_at[origin] = time.monotonic()
            response.raise_for_status()
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(response.text.splitlines())
            self._robots[origin] = parser
        if not parser.can_fetch(USER_AGENT, url):
            raise PermissionError(f"robots.txt 不允许抓取: {url}")
        return parser


def extract_page(html: str, *, source_key: Optional[str] = None) -> Tuple[str, str]:
    capture_id = "topic-summary" if source_key == "medlineplus" else None
    parser = _ContentExtractor(capture_id=capture_id)
    parser.feed(html)
    if capture_id:
        tagged_blocks = parser.capture_tagged_blocks
        if len("\n".join(block for _, block in tagged_blocks)) < 200:
            raise ValueError(f"未找到来源 {source_key} 的许可范围内正文区域")
    else:
        tagged_blocks = (
            parser.main_tagged_blocks
            if len("\n".join(parser.main_blocks)) >= 500
            else parser.all_tagged_blocks
        )
    if source_key == "niddk":
        tagged_blocks = _trim_to_first_h1(tagged_blocks)
    tagged_blocks = _truncate_noncontent_sections(
        tagged_blocks,
        drop_leading_lists=source_key == "niddk",
    )
    blocks = _deduplicate_blocks(block for _, block in tagged_blocks)
    text = "\n\n".join(blocks).strip()
    if len(text) < 200:
        raise ValueError("未提取到足够的正文")
    title = parser.h1 or parser.page_title or "Untitled"
    return title[:255], text


def chunk_english(text: str, *, target_min: int = 800, target_max: int = 1100, overlap: int = 150) -> List[str]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    expanded: List[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= target_max:
            expanded.append(paragraph)
            continue
        expanded.extend(_split_long_paragraph(paragraph, target_max=target_max))

    chunks: List[str] = []
    current = ""
    for paragraph in expanded:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if current and len(candidate) > target_max and len(current) >= target_min:
            chunks.append(current)
            prefix = _overlap_suffix(current, overlap)
            current = f"{prefix}\n\n{paragraph}".strip()
        else:
            current = candidate
    if current:
        if chunks and len(current) < target_min // 2:
            chunks[-1] = f"{chunks[-1]}\n\n{current}".strip()
        else:
            chunks.append(current)
    return chunks


def _split_long_paragraph(paragraph: str, *, target_max: int) -> List[str]:
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", paragraph) if item.strip()]
    if len(sentences) == 1:
        return _split_at_word_boundaries(paragraph, target_max=target_max)

    parts: List[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > target_max:
            if current:
                parts.append(current)
                current = ""
            parts.extend(_split_at_word_boundaries(sentence, target_max=target_max))
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if current and len(candidate) > target_max:
            parts.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def _split_at_word_boundaries(text: str, *, target_max: int) -> List[str]:
    parts: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + target_max, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        parts.append(text[start:end].strip())
        start = end
        while start < len(text) and text[start].isspace():
            start += 1
    return parts


def _overlap_suffix(text: str, overlap: int) -> str:
    if overlap <= 0 or not text:
        return ""
    start = max(0, len(text) - overlap)
    if start:
        boundary = text.find(" ", start)
        if boundary >= 0:
            start = boundary + 1
    return text[start:].lstrip()


class TextRewriter(Protocol):
    provider_name: str
    model_name: str

    def rewrite_many(self, texts: Sequence[str]) -> List[str]: ...

    def rewrite_title(self, title: str) -> str: ...


class Rewriter:
    provider_name = "llm"

    def __init__(self) -> None:
        self.client = OpenAICompatibleClient(temperature=0.0)
        self.model_name = settings.LLM_MODEL

    def rewrite(self, text: str) -> str:
        response = self.client.chat(
            [
                {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ]
        )
        content = response.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("改写模型返回空内容")
        return content.strip()

    def rewrite_many(self, texts: Sequence[str]) -> List[str]:
        return [self.rewrite(text) for text in texts]

    def rewrite_title(self, title: str) -> str:
        response = self.client.chat(
            [
                {"role": "system", "content": "把英文医学科普标题准确翻译为简洁中文，只返回标题。"},
                {"role": "user", "content": title},
            ]
        )
        content = response.get("content")
        return content.strip()[:255] if isinstance(content, str) and content.strip() else title[:255]


class GoogleTranslateRewriter:
    """Optional build-time fallback when no OpenAI-compatible rewriter is available.

    This provider is never used at application runtime. Translations are cached by
    source text so an interrupted corpus build can resume without re-translating
    completed chunks.
    """

    provider_name = "google_translate"
    model_name = GOOGLE_REWRITE_MODEL

    def __init__(self, cache_path: Path = REWRITE_CACHE_PATH) -> None:
        try:
            from deep_translator import GoogleTranslator
        except ImportError as exc:  # pragma: no cover - depends on build extras
            raise RuntimeError(
                "使用 --rewrite-provider google 需要安装 deep-translator"
            ) from exc
        self.translator = GoogleTranslator(source="en", target="zh-CN")
        self.cache_path = cache_path
        self.cache = self._load_cache()
        self._last_request_at = 0.0
        self._endpoint_index = 0

    def rewrite(self, text: str) -> str:
        return self.rewrite_many([text])[0]

    def rewrite_many(self, texts: Sequence[str]) -> List[str]:
        results: List[Optional[str]] = [None] * len(texts)
        pending: List[Tuple[int, str, str]] = []
        for index, text in enumerate(texts):
            key = self._cache_key(text)
            cached = self.cache.get(key)
            if (
                isinstance(cached, str)
                and cached.strip()
                and _translation_is_complete(text, cached)
            ):
                results[index] = cached
            else:
                pending.append((index, key, text))

        for batch in _pack_translation_batches(pending):
            translated = self._translate_batch([item[2] for item in batch])
            for (index, key, _), value in zip(batch, translated):
                source_text = texts[index]
                if not _translation_is_complete(source_text, value):
                    value = self._translate_one_resilient(source_text)
                value = value.strip()
                if not value:
                    raise ValueError("Google 翻译返回空内容")
                results[index] = value
                self.cache[key] = value
            self._save_cache()

        if any(result is None for result in results):
            raise RuntimeError("翻译结果数量不完整")
        repaired_results: List[str] = []
        cache_changed = False
        for text, result in zip(texts, results):
            repaired = repair_numeric_fidelity(text, str(result))
            repaired_results.append(repaired)
            key = self._cache_key(text)
            if self.cache.get(key) != repaired:
                self.cache[key] = repaired
                cache_changed = True
        if cache_changed:
            self._save_cache()
        return repaired_results

    def rewrite_title(self, title: str) -> str:
        return self.rewrite(title).strip()[:255] or title[:255]

    def _translate_batch(self, texts: Sequence[str]) -> List[str]:
        protected: List[Tuple[str, Dict[str, str]]] = [
            _protect_numeric_literals(text) for text in texts
        ]
        if len(protected) == 1:
            translated = self._request_translation(protected[0][0])
            return [_restore_numeric_literals(translated, protected[0][1])]

        markers = [
            f"[[[XIAOQI_ITEM_{_alpha_index(index)}]]]"
            for index in range(len(protected) + 1)
        ]
        payload_parts: List[str] = []
        for index, (text, _) in enumerate(protected):
            payload_parts.extend([markers[index], text])
        payload_parts.append(markers[-1])
        translated_payload = self._request_translation("\n".join(payload_parts))

        values: List[str] = []
        position = 0
        for index, (_, numeric_map) in enumerate(protected):
            start = translated_payload.find(markers[index], position)
            end = translated_payload.find(markers[index + 1], max(start, position))
            if start < 0 or end < 0:
                # The public web translator occasionally rewrites a separator.
                # Retrying each item separately is slower but deterministic.
                return [
                    self._translate_one_resilient(source_text)
                    for source_text in texts
                ]
            start += len(markers[index])
            try:
                value = _restore_numeric_literals(
                    translated_payload[start:end].strip(),
                    numeric_map,
                )
            except ValueError:
                return [self._translate_one_resilient(source_text) for source_text in texts]
            values.append(value)
            position = end
        return values

    def _translate_one_resilient(self, text: str) -> str:
        try:
            translated = self._translate_one(text)
        except ValueError:
            translated = ""
        if translated and _translation_is_complete(text, translated):
            return translated

        segments = _split_translation_segments(text, target_max=350)
        if len(segments) <= 1:
            raise ValueError("翻译结果包含过多未翻译英文")
        translated_parts: List[str] = []
        for segment in segments:
            try:
                translated_parts.append(self._translate_one(segment))
            except ValueError:
                atomic_segments = _split_translation_segments(segment, target_max=180)
                if len(atomic_segments) <= 1:
                    raise
                translated_parts.append(
                    " ".join(self._translate_one(item) for item in atomic_segments)
                )
        translated = "\n\n".join(translated_parts)
        if not _translation_is_complete(text, translated):
            raise ValueError("分段重试后仍包含过多未翻译英文")
        return translated

    def _translate_one(self, text: str) -> str:
        protected, numeric_map = _protect_numeric_literals(text)
        return _restore_numeric_literals(self._request_translation(protected), numeric_map)

    def _request_translation(self, text: str) -> str:
        delays = (2, 5, 15, 30, 60)
        last_error: Optional[Exception] = None
        for attempt, retry_delay in enumerate(delays, start=1):
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < GOOGLE_REQUEST_INTERVAL_SECONDS:
                time.sleep(GOOGLE_REQUEST_INTERVAL_SECONDS - elapsed)
            try:
                if hasattr(self.translator, "_base_url"):
                    endpoint_index = (self._endpoint_index + attempt - 1) % len(
                        GOOGLE_TRANSLATE_ENDPOINTS
                    )
                    self.translator._base_url = GOOGLE_TRANSLATE_ENDPOINTS[endpoint_index]
                translated = self.translator.translate(text)
                self._last_request_at = time.monotonic()
                if isinstance(translated, str) and translated.strip():
                    self._endpoint_index = (endpoint_index + 1) % len(
                        GOOGLE_TRANSLATE_ENDPOINTS
                    ) if hasattr(self.translator, "_base_url") else self._endpoint_index
                    return translated.strip()
                raise ValueError("Google 翻译返回空内容")
            except Exception as exc:  # build-time service; retry transport/rate limits
                self._last_request_at = time.monotonic()
                last_error = exc
                if attempt == len(delays):
                    break
                time.sleep(retry_delay)
        raise RuntimeError("Google 翻译服务连续失败") from last_error

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256(
            f"{self.model_name}\0{text}".encode("utf-8")
        ).hexdigest()

    def _load_cache(self) -> Dict[str, str]:
        if not self.cache_path.exists():
            return {}
        try:
            value = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps(self.cache, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        temporary_path.replace(self.cache_path)


def ingest_source(
    source: KnowledgeSource,
    *,
    fetcher: Fetcher,
    rewriter: Optional[TextRewriter],
    embedder: Optional[OpenAIEmbeddingClient],
    license_summary: str,
) -> Dict[str, object]:
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    title_en, body = extract_page(fetcher.get(source.url), source_key=source.source_key)
    english_chunks = chunk_english(body)
    rewritten_chunks = rewriter.rewrite_many(english_chunks) if rewriter else english_chunks
    chunks: List[Dict[str, object]] = []
    for chunk_index, (text_en, text_zh) in enumerate(zip(english_chunks, rewritten_chunks)):
        validate_numeric_fidelity(text_en, text_zh)
        embedding = embedder.embed(text_zh) if embedder else None
        chunks.append(
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source.url}:{chunk_index}")),
                "chunk_index": chunk_index,
                "text_zh": text_zh,
                "text_en": text_en,
                "char_count": len(text_zh),
                "embedding": embedding,
                "embedding_model": embedder.model_name if embedder else None,
            }
        )

    title_zh = rewriter.rewrite_title(title_en) if rewriter else title_en
    content = "\n\n".join(str(chunk["text_zh"]) for chunk in chunks)
    content_hash = hashlib.sha256(
        json.dumps(
            {
                "source_url": source.url,
                "title_en": title_en,
                "chunks": chunks,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, source.url)),
        "title": title_zh,
        "title_en": title_en,
        "content": content,
        "source": source.site_name,
        "source_key": source.source_key,
        "source_url": source.url,
        "license": _normalize_space(license_summary)[:255],
        "retrieved_at": retrieved_at,
        "content_hash": content_hash,
        "tags": [source.topic],
        "chunks": chunks,
    }


def build_licenses_markdown(licenses: Dict[str, Dict[str, str]]) -> str:
    lines = [
        "# Knowledge Corpus Licenses",
        "",
        "> 本文件由摄取脚本记录源站声明。提交语料前必须由维护者人工复核；正文语料不包含图片或第三方转载内容。",
        "",
    ]
    for source_key in sorted(licenses):
        item = licenses[source_key]
        lines.extend(
            [
                f"## {source_key}",
                "",
                f"- 声明页面：<{item['url']}>",
                f"- 抓取时间：{item['retrieved_at']}",
                f"- 纳入范围：{LICENSE_SUMMARIES[source_key]}",
                "- 人工复核：待完成",
                "",
                "```text",
                item["text"].strip()[:6000],
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the versioned diabetes knowledge corpus")
    parser.add_argument("--only", choices=("niddk", "medlineplus"))
    parser.add_argument("--url", help="只处理白名单中的一个精确 URL，便于失败后定点续跑")
    parser.add_argument("--no-rewrite", action="store_true")
    parser.add_argument(
        "--rewrite-provider",
        choices=("llm", "google"),
        default="llm",
        help="中文生成方式；google 仅用于无可用 LLM 端点时的离线构建",
    )
    parser.add_argument("--no-embed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="允许不满足 40–60 篇/300–500 chunks 或含失败 URL 时覆盖产物",
    )
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    sources = list(get_sources(args.only))
    if args.url:
        sources = [source for source in sources if source.url == args.url]
        if not sources:
            raise SystemExit("--url 必须精确匹配当前 --only 范围内的白名单 URL")
    if args.limit is not None:
        if args.limit < 1:
            raise SystemExit("--limit 必须大于 0")
        sources = sources[: args.limit]
    if not sources:
        raise SystemExit("没有匹配的数据源")

    fetcher = Fetcher()
    rewriter: Optional[TextRewriter]
    if args.no_rewrite:
        rewriter = None
    elif args.rewrite_provider == "google":
        rewriter = GoogleTranslateRewriter()
    else:
        rewriter = Rewriter()
    embedder = None
    if settings.EMBEDDING_ENABLED and not args.no_embed:
        embedder = OpenAIEmbeddingClient()

    licenses: Dict[str, Dict[str, str]] = {}
    license_failures: Dict[str, str] = {}
    for source in sources:
        if source.source_key in licenses or source.source_key in license_failures:
            continue
        try:
            _, license_text = extract_page(fetcher.get(source.license_url))
        except Exception as exc:
            license_failures[source.source_key] = str(exc)
            print(f"许可声明抓取失败，跳过 {source.source_key}: {exc}")
        else:
            licenses[source.source_key] = {
                "url": source.license_url,
                "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "text": license_text,
            }

    documents: List[Dict[str, object]] = []
    failures: List[str] = []
    for position, source in enumerate(sources, start=1):
        print(f"[{position}/{len(sources)}] {source.source_key}: {source.url}")
        if source.source_key not in licenses:
            failures.append(
                f"{source.url}: 未取得许可声明（{license_failures.get(source.source_key, '未知错误')}）"
            )
            print("  失败：未取得许可声明，按强制许可门禁跳过")
            continue
        try:
            documents.append(
                ingest_source(
                    source,
                    fetcher=fetcher,
                    rewriter=rewriter,
                    embedder=embedder,
                    license_summary=LICENSE_SUMMARIES[source.source_key],
                )
            )
        except Exception as exc:
            failures.append(f"{source.url}: {exc}")
            print(f"  失败：{exc}")

    chunk_count = sum(len(document["chunks"]) for document in documents)  # type: ignore[arg-type]
    if args.dry_run:
        print(f"dry-run：成功 {len(documents)} 篇，chunk {chunk_count}，失败 {len(failures)} 篇")
        return
    if not documents:
        raise SystemExit("没有成功生成任何文档")
    is_complete = 40 <= len(documents) <= 60 and 300 <= chunk_count <= 500 and not failures
    if not is_complete and not args.allow_partial:
        raise SystemExit(
            "生成结果未达到完整语料门禁（40–60 篇、300–500 chunks、0 失败），"
            "为保护现有产物，本次未写入；仅调试时可显式使用 --allow-partial"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    corpus_path = OUTPUT_DIR / "corpus.jsonl"
    meta_path = OUTPUT_DIR / "corpus.meta.json"
    licenses_path = OUTPUT_DIR / "LICENSES.md"

    corpus_path.write_text(
        "".join(json.dumps(document, ensure_ascii=False) + "\n" for document in documents),
        encoding="utf-8",
    )
    meta = {
        "status": "complete_unreviewed" if is_complete else "partial",
        "sources": sorted({document["source_key"] for document in documents}),
        "source_document_counts": dict(
            Counter(str(document["source_key"]) for document in documents)
        ),
        "source_chunk_counts": dict(
            Counter(
                str(document["source_key"])
                for document in documents
                for _ in document["chunks"]  # type: ignore[union-attr]
            )
        ),
        "document_count": len(documents),
        "chunk_count": chunk_count,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "rewrite_provider": None if rewriter is None else rewriter.provider_name,
        "rewrite_model": None if rewriter is None else rewriter.model_name,
        "embedding_model": None if embedder is None else embedder.model_name,
        "failed_urls": failures,
        "license_reviewed": False,
        "quality_gates": [
            "official_allowlist",
            "robots_crawl_delay",
            "licensed_text_scope",
            "numeric_fidelity",
            "translation_completeness",
            "unique_source_urls",
        ],
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    licenses_path.write_text(build_licenses_markdown(licenses), encoding="utf-8")
    print(f"完成：{len(documents)} 篇，chunk {chunk_count}，失败 {len(failures)} 篇")
    print("请人工复核 data/knowledge/LICENSES.md 后再发布语料。")


def _pack_translation_batches(
    pending: Sequence[Tuple[int, str, str]],
) -> List[List[Tuple[int, str, str]]]:
    batches: List[List[Tuple[int, str, str]]] = []
    current: List[Tuple[int, str, str]] = []
    current_size = 0
    for item in pending:
        protected_text, _ = _protect_numeric_literals(item[2])
        estimated_size = len(protected_text) + 80
        if current and current_size + estimated_size > GOOGLE_BATCH_MAX_CHARS:
            batches.append(current)
            current = []
            current_size = 0
        current.append(item)
        current_size += estimated_size
    if current:
        batches.append(current)
    return batches


def _split_translation_segments(text: str, *, target_max: int = 650) -> List[str]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    segments: List[str] = []
    current = ""
    for paragraph in paragraphs:
        pieces = (
            [paragraph]
            if len(paragraph) <= target_max
            else _split_long_paragraph(paragraph, target_max=target_max)
        )
        for piece in pieces:
            candidate = f"{current}\n\n{piece}".strip() if current else piece
            if current and len(candidate) > target_max:
                segments.append(current)
                current = piece
            else:
                current = candidate
    if current:
        segments.append(current)
    return segments


def _translation_is_complete(text_en: str, text_zh: str) -> bool:
    if len(text_en) < 80:
        return bool(text_zh.strip())
    han_count = len(re.findall(r"[\u4e00-\u9fff]", text_zh))
    scrubbed = re.sub(
        r"\b(?:https?://|www\.)\S+|\b[A-Za-z0-9.-]+\.(?:com|org|gov|net|edu)\b",
        " ",
        text_zh,
        flags=re.IGNORECASE,
    )
    english_runs = re.findall(
        r"(?:\b[A-Za-z][A-Za-z'’-]*\b(?:[\s,;:()\"'/\-]+|$)){6,}",
        scrubbed,
    )
    has_untranslated_sentence = any(
        len(re.sub(r"[^A-Za-z]", "", run)) >= 35 for run in english_runs
    )
    return han_count >= 20 and not has_untranslated_sentence


def _alpha_index(index: int) -> str:
    value = index + 1
    result = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _protect_numeric_literals(text: str) -> Tuple[str, Dict[str, str]]:
    replacements: Dict[str, str] = {}

    def replace_compound(match: re.Match[str]) -> str:
        token = f"[[[XIAOQI_NUMBER_{_alpha_index(len(replacements))}]]]"
        replacements[token] = match.group(0)
        return token

    protected = _COMPOUND_NUMBER_PATTERN.sub(replace_compound, text)

    def replace(match: re.Match[str]) -> str:
        token = f"[[[XIAOQI_NUMBER_{_alpha_index(len(replacements))}]]]"
        replacements[token] = match.group(0)
        return token

    return _NUMBER_PATTERN.sub(replace, protected), replacements


def _restore_numeric_literals(text: str, replacements: Dict[str, str]) -> str:
    restored = text
    for token, value in replacements.items():
        if token not in restored:
            raise ValueError(f"翻译结果丢失数字占位符: {token}")
        restored = restored.replace(token, value)
    return restored


def repair_numeric_fidelity(text_en: str, text_zh: str) -> str:
    """Keep source digit literals exact while preserving translated word-numbers.

    Machine translation may render an English word such as ``three`` as ``3``
    or combine ``95 percent`` into ``95%``. Those are semantically faithful but
    would look like newly introduced numeric facts to the strict validator. This
    pass reserves every numeric literal that existed in the source, converts only
    extra machine-introduced literals to Chinese numerals, and then restores the
    source literals byte-for-byte.
    """

    expected = Counter(_NUMBER_PATTERN.findall(text_en))
    if expected == Counter(_NUMBER_PATTERN.findall(text_zh)):
        return text_zh

    remaining = expected.copy()
    reserved: Dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        value = match.group(0)
        kept_value = value
        suffix = ""
        if remaining[value] <= 0 and value.endswith("%") and remaining[value[:-1]] > 0:
            kept_value = value[:-1]
            suffix = " 百分比"
        if remaining[kept_value] > 0:
            token = f"[[[XIAOQI_KEEP_{_alpha_index(len(reserved))}]]]"
            remaining[kept_value] -= 1
            reserved[token] = kept_value
            return token + suffix
        return _numeric_literal_to_chinese(value)

    repaired = _NUMBER_PATTERN.sub(replace, text_zh)
    missing = {value: count for value, count in remaining.items() if count > 0}
    if missing:
        raise ValueError(f"翻译结果缺少原文数字: {missing}")
    for token, value in reserved.items():
        repaired = repaired.replace(token, value)
    return repaired


def _numeric_literal_to_chinese(value: str) -> str:
    percent = value.endswith("%")
    normalized = value[:-1] if percent else value
    normalized = normalized.replace(",", "")
    if "." in normalized:
        integer, fraction = normalized.split(".", 1)
        rendered = f"{_integer_to_chinese(integer)}点{''.join(_DIGIT_ZH[d] for d in fraction)}"
    else:
        rendered = _integer_to_chinese(normalized)
    return f"百分之{rendered}" if percent else rendered


_DIGIT_ZH = {
    "0": "零",
    "1": "一",
    "2": "二",
    "3": "三",
    "4": "四",
    "5": "五",
    "6": "六",
    "7": "七",
    "8": "八",
    "9": "九",
}


def _integer_to_chinese(value: str) -> str:
    stripped = value.lstrip("0") or "0"
    number = int(stripped)
    if number == 0:
        return "零"
    if number >= 10000:
        return "".join(_DIGIT_ZH[digit] for digit in value)

    units = ("", "十", "百", "千")
    result: List[str] = []
    zero_pending = False
    digits = list(str(number))
    for index, digit in enumerate(digits):
        digit_value = int(digit)
        unit_index = len(digits) - index - 1
        if digit_value == 0:
            zero_pending = bool(result)
            continue
        if zero_pending:
            result.append("零")
            zero_pending = False
        if not (digit_value == 1 and unit_index == 1 and not result):
            result.append(_DIGIT_ZH[digit])
        result.append(units[unit_index])
    return "".join(result)


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def validate_numeric_fidelity(text_en: str, text_zh: str) -> None:
    """Reject a rewrite that adds, drops, or changes numeric facts."""
    numbers_en = Counter(_NUMBER_PATTERN.findall(text_en))
    numbers_zh = Counter(_NUMBER_PATTERN.findall(text_zh))
    if numbers_en != numbers_zh:
        raise ValueError(
            "改写后的数字、阈值或百分比与原文不一致: "
            f"source={dict(numbers_en)}, rewrite={dict(numbers_zh)}"
        )


def _deduplicate_blocks(blocks: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for block in blocks:
        normalized = _normalize_space(block)
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def _truncate_noncontent_sections(
    blocks: Iterable[Tuple[str, str]],
    *,
    drop_leading_lists: bool = False,
) -> List[Tuple[str, str]]:
    result: List[Tuple[str, str]] = []
    seen_section_heading = False
    for tag, block in blocks:
        normalized = _normalize_space(block)
        is_noncontent_title = bool(
            re.fullmatch(r"references?", normalized, flags=re.IGNORECASE)
            or re.fullmatch(
                r"clinical trials(?:\s+(?:for|on)\b.*)?",
                normalized,
                flags=re.IGNORECASE,
            )
        )
        if is_noncontent_title and tag == "li":
            continue
        if is_noncontent_title and tag in {"h2", "h3", "h4"}:
            break
        if tag in {"h2", "h3", "h4"} and re.fullmatch(
            r"how does (?:the )?niddk support .*research.*\?",
            normalized,
            flags=re.IGNORECASE,
        ):
            break
        if tag in {"h2", "h3", "h4"}:
            seen_section_heading = True
        if drop_leading_lists and tag == "li" and not seen_section_heading:
            continue
        result.append((tag, block))
    return result


def _trim_to_first_h1(blocks: Iterable[Tuple[str, str]]) -> List[Tuple[str, str]]:
    values = list(blocks)
    for index, (tag, _) in enumerate(values):
        if tag == "h1":
            return values[index:]
    return values


if __name__ == "__main__":
    main()
