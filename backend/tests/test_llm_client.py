import json

import httpx

from app.agent.llm_client import OpenAICompatibleClient


def test_client_explicitly_disables_streaming():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": "OK"}}
                ]
            },
        )

    client = OpenAICompatibleClient(
        base_url="http://proxy.test/v1",
        api_key="test-key",
        model="gemini/gemini-3.6-flash",
        transport=httpx.MockTransport(handler),
    )

    message = client.chat([{"role": "user", "content": "hello"}])

    assert captured["payload"]["model"] == "gemini/gemini-3.6-flash"
    assert captured["payload"]["stream"] is False
    assert "tool_choice" not in captured["payload"]
    assert message == {"role": "assistant", "content": "OK"}


def test_client_enables_auto_tool_choice_when_tools_are_present():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "OK"}}]},
        )

    client = OpenAICompatibleClient(
        base_url="http://proxy.test/v1",
        api_key="test-key",
        model="test-model",
        transport=httpx.MockTransport(handler),
    )
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_knowledge",
                "description": "test",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]

    client.chat([{"role": "user", "content": "hello"}], tools)

    assert captured["payload"]["tools"] == tools
    assert captured["payload"]["tool_choice"] == "auto"
