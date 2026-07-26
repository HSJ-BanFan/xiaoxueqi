from app.agent.runtime import HealthAgent
from app.agent.tools import HealthToolRegistry
from app.db.models import GlucoseRecord
from app.models.glucose import (
    GlucoseCreate,
    MeasurementMethodEnum,
    MeasurementTimeEnum,
)
from app.services.glucose import create_glucose_record


class FailingClient:
    def chat(self, *args, **kwargs):
        raise RuntimeError("proxy unavailable")


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, tools, **kwargs):
        self.calls.append({"messages": messages, "tools": tools, "kwargs": kwargs})
        return self.responses.pop(0)


def add_record(db, user_id: str, value: float = 6.5):
    create_glucose_record(
        db,
        GlucoseCreate(
            user_id=user_id,
            value=value,
            measurement_time=MeasurementTimeEnum.BEFORE_BREAKFAST,
            measurement_method=MeasurementMethodEnum.FINGER_STICK,
        ),
    )


def test_r1_recent_glucose_fallback_has_tool_result(db, user_a):
    add_record(db, user_a.id)
    agent = HealthAgent(HealthToolRegistry(db, user_a), client=FailingClient())

    result = agent.run("最近血糖")

    assert result.mode == "fallback"
    assert result.tool_results[0].name == "list_recent_glucose"
    assert result.tool_results[0].data["count"] == 1


def test_r2_weekly_stats_fallback_returns_real_aggregate(db, user_a):
    add_record(db, user_a.id, 5.0)
    add_record(db, user_a.id, 7.0)
    agent = HealthAgent(HealthToolRegistry(db, user_a), client=FailingClient())

    result = agent.run("本周血糖统计")

    assert result.mode == "fallback"
    assert result.tool_results[0].name == "get_glucose_stats"
    assert result.tool_results[0].data["average"] == 6.0


def test_r3_mock_llm_tool_loop_executes_stats(db, user_a):
    fake = FakeClient(
        [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "get_glucose_stats",
                            "arguments": '{"period":"week"}',
                        },
                    }
                ],
            },
            {"role": "assistant", "content": "本周暂无血糖记录。"},
        ]
    )
    agent = HealthAgent(HealthToolRegistry(db, user_a), client=fake)

    result = agent.run("本周血糖怎么样？")

    assert result.mode == "agent"
    assert result.rounds == 2
    assert result.tool_calls[0].name == "get_glucose_stats"
    assert result.tool_results[0].ok is True
    assert fake.calls[1]["messages"][-1]["role"] == "tool"


def test_r4_llm_failure_falls_back_without_raising(db, user_a):
    result = HealthAgent(
        HealthToolRegistry(db, user_a),
        client=FailingClient(),
    ).run("帮助")

    assert result.mode == "fallback"
    assert "规则模式" in result.reply


def test_r5_disabled_agent_does_not_call_client(db, user_a):
    fake = FakeClient([])

    result = HealthAgent(
        HealthToolRegistry(db, user_a),
        client=fake,
        enabled=False,
    ).run("最近血糖")

    assert result.mode == "disabled"
    assert fake.calls == []


def test_model_cannot_self_confirm_a_write(db, user_a):
    fake = FakeClient(
        [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_write",
                        "type": "function",
                        "function": {
                            "name": "add_glucose_record",
                            "arguments": (
                                '{"value":6.5,"measurement_time":"BEFORE_BREAKFAST",'
                                '"confirm":true}'
                            ),
                        },
                    }
                ],
            }
        ]
    )
    agent = HealthAgent(HealthToolRegistry(db, user_a), client=fake)

    result = agent.run("记录血糖 6.5 空腹", confirm_write=False)

    assert result.mode == "agent"
    assert result.tool_results[0].requires_confirm is True
    assert result.tool_calls[0].arguments["confirm"] is False
    assert db.query(GlucoseRecord).count() == 0


def test_write_intent_falls_back_to_guarded_tool_if_model_avoids_write(db, user_a):
    fake = FakeClient(
        [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_profile",
                        "type": "function",
                        "function": {"name": "get_profile", "arguments": "{}"},
                    }
                ],
            },
            {"role": "assistant", "content": "请先确认。"},
        ]
    )

    result = HealthAgent(HealthToolRegistry(db, user_a), client=fake).run(
        "记录血糖 6.5 空腹",
        confirm_write=False,
    )

    assert result.mode == "fallback"
    assert result.tool_results[0].name == "add_glucose_record"
    assert result.tool_results[0].requires_confirm is True
    assert db.query(GlucoseRecord).count() == 0


def test_runtime_honors_max_tool_rounds(db, user_a):
    repeated_call = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_stats",
                "type": "function",
                "function": {
                    "name": "get_glucose_stats",
                    "arguments": '{"period":"week"}',
                },
            }
        ],
    }
    fake = FakeClient([repeated_call, repeated_call, repeated_call])

    result = HealthAgent(
        HealthToolRegistry(db, user_a),
        client=fake,
        max_rounds=2,
    ).run("本周血糖统计")

    assert result.mode == "agent"
    assert result.rounds == 2
    assert len(fake.calls) == 2
