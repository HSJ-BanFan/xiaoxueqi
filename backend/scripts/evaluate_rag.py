from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Literal, Mapping, Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
DEFAULT_DATASET = BACKEND_DIR / "evals" / "rag_retrieval_eval.jsonl"
DEFAULT_CORPUS = REPO_ROOT / "data" / "knowledge" / "corpus.jsonl"
DEFAULT_JSON_REPORT = (
    REPO_ROOT / "docs" / "research" / "artifacts" / "rag-evaluation.json"
)
DEFAULT_MARKDOWN_REPORT = (
    REPO_ROOT / "docs" / "research" / "2026-07-28-rag-evaluation.md"
)
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.db.base_class import Base  # noqa: E402
from app.db.models import KnowledgeBase, KnowledgeChunk  # noqa: E402
from app.services.knowledge_retrieval import (  # noqa: E402
    KnowledgeRetriever,
    clear_knowledge_index_cache,
)
from scripts.seed_knowledge import load_corpus, seed_corpus  # noqa: E402


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    query: str = Field(min_length=2, max_length=200)
    gold_document_ids: list[str] = Field(min_length=1)
    gold_source_urls: list[str] = Field(min_length=1)
    topic: str = Field(min_length=1)
    split: Literal["dev", "test"]


class RetrievedCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    source_url: str | None = None
    title: str
    chunk_id: str | None = None


class EvaluationRetriever(Protocol):
    def search(self, query: str, *, limit: int) -> Sequence[RetrievedCitation]: ...


class CaseEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    query: str
    topic: str
    split: Literal["dev", "test"]
    gold_document_ids: list[str]
    gold_source_urls: list[str]
    retrieved_citations: list[RetrievedCitation]
    recall_at_k: float
    hit_at_k: float
    citation_precision_at_k: float


class SystemEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_count: int
    recall_at_k: float
    hit_at_k: float
    citation_precision_at_k: float
    failed_case_ids: list[str]
    cases: list[CaseEvaluation]


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    split: Literal["dev", "test", "all"]
    k: int
    case_count: int
    dataset_case_count: int
    split_counts: dict[str, int]
    corpus_document_count: int
    corpus_chunk_count: int
    dataset_sha256: str
    corpus_sha256: str
    baseline_commit: str
    systems: dict[str, SystemEvaluation]


