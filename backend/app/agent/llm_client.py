from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class LLMClientError(RuntimeError):
    """An LLM transport or response-shape failure."""


class OpenAICompatibleClient:
    """Minimal synchronous client for OpenAI-compatible chat completions."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        temperature: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.api_key = settings.LLM_API_KEY if api_key is None else api_key
        self.model = model or settings.LLM_MODEL
        self.timeout_seconds = timeout_seconds or settings.LLM_TIMEOUT_SECONDS
        self.temperature = settings.LLM_TEMPERATURE if temperature is None else temperature
        self.transport = transport

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        *,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": self.temperature,
            "tool_choice": "auto",
            # Some OpenAI-compatible proxies default Gemini-family models to
            # SSE even when the caller did not request streaming. The Agent
            # runtime consumes one complete response per tool round.
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            # Never include the Authorization header or full key in logs/errors.
            logger.warning("LLM request failed at %s: %s", self.endpoint, exc.__class__.__name__)
            raise LLMClientError("模型服务暂不可用") from exc

        try:
            message = body["choices"][0]["message"]
            if not isinstance(message, dict):
                raise TypeError("message is not an object")
            return message
        except (KeyError, IndexError, TypeError) as exc:
            logger.warning("LLM response has an unexpected shape")
            raise LLMClientError("模型响应格式无效") from exc
