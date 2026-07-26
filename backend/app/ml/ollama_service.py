"""Small HTTP adapter kept for the legacy ``/ollama`` debug endpoints.

The Agent MVP uses ``app.agent.llm_client`` and the configured OpenAI-compatible
proxy. Keeping this adapter HTTP-only prevents API startup from depending on the
Ollama Python package or any local model libraries.
"""

import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

import httpx


logger = logging.getLogger(__name__)


class OllamaService:
    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: str = "deepseek-r1:7b",
        timeout_seconds: float = 60.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system:
            payload["system"] = system
        return await self._post_json("/api/generate", payload)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        chat_messages = list(messages)
        if system:
            chat_messages.insert(0, {"role": "system", "content": system})
        payload = {
            "model": model or self.default_model,
            "messages": chat_messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        return await self._post_json("/api/chat", payload)

    async def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            yield json.loads(line)
        except Exception as exc:
            logger.warning("Legacy Ollama stream unavailable: %s", exc)
            yield {"response": "Ollama服务不可用", "done": True, "error": True}

    async def list_models(self) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                return response.json().get("models", [])
        except Exception as exc:
            logger.info("Legacy Ollama service unavailable: %s", exc)
            return []

    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        try:
            return await self._post_json("/api/show", {"name": model_name})
        except Exception as exc:
            return {"error": f"Ollama服务不可用: {exc}"}

    async def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}{path}", json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.info("Legacy Ollama request failed: %s", exc)
            return {
                "response": "Ollama服务不可用，请使用新的 Agent 接口",
                "model": payload.get("model", self.default_model),
                "error": True,
            }


ollama_service = OllamaService()