class LegacySqlLikeRetriever:
    """Reproduce the pre-RAG knowledge endpoint from commit 9a37edc."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def search(self, query: str, *, limit: int) -> list[RetrievedCitation]:
        rows = (
            self.db.query(KnowledgeBase)
            .filter(
                KnowledgeBase.content.ilike(f"%{query}%")
                | KnowledgeBase.title.ilike(f"%{query}%")
            )
            .limit(limit)
            .all()
        )
        return [
            RetrievedCitation(
                document_id=row.id,
                source_url=row.source_url,
                title=row.title,
            )
            for row in rows
        ]


class BigramBm25RrfRetriever:
    """Expose the production retriever through the evaluation citation seam."""

    def __init__(self, db: Session) -> None:
        self.retriever = KnowledgeRetriever(db)

    def search(self, query: str, *, limit: int) -> list[RetrievedCitation]:
        result = self.retriever.search(query, limit=limit)
        return [
            RetrievedCitation(
                document_id=citation.document_id,
                source_url=citation.source_url,
                title=citation.title,
                chunk_id=citation.chunk_id,
            )
            for citation in result.citations
        ]


def _load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as source_file:
        for line_number, raw_line in enumerate(source_file, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number} 不是有效 JSON") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number} 必须是 JSON 对象")
            yield payload


def load_evaluation_cases(
    dataset_path: Path, corpus_path: Path
) -> list[EvaluationCase]:
    documents = {
        str(document["id"]): str(document.get("source_url") or "")
        for document in _load_jsonl(corpus_path)
    }
    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()

    for payload in _load_jsonl(dataset_path):
        case = EvaluationCase.model_validate(payload)
        if case.id in seen_ids:
            raise ValueError(f"评测题 ID 重复: {case.id}")
        seen_ids.add(case.id)

        unknown_ids = sorted(set(case.gold_document_ids) - documents.keys())
        if unknown_ids:
            raise ValueError(
                f"{case.id} 引用了不存在的 gold 文档: {', '.join(unknown_ids)}"
            )

        expected_urls = {
            documents[document_id] for document_id in case.gold_document_ids
        }
        if set(case.gold_source_urls) != expected_urls:
            raise ValueError(f"{case.id} 的 gold_source_urls 与语料文档不一致")
        cases.append(case)

    return cases


def evaluate_cases(
    cases: Sequence[EvaluationCase],
    retrievers: Mapping[str, EvaluationRetriever],
    *,
    k: int = 3,
) -> dict[str, SystemEvaluation]:
    if k < 1:
        raise ValueError("k 必须大于等于 1")
    if not cases:
        raise ValueError("评测集不能为空")

    evaluations: dict[str, SystemEvaluation] = {}
    for name, retriever in retrievers.items():
        case_results: list[CaseEvaluation] = []
        for case in cases:
            citations = list(retriever.search(case.query, limit=k))[:k]
            retrieved_document_ids = {citation.document_id for citation in citations}
            gold_document_ids = set(case.gold_document_ids)
            matched_documents = retrieved_document_ids & gold_document_ids
            recall = len(matched_documents) / len(gold_document_ids)
            matched_citations = sum(
                1
                for citation in citations
                if citation.document_id in gold_document_ids
                and citation.source_url in case.gold_source_urls
            )
            hit = float(matched_citations > 0)
            citation_precision = (
                matched_citations / len(citations) if citations else 0.0
            )
            case_results.append(
                CaseEvaluation(
                    id=case.id,
                    query=case.query,
                    topic=case.topic,
                    split=case.split,
                    gold_document_ids=case.gold_document_ids,
                    gold_source_urls=case.gold_source_urls,
                    retrieved_citations=citations,
                    recall_at_k=recall,
                    hit_at_k=hit,
                    citation_precision_at_k=citation_precision,
                )
            )

        count = len(case_results)
        evaluations[name] = SystemEvaluation(
            case_count=count,
            recall_at_k=sum(item.recall_at_k for item in case_results) / count,
            hit_at_k=sum(item.hit_at_k for item in case_results) / count,
            citation_precision_at_k=(
                sum(item.citation_precision_at_k for item in case_results) / count
            ),
            failed_case_ids=[
                item.id for item in case_results if item.recall_at_k < 1.0
            ],
            cases=case_results,
        )
    return evaluations


def run_offline_evaluation(
    *,
    dataset_path: Path,
    corpus_path: Path,
    split: Literal["dev", "test", "all"] = "all",
    k: int = 3,
) -> EvaluationReport:
    cases = load_evaluation_cases(dataset_path, corpus_path)
    selected_cases = (
        cases if split == "all" else [case for case in cases if case.split == split]
    )
    if not selected_cases:
        raise ValueError(f"split={split} 没有评测题")
    split_counts: dict[str, int] = {}
    for case in cases:
        split_counts[case.split] = split_counts.get(case.split, 0) + 1

    evaluation_engine = create_engine("sqlite://")
    EvaluationSession = sessionmaker(bind=evaluation_engine)
    Base.metadata.create_all(bind=evaluation_engine)
    clear_knowledge_index_cache()

    try:
        with EvaluationSession() as db:
            seed_corpus(db, load_corpus(corpus_path))
            document_count = db.query(KnowledgeBase).count()
            chunk_count = db.query(KnowledgeChunk).count()

            embedding_enabled = settings.EMBEDDING_ENABLED
            settings.EMBEDDING_ENABLED = False
            try:
                current_retriever = BigramBm25RrfRetriever(db)
            finally:
                settings.EMBEDDING_ENABLED = embedding_enabled

            systems = evaluate_cases(
                selected_cases,
                {
                    "legacy_sql_like": LegacySqlLikeRetriever(db),
                    "bigram_bm25_rrf": current_retriever,
                },
                k=k,
            )
            return EvaluationReport(
                split=split,
                k=k,
                case_count=len(selected_cases),
                dataset_case_count=len(cases),
                split_counts=split_counts,
                corpus_document_count=document_count,
                corpus_chunk_count=chunk_count,
                dataset_sha256=_sha256_file(dataset_path),
                corpus_sha256=_sha256_file(corpus_path),
                baseline_commit="9a37edc",
                systems=systems,
            )
    finally:
        clear_knowledge_index_cache()
        evaluation_engine.dispose()


def render_markdown_report(report: EvaluationReport) -> str:
    lines = [
        "# RAG 离线检索效果评测",
        "",
        f"- 评测集：共 {report.dataset_case_count} 题（"
        + " / ".join(f"{name} {count}" for name, count in report.split_counts.items())
        + "）",
        f"- 本次评测范围：`{report.split}` split，共 {report.case_count} 题",
        f"- 语料规模：{report.corpus_document_count} documents / {report.corpus_chunk_count} chunks",
        f"- 截断位置：top-{report.k}",
        "- 运行约束：内存 SQLite、禁用 embedding、无网络、无真实 LLM",
        f"- 评测集 SHA-256：`{report.dataset_sha256}`",
        f"- 语料 SHA-256：`{report.corpus_sha256}`",
        f"- 旧基线提交：`{report.baseline_commit}`",
        "",
        "## 评测协议",
        "",
        "问题由维护者根据健康助理的非个人知识意图人工策划，每题显式绑定语料文档 UUID 与官方 URL。",
        "dev split 仅用于分析和通用检索调优；test split 在实现与输入哈希冻结后首次运行，"
        "不根据 test 失败清单继续调参。",
        "",
        "## 指标定义",
        "",
        f"- Macro Recall@{report.k}：逐题计算 gold 文档被 top-{report.k} 覆盖的比例，再做宏平均。",
        f"- Citation Hit@{report.k}：至少一个文档 ID 与来源 URL 均属于 gold 的引用进入 top-{report.k} 的问题占比。",
        f"- Citation Precision@{report.k}：逐题计算返回引用中，文档 ID 与来源 URL 同时属于 gold 的比例，再做宏平均。",
        "",
        "## 结果",
        "",
        f"| 系统 | 题数 | Macro Recall@{report.k} | Citation Hit@{report.k} | Citation Precision@{report.k} | 未完整召回题数 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, system in report.systems.items():
        lines.append(
            f"| `{name}` | {system.case_count} | {_percent(system.recall_at_k)} | "
            f"{_percent(system.hit_at_k)} | {_percent(system.citation_precision_at_k)} | "
            f"{len(system.failed_case_ids)} |"
        )

    lines.extend(["", "## 逐题失败清单", ""])
    for name, system in report.systems.items():
        lines.extend([f"### `{name}`", ""])
        failures = [item for item in system.cases if item.recall_at_k < 1.0]
        if not failures:
            lines.extend(["无。", ""])
            continue
        for item in failures:
            retrieved = (
                ", ".join(
                    f"{citation.title} ({citation.document_id})"
                    for citation in item.retrieved_citations
                )
                or "无结果"
            )
            lines.extend(
                [
                    f"- `{item.id}`：{item.query}",
                    f"  - gold：{', '.join(item.gold_document_ids)}",
                    f"  - top-{report.k}：{retrieved}",
                    f"  - Recall@{report.k}：{_percent(item.recall_at_k)}",
                ]
            )
        lines.append("")

    lines.extend(
        [
            "## 口径说明",
            "",
            "`legacy_sql_like` 复现 RAG 改造前的整句 SQL `ILIKE '%query%'` 搜索；"
            "`bigram_bm25_rrf` 使用当前生产检索器。当前提交语料的 embedding 字段为空，"
            "因此本报告只证明 SQL LIKE → 中文 bigram BM25/RRF 的变化，不声称向量召回带来的提升。",
            "",
        ]
    )
    return "\n".join(lines)


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="离线比较旧 SQL 搜索与当前 RAG 检索器")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--split", choices=("dev", "test", "all"), default="all")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--output-markdown", type=Path, default=DEFAULT_MARKDOWN_REPORT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_offline_evaluation(
        dataset_path=args.dataset,
        corpus_path=args.corpus,
        split=args.split,
        k=args.k,
    )
    _write_text(args.output_json, report.model_dump_json(indent=2) + "\n")
    _write_text(args.output_markdown, render_markdown_report(report))

    baseline = report.systems["legacy_sql_like"]
    current = report.systems["bigram_bm25_rrf"]
    print(
        f"Recall@{report.k}: {_percent(baseline.recall_at_k)} -> "
        f"{_percent(current.recall_at_k)}; "
        f"Citation Hit@{report.k}: {_percent(current.hit_at_k)}; "
        f"Citation Precision@{report.k}: {_percent(current.citation_precision_at_k)}"
    )
    print(f"JSON: {args.output_json}")
    print(f"Markdown: {args.output_markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
