from datetime import datetime

from app.db.models import KnowledgeBase, KnowledgeChunk


def add_api_document(db, *, document_id: str, title: str, text: str, source_key: str):
    db.add(
        KnowledgeBase(
            id=document_id,
            title=title,
            content=text,
            source=source_key,
            tags=["test"],
            source_key=source_key,
            source_url=f"https://example.test/{document_id}",
            license="public domain test fixture",
            retrieved_at=datetime(2026, 7, 28),
            content_hash=(document_id * 64)[:64],
            chunks=[
                KnowledgeChunk(
                    id=f"chunk-{document_id}",
                    chunk_index=0,
                    text_zh=text,
                    text_en=f"English source for {title}",
                    char_count=len(text),
                )
            ],
        )
    )
    db.commit()


def test_knowledge_search_requires_authentication(client):
    response = client.get("/api/v1/knowledge/search", params={"q": "低血糖"})

    assert response.status_code == 401


def test_knowledge_search_validates_query_and_limit(client, auth_header_a):
    too_short = client.get(
        "/api/v1/knowledge/search",
        headers=auth_header_a,
        params={"q": "低"},
    )
    too_many = client.get(
        "/api/v1/knowledge/search",
        headers=auth_header_a,
        params={"q": "低血糖", "limit": 6},
    )

    assert too_short.status_code == 422
    assert too_many.status_code == 422


def test_knowledge_search_returns_ranked_citations_with_real_scores(
    client,
    db,
    auth_header_a,
):
    add_api_document(
        db,
        document_id="strong",
        title="低血糖处理",
        text="低血糖低血糖出现时需要及时识别低血糖症状。",
        source_key="niddk",
    )
    add_api_document(
        db,
        document_id="weak",
        title="血糖监测",
        text="血糖监测有助于识别低血糖。",
        source_key="cdc",
    )

    response = client.get(
        "/api/v1/knowledge/search",
        headers=auth_header_a,
        params={"q": "低血糖", "limit": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert body["citations"][0]["document_id"] == "strong"
    assert body["citations"][0]["score"] != body["citations"][1]["score"]
    assert body["citations"][0]["source_url"].startswith("https://")


def test_knowledge_search_can_filter_by_source(client, db, auth_header_a):
    add_api_document(
        db,
        document_id="niddk",
        title="低血糖",
        text="低血糖资料。",
        source_key="niddk",
    )
    add_api_document(
        db,
        document_id="cdc",
        title="低血糖",
        text="低血糖资料。",
        source_key="cdc",
    )

    response = client.get(
        "/api/v1/knowledge/search",
        headers=auth_header_a,
        params={"q": "低血糖", "source": "cdc"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["citations"][0]["source_key"] == "cdc"
