from app.agent.llm_client import OpenAICompatibleClient
from app.db.models import GlucoseRecord, Message
from app.models.assistant import MessageRoleEnum


def force_proxy_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("proxy unavailable")

    monkeypatch.setattr(OpenAICompatibleClient, "chat", fail)


def test_c1_authenticated_agent_chat_persists_audit(
    client,
    db,
    auth_header_a,
    monkeypatch,
):
    force_proxy_failure(monkeypatch)

    response = client.post(
        "/api/v1/agent/chat",
        headers=auth_header_a,
        json={"message": "最近血糖"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "fallback"
    assistant_message = (
        db.query(Message)
        .filter(
            Message.conversation_id == body["conversation_id"],
            Message.role == MessageRoleEnum.ASSISTANT,
        )
        .one()
    )
    assert assistant_message.message_metadata["mode"] == "fallback"
    assert assistant_message.message_metadata["tool_calls"][0]["name"] == "list_recent_glucose"


def test_c2_agent_chat_requires_jwt(client):
    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "最近血糖"},
    )

    assert response.status_code == 401


def test_c3_confirm_write_round_trip(client, db, auth_header_a, monkeypatch):
    force_proxy_failure(monkeypatch)
    request = {"message": "记录血糖 6.5 空腹", "confirm_write": False}

    preview = client.post("/api/v1/agent/chat", headers=auth_header_a, json=request)

    assert preview.status_code == 200
    assert preview.json()["tool_results"][0]["requires_confirm"] is True
    assert db.query(GlucoseRecord).count() == 0

    request.update(
        {
            "conversation_id": preview.json()["conversation_id"],
            "confirm_write": True,
        }
    )
    confirmed = client.post("/api/v1/agent/chat", headers=auth_header_a, json=request)

    db.expire_all()
    assert confirmed.status_code == 200
    assert confirmed.json()["tool_results"][0]["requires_confirm"] is False
    assert db.query(GlucoseRecord).count() == 1
