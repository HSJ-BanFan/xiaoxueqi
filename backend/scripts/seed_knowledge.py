from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from sqlalchemy import Engine, inspect, text
from sqlalchemy.orm import Session


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.base_class import Base
from app.db.models import KnowledgeBase, KnowledgeChunk
from app.db.session import SessionLocal, engine
from app.services.knowledge_retrieval import clear_knowledge_index_cache


DEFAULT_CORPUS = REPO_ROOT / "data" / "knowledge" / "corpus.jsonl"

_KNOWLEDGE_BASE_COLUMNS = {
    "source_key": "VARCHAR(32)",
    "source_url": "VARCHAR(512)",
    "title_en": "VARCHAR(255)",
    "license": "VARCHAR(255)",
    "retrieved_at": "DATETIME",
    "content_hash": "VARCHAR(64)",
}


def ensure_knowledge_schema(bind: Engine) -> None:
    """Create new tables and add nullable document metadata columns idempotently."""
    inspector = inspect(bind)
    if not inspector.has_table(KnowledgeBase.__tablename__):
        Base.metadata.create_all(bind=bind)
        return

    existing = {column["name"] for column in inspector.get_columns(KnowledgeBase.__tablename__)}
    preparer = bind.dialect.identifier_preparer
    table_name = preparer.quote(KnowledgeBase.__tablename__)
    with bind.begin() as connection:
        for column_name, column_type in _KNOWLEDGE_BASE_COLUMNS.items():
            if column_name in existing:
                continue
            quoted_column = preparer.quote(column_name)
            connection.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN {quoted_column} {column_type} NULL")
            )

    # create_all now sees an upgraded knowledge_base table and creates
    # knowledge_chunks plus any other missing tables without changing data.
    Base.metadata.create_all(bind=bind)


def load_corpus(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as corpus_file:
        for line_number, raw_line in enumerate(corpus_file, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                item = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number} 不是有效 JSON") from exc
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_number} 必须是 JSON 对象")
            yield item


def seed_corpus(db: Session, documents: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "chunks": 0}
    try:
        for payload in documents:
            normalized = _normalize_document(payload)
            existing = _find_existing(db, normalized)
            chunks = normalized.pop("chunks")

            if existing is not None and existing.content_hash == normalized["content_hash"]:
                if len(existing.chunks) == len(chunks):
                    stats["skipped"] += 1
                    stats["chunks"] += len(existing.chunks)
                    continue

            if existing is None:
                document = KnowledgeBase(id=normalized.pop("id"), **normalized)
                db.add(document)
                db.flush()
                stats["inserted"] += 1
            else:
                document = existing
                normalized.pop("id", None)
                for key, value in normalized.items():
                    setattr(document, key, value)
                db.query(KnowledgeChunk).filter(
                    KnowledgeChunk.document_id == document.id
                ).delete(synchronize_session=False)
                db.flush()
                stats["updated"] += 1

            for chunk_payload in chunks:
                db.add(
                    KnowledgeChunk(
                        id=chunk_payload["id"],
                        document_id=document.id,
                        chunk_index=chunk_payload["chunk_index"],
                        text_zh=chunk_payload["text_zh"],
                        text_en=chunk_payload.get("text_en"),
                        char_count=chunk_payload["char_count"],
                        embedding=chunk_payload.get("embedding"),
                        embedding_model=chunk_payload.get("embedding_model"),
                    )
                )
            stats["chunks"] += len(chunks)

        db.commit()
    except Exception:
        db.rollback()
        raise

    clear_knowledge_index_cache()
    return stats


def _find_existing(db: Session, payload: Dict[str, Any]) -> Optional[KnowledgeBase]:
    source_url = payload.get("source_url")
    if source_url:
        existing = db.query(KnowledgeBase).filter(KnowledgeBase.source_url == source_url).first()
        if existing is not None:
            return existing
    return (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.content_hash == payload["content_hash"])
        .first()
    )


def _normalize_document(payload: Dict[str, Any]) -> Dict[str, Any]:
    chunks = payload.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("每个知识文档必须包含至少一个 chunk")

    source_url = _optional_string(payload.get("source_url"))
    document_id = _optional_string(payload.get("id")) or str(
        uuid.uuid5(uuid.NAMESPACE_URL, source_url or str(payload.get("title")))
    )
    normalized_chunks = []
    for position, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValueError("chunk 必须是 JSON 对象")
        text_zh = str(chunk.get("text_zh") or "").strip()
        if not text_zh:
            raise ValueError("chunk.text_zh 不能为空")
        chunk_index = int(chunk.get("chunk_index", position))
        chunk_id = _optional_string(chunk.get("id")) or str(
            uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:{chunk_index}")
        )
        embedding = chunk.get("embedding")
        if embedding is not None:
            if not isinstance(embedding, list):
                raise ValueError("chunk.embedding 必须是数组或 null")
            embedding = [float(value) for value in embedding]
        normalized_chunks.append(
            {
                "id": chunk_id,
                "chunk_index": chunk_index,
                "text_zh": text_zh,
                "text_en": _optional_string(chunk.get("text_en")),
                "char_count": int(chunk.get("char_count") or len(text_zh)),
                "embedding": embedding,
                "embedding_model": _optional_string(chunk.get("embedding_model")),
            }
        )

    normalized_chunks.sort(key=lambda item: item["chunk_index"])
    content = str(payload.get("content") or "\n\n".join(item["text_zh"] for item in normalized_chunks)).strip()
    content_hash = _optional_string(payload.get("content_hash")) or hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    tags = payload.get("tags") or []
    if not isinstance(tags, list):
        raise ValueError("tags 必须是数组")

    return {
        "id": document_id,
        "title": str(payload.get("title") or payload.get("title_en") or "未命名资料")[:255],
        "content": content,
        "source": _optional_string(payload.get("source")),
        "tags": [str(tag) for tag in tags],
        "source_key": _optional_string(payload.get("source_key")),
        "source_url": source_url,
        "title_en": _optional_string(payload.get("title_en")),
        "license": _optional_string(payload.get("license")),
        "retrieved_at": _parse_datetime(payload.get("retrieved_at")),
        "content_hash": content_hash,
        "chunks": normalized_chunks,
    }


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    normalized = str(value).strip().replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the versioned RAG corpus into the database")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    args = parser.parse_args()

    corpus_path = args.corpus.resolve()
    if not corpus_path.is_file():
        raise SystemExit(f"corpus 不存在: {corpus_path}")

    ensure_knowledge_schema(engine)
    with SessionLocal() as db:
        stats = seed_corpus(db, load_corpus(corpus_path))
    print(
        "知识库 seed 完成："
        f"新增 {stats['inserted']}，更新 {stats['updated']}，"
        f"跳过 {stats['skipped']}，chunk {stats['chunks']}"
    )


if __name__ == "__main__":
    main()
