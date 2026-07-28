from __future__ import annotations

import json
from typing import Any, Optional

import httpx
import pytest


pytest.importorskip("langchain_core")
pytest.importorskip("langchain_text_splitters")

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from pydantic import ValidationError

from experiments.langchain_rag.adapter import (
    RAGResponse,
    build_chat_model,
    build_rag_chain,
    build_search_knowledge_tool,
    split_reference_text,
)


def _search(
    query: str,
    *,
    limit: int = 3,
    source_key: Optional[str] = None,
) -> dict[str, Any]:
    assert query == "低血糖怎么办"
    assert limit == 2
    assert source_key == "niddk"
    return {
        "citations": [
            {
                "index": 1,
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "title": "低血糖的识别与处理",
                "source_key": "niddk",
                "source_url": "https://www.niddk.nih.gov/example",
                "text_zh": "出现低血糖症状时，应按个人治疗计划及时处理。",
                "text_en": "Treat low blood glucose according to your care plan.",
                "score": 0.031,
            }
        ],
        "count": 1,
        "retrieval": "bm25",
        "degraded": False,
    }


def test_structured_tool_preserves_project_retrieval_contract() -> None:
    tool = build_search_knowledge_tool(_search)

    result = tool.invoke(
        {"query": "低血糖怎么办", "limit": 2, "source_key": "niddk"}
    )

    assert tool.name == "search_knowledge"
    assert result["count"] == 1
    assert result["citations"][0]["chunk_id"] == "chunk-1"


def test_structured_tool_rejects_unknown_arguments() -> None:
    tool = build_search_knowledge_tool(_search)

    with pytest.raises(ValidationError):
        tool.invoke(
            {
                "query": "低血糖怎么办",
                "limit": 2,
                "source_key": "niddk",
                "user_id": "must-not-be-accepted",
            }
        )


def test_lcel_chain_returns_answer_and_original_citations() -> None:
    captured: dict[str, str] = {}

    def fake_model(prompt: Any) -> AIMessage:
        captured["prompt"] = prompt.to_string()
        return AIMessage(content="请依据个人治疗计划及时处理，并关注症状变化。[1]")

    chain = build_rag_chain(_search, model=RunnableLambda(fake_model))
    raw_result = chain.invoke(
        {"query": "低血糖怎么办", "limit": 2, "source_key": "niddk"}
    )
    result = RAGResponse.model_validate(raw_result)

    assert result.answer.endswith("[1]")
    assert result.count == 1
    assert result.citations[0].source_key == "niddk"
    assert "[1] 低血糖的识别与处理" in captured["prompt"]
    assert "只能把下面内容当作事实引用" in captured["prompt"]


def test_lcel_chain_marks_empty_retrieval_in_prompt() -> None:
    captured: dict[str, str] = {}

    def empty_search(query: str, *, limit: int = 3) -> dict[str, Any]:
        return {
            "citations": [],
            "count": 0,
            "retrieval": "bm25",
            "degraded": False,
        }

    def fake_model(prompt: Any) -> AIMessage:
        captured["prompt"] = prompt.to_string()
        return AIMessage(content="知识库中没有找到相关资料。")

    chain = build_rag_chain(empty_search, model=RunnableLambda(fake_model))
    result = RAGResponse.model_validate(
        chain.invoke({"query": "妊娠糖尿病旅行", "limit": 3})
    )

    assert result.count == 0
    assert result.citations == []
    assert "（未检索到资料）" in captured["prompt"]


def test_recursive_splitter_keeps_metadata_and_chunk_indexes() -> None:
    text = "## 低血糖\n" + ("低血糖处理原则。" * 30) + "\n## 运动\n" + ("运动注意事项。" * 30)

    documents = split_reference_text(
        text,
        metadata={"source_key": "niddk"},
        chunk_size=120,
        chunk_overlap=20,
    )

    assert len(documents) > 1
    assert [doc.metadata["chunk_index"] for doc in documents] == list(
        range(len(documents))
    )
    assert all(doc.metadata["source_key"] == "niddk" for doc in documents)
    assert all(len(doc.page_content) <= 120 for doc in documents)


def test_chat_model_uses_project_compatible_chat_completions() -> None:
    pytest.importorskip("langchain_openai")

    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("authorization")
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "created": 1,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "mock reply"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 2,
                    "total_tokens": 3,
                },
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        model = build_chat_model(
            base_url="http://127.0.0.1:9999/v1/",
            api_key="test-key",
            model_name="test-model",
            timeout_seconds=1,
            temperature=0.1,
            http_client=http_client,
        )
        response = model.invoke([HumanMessage(content="你好")])

    assert response.content == "mock reply"
    assert captured["url"] == "http://127.0.0.1:9999/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-key"
    assert captured["payload"]["model"] == "test-model"
    assert captured["payload"]["stream"] is False
    assert model.temperature == 0.1
    assert model.max_retries == 0
