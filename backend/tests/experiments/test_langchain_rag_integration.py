from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest


pytest.importorskip("langchain_core")
knowledge_retrieval = pytest.importorskip(
    "app.services.knowledge_retrieval",
    reason="the real RAG seam is supplied by feat/rag-knowledge",
)

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app.db.models import KnowledgeBase, KnowledgeChunk
from experiments.langchain_rag.adapter import RAGResponse, build_rag_chain


KnowledgeRetriever = knowledge_retrieval.KnowledgeRetriever
clear_knowledge_index_cache = knowledge_retrieval.clear_knowledge_index_cache


@pytest.fixture(autouse=True)
def clear_index_cache():
    clear_knowledge_index_cache()
    yield
    clear_knowledge_index_cache()


def _add_document(
    db,
    *,
    document_id: str,
    title: str,
    text_zh: str,
    embedding: list[float] | None = None,
) -> None:
    db.add(
        KnowledgeBase(
            id=document_id,
            title=title,
            content=text_zh,
            source="Test Source",
            tags=["test"],
            source_key="niddk",
            source_url=f"https://example.test/{document_id}",
            title_en=title,
            license="public domain test fixture",
            retrieved_at=datetime(2026, 7, 28),
            content_hash=(document_id * 64)[:64],
            chunks=[
                KnowledgeChunk(
                    id=f"chunk-{document_id}",
                    chunk_index=0,
                    text_zh=text_zh,
                    text_en=f"English source for {title}",
                    char_count=len(text_zh),
                    embedding=embedding,
                    embedding_model="test-embedding" if embedding else None,
                )
            ],
        )
    )
    db.commit()


class _FakeEmbedder:
    model_name = "test-embedding"

    def embed(self, text: str) -> list[float]:
        return [1.0, 0.0]


class _FailingEmbedder:
    model_name = "test-embedding"

    def embed(self, text: str) -> list[float]:
        raise RuntimeError("embedding endpoint unavailable")


def _citing_model(prompt: Any) -> AIMessage:
    return AIMessage(content="请依据检索资料及时处理，并关注症状变化。[1]")


def test_real_retriever_preserves_rrf_citations_through_lcel(db) -> None:
    _add_document(
        db,
        document_id="bm25-doc",
        title="低血糖",
        text_zh="低血糖的关键词资料。",
        embedding=[0.0, 1.0],
    )
    _add_document(
        db,
        document_id="vector-doc",
        title="应急处理",
        text_zh="出现症状时的处理原则。",
        embedding=[1.0, 0.0],
    )
    retriever = KnowledgeRetriever(db, embedder=_FakeEmbedder())
    chain = build_rag_chain(retriever.search, model=RunnableLambda(_citing_model))

    result = RAGResponse.model_validate(
        chain.invoke({"query": "低血糖怎么办", "limit": 2})
    )

    assert result.retrieval == "bm25+vector"
    assert result.degraded is False
    assert result.count == 2
    assert {citation.document_id for citation in result.citations} == {
        "bm25-doc",
        "vector-doc",
    }
    assert all(citation.source_url for citation in result.citations)


def test_real_retriever_preserves_vector_degradation_through_lcel(db) -> None:
    _add_document(
        db,
        document_id="hypo",
        title="低血糖的识别与处理",
        text_zh="低血糖可能出现发抖和出汗，应按既定计划及时处理。",
        embedding=[1.0, 0.0],
    )
    retriever = KnowledgeRetriever(db, embedder=_FailingEmbedder())
    chain = build_rag_chain(retriever.search, model=RunnableLambda(_citing_model))

    result = RAGResponse.model_validate(
        chain.invoke({"query": "低血糖怎么办", "limit": 2})
    )

    assert result.retrieval == "bm25"
    assert result.degraded is True
    assert result.count == 1
    assert result.citations[0].document_id == "hypo"
