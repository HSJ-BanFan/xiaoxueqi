"""Optional LangChain adapters for evaluating the project's RAG seam."""

from experiments.langchain_rag.adapter import (
    Citation,
    EMPTY_RETRIEVAL_ANSWER,
    GroundingError,
    RAGRequest,
    RAGResponse,
    RetrievalPayload,
    build_chat_model,
    build_rag_chain,
    build_search_knowledge_tool,
    split_reference_text,
)

__all__ = [
    "Citation",
    "EMPTY_RETRIEVAL_ANSWER",
    "GroundingError",
    "RAGRequest",
    "RAGResponse",
    "RetrievalPayload",
    "build_chat_model",
    "build_rag_chain",
    "build_search_knowledge_tool",
    "split_reference_text",
]
