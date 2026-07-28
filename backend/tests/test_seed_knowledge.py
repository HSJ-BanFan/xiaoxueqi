from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from app.db.models import KnowledgeBase, KnowledgeChunk
from scripts.seed_knowledge import ensure_knowledge_schema, load_corpus, seed_corpus


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "knowledge_sample.jsonl"


def test_legacy_knowledge_table_is_upgraded_idempotently():
    legacy_engine = create_engine("sqlite://")
    with legacy_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE knowledge_base (
                    id VARCHAR(36) PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    source VARCHAR(255),
                    tags JSON NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )

    ensure_knowledge_schema(legacy_engine)
    ensure_knowledge_schema(legacy_engine)

    inspector = inspect(legacy_engine)
    columns = {column["name"] for column in inspector.get_columns("knowledge_base")}
    assert {
        "source_key",
        "source_url",
        "title_en",
        "license",
        "retrieved_at",
        "content_hash",
    }.issubset(columns)
    assert inspector.has_table("knowledge_chunks")


def test_seed_corpus_is_idempotent(db: Session):
    first = seed_corpus(db, load_corpus(FIXTURE_PATH))
    second = seed_corpus(db, load_corpus(FIXTURE_PATH))

    assert first["inserted"] == 10
    assert first["chunks"] == 10
    assert second["skipped"] == 10
    assert db.query(KnowledgeBase).count() == 10
    assert db.query(KnowledgeChunk).count() == 10
