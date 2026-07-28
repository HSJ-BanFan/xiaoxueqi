import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.evaluate_rag import (
    EvaluationCase,
    RetrievedCitation,
    evaluate_cases,
    load_evaluation_cases,
    main,
    run_offline_evaluation,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_DATASET = REPO_ROOT / "backend" / "evals" / "rag_retrieval_eval.jsonl"
FULL_CORPUS = REPO_ROOT / "data" / "knowledge" / "corpus.jsonl"


def _write_jsonl(path, rows):
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_load_evaluation_cases_validates_gold_against_corpus(tmp_path):
    corpus_path = tmp_path / "corpus.jsonl"
    dataset_path = tmp_path / "rag_eval.jsonl"
    _write_jsonl(
        corpus_path,
        [
            {
                "id": "doc-hypoglycemia",
                "source_url": "https://example.test/hypoglycemia",
            }
        ],
    )
    _write_jsonl(
        dataset_path,
        [
            {
                "id": "hypoglycemia-treatment-01",
                "query": "低血糖时应该怎么办",
                "gold_document_ids": ["doc-hypoglycemia"],
                "gold_source_urls": ["https://example.test/hypoglycemia"],
                "topic": "hypoglycemia",
                "split": "dev",
            }
        ],
    )

    cases = load_evaluation_cases(dataset_path, corpus_path)

    assert len(cases) == 1
    assert cases[0].id == "hypoglycemia-treatment-01"
    assert cases[0].gold_document_ids == ["doc-hypoglycemia"]


class FakeRetriever:
    def __init__(self, citations):
        self.citations = citations

    def search(self, query, *, limit):
        return self.citations[:limit]


def test_evaluate_cases_reports_distinct_recall_hit_and_citation_precision():
    case = EvaluationCase(
        id="case-1",
        query="低血糖怎么处理",
        gold_document_ids=["doc-a", "doc-b"],
        gold_source_urls=["https://example.test/a", "https://example.test/b"],
        topic="hypoglycemia",
        split="dev",
    )
    retriever = FakeRetriever(
        [
            RetrievedCitation(
                document_id="doc-a",
                source_url="https://example.test/a",
                title="A",
                chunk_id="chunk-a-1",
            ),
            RetrievedCitation(
                document_id="doc-x",
                source_url="https://example.test/x",
                title="X",
                chunk_id="chunk-x-1",
            ),
            RetrievedCitation(
                document_id="doc-a",
                source_url="https://example.test/a",
                title="A",
                chunk_id="chunk-a-2",
            ),
        ]
    )

    result = evaluate_cases([case], {"candidate": retriever}, k=3)["candidate"]

    assert result.case_count == 1
    assert result.recall_at_k == pytest.approx(0.5)
    assert result.hit_at_k == pytest.approx(1.0)
    assert result.citation_precision_at_k == pytest.approx(2 / 3)
    assert result.failed_case_ids == ["case-1"]


def test_citation_hit_requires_both_gold_document_id_and_source_url():
    case = EvaluationCase(
        id="case-url-mismatch",
        query="什么是低血糖",
        gold_document_ids=["doc-a"],
        gold_source_urls=["https://example.test/a"],
        topic="hypoglycemia",
        split="dev",
    )
    retriever = FakeRetriever(
        [
            RetrievedCitation(
                document_id="doc-a",
                source_url="https://example.test/wrong",
                title="A",
                chunk_id="chunk-a",
            )
        ]
    )

    result = evaluate_cases([case], {"candidate": retriever}, k=3)["candidate"]

    assert result.recall_at_k == 1.0
    assert result.hit_at_k == 0.0
    assert result.citation_precision_at_k == 0.0


def test_committed_evaluation_dataset_is_balanced_and_auditable():
    cases = load_evaluation_cases(EVAL_DATASET, FULL_CORPUS)

    assert len(cases) == 50
    assert Counter(case.split for case in cases) == {"dev": 25, "test": 25}
    assert len({case.id for case in cases}) == 50
    assert len({case.query for case in cases}) == 50
    assert len({case.topic for case in cases}) >= 20


def test_offline_runner_compares_legacy_sql_with_current_retriever(tmp_path):
    dataset_path = tmp_path / "rag_eval.jsonl"
    _write_jsonl(
        dataset_path,
        [
            {
                "id": "hypoglycemia-treatment-01",
                "query": "低血糖怎么处理",
                "gold_document_ids": ["sample-hypoglycemia"],
                "gold_source_urls": [
                    "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/low-blood-glucose-hypoglycemia"
                ],
                "topic": "hypoglycemia",
                "split": "test",
            }
        ],
    )
    fixture_corpus = Path(__file__).parent / "fixtures" / "knowledge_sample.jsonl"

    report = run_offline_evaluation(
        dataset_path=dataset_path,
        corpus_path=fixture_corpus,
        split="test",
        k=3,
    )

    assert report.case_count == 1
    assert report.corpus_document_count == 10
    assert report.corpus_chunk_count == 10
    assert report.systems["legacy_sql_like"].recall_at_k == 0.0
    assert report.systems["bigram_bm25_rrf"].recall_at_k == 1.0
    assert report.systems["bigram_bm25_rrf"].citation_precision_at_k > 0.0


def test_cli_writes_machine_readable_and_reviewable_reports(tmp_path):
    dataset_path = tmp_path / "rag_eval.jsonl"
    json_report = tmp_path / "report.json"
    markdown_report = tmp_path / "report.md"
    _write_jsonl(
        dataset_path,
        [
            {
                "id": "hypoglycemia-symptoms-01",
                "query": "低血糖有哪些症状",
                "gold_document_ids": ["sample-hypoglycemia"],
                "gold_source_urls": [
                    "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/low-blood-glucose-hypoglycemia"
                ],
                "topic": "hypoglycemia",
                "split": "test",
            }
        ],
    )
    fixture_corpus = Path(__file__).parent / "fixtures" / "knowledge_sample.jsonl"

    exit_code = main(
        [
            "--dataset",
            str(dataset_path),
            "--corpus",
            str(fixture_corpus),
            "--split",
            "test",
            "--output-json",
            str(json_report),
            "--output-markdown",
            str(markdown_report),
        ]
    )

    payload = json.loads(json_report.read_text(encoding="utf-8"))
    markdown = markdown_report.read_text(encoding="utf-8")
    assert exit_code == 0
    assert payload["case_count"] == 1
    assert payload["dataset_case_count"] == 1
    assert payload["split_counts"] == {"test": 1}
    assert len(payload["dataset_sha256"]) == 64
    assert len(payload["corpus_sha256"]) == 64
    assert payload["baseline_commit"] == "9a37edc"
    assert "Macro Recall@3" in markdown
    assert "Citation Precision@3" in markdown
    assert "legacy_sql_like" in markdown
    assert "bigram_bm25_rrf" in markdown
