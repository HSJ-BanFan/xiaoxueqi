from datetime import datetime

import pytest

from app.agent.tools import HealthToolRegistry
from app.db.models import DietRecord, GlucoseRecord
from app.models.diet import MealTypeEnum
from app.models.glucose import (
    GlucoseCreate,
    MeasurementMethodEnum,
    MeasurementTimeEnum,
)
from app.services.glucose import create_glucose_record


def create_glucose(db, user_id: str, value: float):
    return create_glucose_record(
        db,
        GlucoseCreate(
            user_id=user_id,
            value=value,
            measurement_time=MeasurementTimeEnum.BEFORE_BREAKFAST,
            measurement_method=MeasurementMethodEnum.FINGER_STICK,
        ),
    )


def test_t1_get_profile_contains_effective_targets(db, user_a):
    result = HealthToolRegistry(db, user_a).dispatch("get_profile", {})

    assert result.ok is True
    assert result.data["id"] == user_a.id
    assert result.data["effective_target_glucose_min"] == 3.9
    assert result.data["effective_target_glucose_max"] == 10.0


def test_tools_reject_injected_user_id(db, user_a, user_b):
    result = HealthToolRegistry(db, user_a).dispatch(
        "list_recent_glucose",
        {"limit": 10, "user_id": user_b.id},
    )

    assert result.ok is False
    assert "校验失败" in result.error


def test_t2_list_recent_glucose_is_bound_to_current_user(db, user_a, user_b):
    own = create_glucose(db, user_a.id, 6.2)
    create_glucose(db, user_b.id, 9.9)

    result = HealthToolRegistry(db, user_a).dispatch(
        "list_recent_glucose",
        {"limit": 10},
    )

    assert result.ok is True
    assert [item["id"] for item in result.data["records"]] == [own.id]


def test_t3_get_glucose_stats_aggregates_current_period(db, user_a):
    for value in (4.0, 6.0, 8.0):
        create_glucose(db, user_a.id, value)

    result = HealthToolRegistry(db, user_a).dispatch(
        "get_glucose_stats",
        {"period": "week"},
    )

    assert result.ok is True
    assert result.data["count"] == 3
    assert result.data["average"] == 6.0
    assert result.data["min"] == 4.0
    assert result.data["max"] == 8.0


@pytest.mark.parametrize(
    ("value", "expected_level"),
    [(3.0, "low"), (6.5, "in_range"), (12.0, "high")],
)
def test_t4_evaluate_glucose_alert_is_deterministic(db, user_a, value, expected_level):
    result = HealthToolRegistry(db, user_a).dispatch(
        "evaluate_glucose_alert",
        {"value": value},
    )

    assert result.ok is True
    assert result.data["level"] == expected_level


def test_t5_add_without_confirmation_does_not_write(db, user_a):
    registry = HealthToolRegistry(db, user_a, require_confirm_write=True)

    result = registry.dispatch(
        "add_glucose_record",
        {
            "value": 6.5,
            "measurement_time": "BEFORE_BREAKFAST",
            "confirm": False,
        },
    )

    assert result.ok is True
    assert result.requires_confirm is True
    assert db.query(GlucoseRecord).count() == 0


def test_t6_add_with_confirmation_writes_one_record(db, user_a):
    registry = HealthToolRegistry(db, user_a, require_confirm_write=True)

    result = registry.dispatch(
        "add_glucose_record",
        {
            "value": 6.5,
            "measurement_time": "BEFORE_BREAKFAST",
            "confirm": True,
        },
    )

    assert result.ok is True
    assert result.requires_confirm is False
    assert db.query(GlucoseRecord).count() == 1
    assert db.query(GlucoseRecord).one().user_id == user_a.id


def test_list_recent_diet_uses_current_users_service_query(db, user_a, user_b):
    db.add_all(
        [
            DietRecord(
                user_id=user_a.id,
                meal_type=MealTypeEnum.BREAKFAST,
                meal_time=datetime.now(),
                food_items=[],
                total_carbs=20,
                total_calories=200,
            ),
            DietRecord(
                user_id=user_b.id,
                meal_type=MealTypeEnum.DINNER,
                meal_time=datetime.now(),
                food_items=[],
                total_carbs=99,
                total_calories=999,
            ),
        ]
    )
    db.commit()

    result = HealthToolRegistry(db, user_a).dispatch("list_recent_diet", {"limit": 10})

    assert result.ok is True
    assert result.data["count"] == 1
    assert result.data["records"][0]["user_id"] == user_a.id
