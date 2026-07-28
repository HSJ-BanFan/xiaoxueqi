from datetime import datetime

import pytest

from app.db.models import KnowledgeBase, KnowledgeChunk
from app.services.knowledge_retrieval import (
    KnowledgeRetriever,
    clear_knowledge_index_cache,
    expand_query,
    reciprocal_rank_fusion,
    tokenize,
)


@pytest.fixture(autouse=True)
def clear_index_cache():
    clear_knowledge_index_cache()
    yield
    clear_knowledge_index_cache()


def add_document(
    db,
    *,
    document_id: str,
    title: str,
    text_zh: str,
    source_key: str = "niddk",
    embedding=None,
):
    document = KnowledgeBase(
        id=document_id,
        title=title,
        content=text_zh,
        source="Test Source",
        tags=["test"],
        source_key=source_key,
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
    db.add(document)
    db.commit()
    return document


def test_chinese_bigram_and_ascii_tokenization():
    assert tokenize("低血糖怎么办 A1C test-model") == [
        "低血",
        "血糖",
        "糖怎",
        "怎么",
        "么办",
        "a1c",
        "test-model",
    ]


def test_query_expansion_adds_common_self_management_synonyms():
    assert expand_query("运动前后如何管理 A1C 和碳水") == (
        "运动前后如何管理 A1C 和碳水 身体活动 体力活动 健康生活 糖化血红蛋白 碳水化合物"
    )


def test_query_expansion_normalizes_common_natural_question_phrases():
    expanded = expand_query(
        "生完孩子后复查时，怎样确诊高血糖，1 型糖尿病和 2 型糖尿病有何区别"
    )

    assert "宝宝出生后" in expanded
    assert "产后" in expanded
    assert "检查" in expanded
    assert "测试" in expanded
    assert "诊断" in expanded
    assert "血糖过高" in expanded
    assert "类型 1 糖尿病" in expanded
    assert "类型 2 糖尿病" in expanded


def test_bm25_scores_and_ranks_relevant_chunk_first(db):
    add_document(
        db,
        document_id="hypo",
        title="低血糖的识别与处理",
        text_zh="低血糖可能出现发抖、出汗和头晕。应按既定计划及时处理低血糖。",
    )
    add_document(
        db,
        document_id="foot",
        title="足部护理",
        text_zh="每天检查足部皮肤，并保持足部清洁干燥。",
    )

    result = KnowledgeRetriever(db).search("低血糖怎么办", limit=2)

    assert result.retrieval == "bm25"
    assert result.degraded is False
    assert result.count == 1
    assert result.citations[0].document_id == "hypo"
    assert result.citations[0].index == 1
    assert result.citations[0].score > 0


def test_search_prioritizes_distinct_sources_before_repeated_chunks(db):
    first_source = KnowledgeBase(
        id="hypo-a",
        title="低血糖处理",
        content="低血糖时需要及时处理。严重时需要他人帮助。",
        source="Test Source A",
        tags=["test"],
        source_key="niddk",
        source_url="https://example.test/hypo-a",
        title_en="Hypoglycemia A",
        license="public domain test fixture",
        retrieved_at=datetime(2026, 7, 28),
        content_hash="a" * 64,
        chunks=[
            KnowledgeChunk(
                id="chunk-hypo-a-1",
                chunk_index=0,
                text_zh="低血糖时需要及时处理。",
                text_en="Treat low blood glucose promptly.",
                char_count=12,
            ),
            KnowledgeChunk(
                id="chunk-hypo-a-2",
                chunk_index=1,
                text_zh="严重低血糖时需要他人帮助。",
                text_en="Severe hypoglycemia requires help.",
                char_count=14,
            ),
        ],
    )
    second_source = KnowledgeBase(
        id="hypo-b",
        title="低血糖急救",
        content="低血糖急救资料。",
        source="Test Source B",
        tags=["test"],
        source_key="medlineplus",
        source_url="https://example.test/hypo-b",
        title_en="Hypoglycemia B",
        license="public domain test fixture",
        retrieved_at=datetime(2026, 7, 28),
        content_hash="b" * 64,
        chunks=[
            KnowledgeChunk(
                id="chunk-hypo-b-1",
                chunk_index=0,
                text_zh="低血糖急救时应补充快速起效的碳水化合物。",
                text_en="Use fast-acting carbohydrate for hypoglycemia.",
                char_count=20,
            )
        ],
    )
    general_source = KnowledgeBase(
        id="general",
        title="糖尿病日常管理",
        content="出现问题时应该马上按管理计划处理。",
        source="Test Source C",
        tags=["test"],
        source_key="niddk",
        source_url="https://example.test/general",
        title_en="General management",
        license="public domain test fixture",
        retrieved_at=datetime(2026, 7, 28),
        content_hash="c" * 64,
        chunks=[
            KnowledgeChunk(
                id="chunk-general-1",
                chunk_index=0,
                text_zh="出现问题时应该马上按管理计划处理。",
                text_en="Follow the management plan promptly.",
                char_count=17,
            )
        ],
    )
    db.add_all([first_source, second_source, general_source])
    db.commit()

    result = KnowledgeRetriever(db).search("低血糖时应该马上怎么处理", limit=3)
    document_ids = [citation.document_id for citation in result.citations]

    assert len(document_ids) == 3
    assert len(set(document_ids)) == 3


def test_title_coverage_keeps_the_named_health_topic_ahead_of_generic_wording(db):
    add_document(
        db,
        document_id="hyperglycemia",
        title="高血糖",
        text_zh="高血糖常见表现包括口渴、疲倦、尿频和视力模糊。",
    )
    add_document(
        db,
        document_id="generic-danger",
        title="糖尿病危险情况",
        text_zh="高血糖会有什么表现，严重时有什么危险，应该怎样处理这些问题。",
    )

    result = KnowledgeRetriever(db).search(
        "高血糖会有什么表现，严重时有什么危险？",
        limit=2,
    )

    assert result.citations[0].document_id == "hyperglycemia"


def test_rrf_fusion_rewards_items_present_in_both_rankings():
    scores = reciprocal_rank_fusion(
        [["bm25-first", "shared"], ["shared", "vector-second"]]
    )

    assert scores["shared"] > scores["bm25-first"]
    assert scores["shared"] > scores["vector-second"]


def test_empty_corpus_returns_successful_empty_result(db):
    result = KnowledgeRetriever(db).search("低血糖")

    assert result.count == 0
    assert result.citations == []
    assert result.retrieval == "bm25"
    assert result.degraded is False


def test_source_key_filter_limits_candidates(db):
    add_document(
        db,
        document_id="niddk-doc",
        title="NIDDK 低血糖",
        text_zh="低血糖处理资料。",
        source_key="niddk",
    )
    add_document(
        db,
        document_id="cdc-doc",
        title="CDC 低血糖",
        text_zh="低血糖预防资料。",
        source_key="cdc",
    )

    result = KnowledgeRetriever(db).search("低血糖", source_key="cdc")

    assert result.count == 1
    assert result.citations[0].source_key == "cdc"


class FakeEmbedder:
    model_name = "test-embedding"

    def embed(self, text: str):
        return [1.0, 0.0]


class FailingEmbedder:
    model_name = "test-embedding"

    def embed(self, text: str):
        raise RuntimeError("embedding endpoint unavailable")


def test_vector_results_are_fused_with_bm25(db):
    add_document(
        db,
        document_id="bm25-doc",
        title="低血糖",
        text_zh="低血糖的关键词资料。",
        embedding=[0.0, 1.0],
    )
    add_document(
        db,
        document_id="vector-doc",
        title="应急处理",
        text_zh="出现症状时的处理原则。",
        embedding=[1.0, 0.0],
    )

    result = KnowledgeRetriever(db, embedder=FakeEmbedder()).search("低血糖", limit=2)

    assert result.retrieval == "bm25+vector"
    assert result.degraded is False
    assert {citation.document_id for citation in result.citations} == {
        "bm25-doc",
        "vector-doc",
    }


def test_embedder_failure_degrades_to_bm25(db):
    add_document(
        db,
        document_id="hypo",
        title="低血糖",
        text_zh="低血糖处理资料。",
        embedding=[1.0, 0.0],
    )

    result = KnowledgeRetriever(db, embedder=FailingEmbedder()).search("低血糖")

    assert result.retrieval == "bm25"
    assert result.degraded is True
    assert result.citations[0].document_id == "hypo"
