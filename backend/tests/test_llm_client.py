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
    assert message == {"role": "assistant", "content": "OK"}
