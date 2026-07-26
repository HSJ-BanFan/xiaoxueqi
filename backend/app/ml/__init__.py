"""Legacy ML integrations.

The application startup path must not import heavyweight local-model packages.
Callers that still need the legacy service can import it explicitly.
"""

from typing import Any

__all__ = ["LLMService"]


def __getattr__(name: str) -> Any:
    if name == "LLMService":
        from app.ml.llm_service import LLMService

        return LLMService
    raise AttributeError(name)
