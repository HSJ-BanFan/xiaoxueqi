from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Mapping, Optional, Type

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import User
from app.models.glucose import (
    GlucoseCreate,
    MeasurementMethodEnum,
    MeasurementTimeEnum,
)
from app.agent.schemas import ToolResultDTO
from app.services.diet import get_user_diet_records
from app.services.glucose import (
    create_glucose_record,
    get_glucose_statistics,
    get_user_glucose_records,
)
from app.services.knowledge_retrieval import KnowledgeRetriever


logger = logging.getLogger(__name__)


class _StrictArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _EmptyArgs(_StrictArgs):
    pass


class _LimitArgs(_StrictArgs):
    limit: int = Field(default=10, ge=1, le=50)


class _StatsArgs(_StrictArgs):
    period: Literal["day", "week", "month", "quarter"] = "week"


class _AlertArgs(_StrictArgs):
    value: float = Field(gt=0, le=100)


class _AddGlucoseArgs(_StrictArgs):
    value: float = Field(gt=0, le=100)
    measurement_time: MeasurementTimeEnum
    measurement_method: MeasurementMethodEnum = MeasurementMethodEnum.FINGER_STICK
    notes: Optional[str] = Field(default=None, max_length=500)
    confirm: bool = False


class _SearchKnowledgeArgs(_StrictArgs):
    query: str = Field(min_length=2, max_length=200)
    limit: int = Field(default=3, ge=1, le=5)


class HealthToolRegistry:
    """Tools bound to one authenticated user and one request-scoped DB session."""

    def __init__(
        self,
        db: Session,
        current_user: User,
        *,
        require_confirm_write: Optional[bool] = None,
    ) -> None:
        self.db = db
        self.current_user = current_user
        self.require_confirm_write = (
            settings.AGENT_REQUIRE_CONFIRM_WRITE
            if require_confirm_write is None
            else require_confirm_write
        )
        self._specs: Dict[str, tuple[Type[BaseModel], str, Any]] = {
            "get_profile": (_EmptyArgs, "读取当前登录用户的非敏感健康档案摘要。", self._get_profile),
            "list_recent_glucose": (
                _LimitArgs,
                "列出当前用户最近的血糖记录。",
                self._list_recent_glucose,
            ),
            "get_glucose_stats": (
                _StatsArgs,
                "计算当前用户指定周期的血糖统计。",
                self._get_glucose_stats,
            ),
            "evaluate_glucose_alert": (
                _AlertArgs,
                "用确定性目标范围规则评估一个血糖值。",
                self._evaluate_glucose_alert,
            ),
            "add_glucose_record": (
                _AddGlucoseArgs,
                "预览或写入当前用户的一条血糖记录；写入需要确认。",
                self._add_glucose_record,
            ),
            "list_recent_diet": (
                _LimitArgs,
                "列出当前用户最近的饮食记录。",
                self._list_recent_diet,
            ),
            "search_knowledge": (
                _SearchKnowledgeArgs,
                "检索糖尿病自我管理的权威科普资料；回答常识性问题前必须先调用。"
                "不用于查询用户本人的血糖、饮食或档案数据。",
                self._search_knowledge,
            ),
        }

    @property
    def names(self) -> List[str]:
        return list(self._specs)

    def openai_schemas(self) -> List[Dict[str, Any]]:
        """Return the strict function schemas sent to an OpenAI-compatible model."""
        schemas: List[Dict[str, Any]] = []
        for name, (arg_model, description, _) in self._specs.items():
            schema = arg_model.model_json_schema()
            # Pydantic emits no properties for the empty model, which is valid JSON schema.
            schema.pop("title", None)
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": schema,
                    },
                }
            )
        return schemas

    def dispatch(self, name: str, arguments: Optional[Mapping[str, Any]] = None) -> ToolResultDTO:
        spec = self._specs.get(name)
        if spec is None:
            return ToolResultDTO(name=name, ok=False, error="未知工具")

        arg_model, _, handler = spec
        raw_arguments: Mapping[str, Any] = arguments or {}
        if not isinstance(raw_arguments, Mapping):
            return ToolResultDTO(name=name, ok=False, error="工具参数必须是对象")

        try:
            parsed = arg_model.model_validate(dict(raw_arguments))
        except ValidationError as exc:
            return ToolResultDTO(
                name=name,
                ok=False,
                error=f"工具参数校验失败: {exc.errors()[0].get('msg', '参数无效')}",
            )

        try:
            return handler(parsed)
        except HTTPException as exc:
            return ToolResultDTO(name=name, ok=False, error=str(exc.detail))
        except Exception:
            logger.exception("Tool %s failed for user %s", name, self.current_user.id)
            return ToolResultDTO(name=name, ok=False, error="工具执行失败，请稍后重试")

    def _get_profile(self, _: _EmptyArgs) -> ToolResultDTO:
        user = self.current_user
        return ToolResultDTO(
            name="get_profile",
            ok=True,
            data={
                "id": user.id,
                "name": user.name,
                "diabetes_type": _enum_value(user.diabetes_type),
                "target_glucose_min": user.target_glucose_min,
                "target_glucose_max": user.target_glucose_max,
                "effective_target_glucose_min": user.target_glucose_min or 3.9,
                "effective_target_glucose_max": user.target_glucose_max or 10.0,
                "height": user.height,
                "weight": user.weight,
            },
        )

    def _list_recent_glucose(self, args: _LimitArgs) -> ToolResultDTO:
        records = get_user_glucose_records(
            db=self.db,
            user_id=self.current_user.id,
            limit=args.limit,
        )
        data = [_glucose_payload(record) for record in records]
        return ToolResultDTO(
            name="list_recent_glucose",
            ok=True,
            data={"records": data, "count": len(data)},
        )

    def _get_glucose_stats(self, args: _StatsArgs) -> ToolResultDTO:
        stats = get_glucose_statistics(
            db=self.db,
            user_id=self.current_user.id,
            period=args.period,
        )
        return ToolResultDTO(
            name="get_glucose_stats",
            ok=True,
            data=stats.model_dump(mode="json"),
        )

    def _evaluate_glucose_alert(self, args: _AlertArgs) -> ToolResultDTO:
        target_min = self.current_user.target_glucose_min or 3.9
        target_max = self.current_user.target_glucose_max or 10.0
        if args.value < target_min:
            level = "low"
            advice = "数值低于目标下限，请先复核测量并按个人医嘱处理；如有不适请及时就医。"
        elif args.value > target_max:
            level = "high"
            advice = "数值高于目标上限，请复核测量、记录相关情况，并按个人医嘱处理。"
        else:
            level = "in_range"
            advice = "数值在当前目标范围内，继续按计划监测和记录。"

        return ToolResultDTO(
            name="evaluate_glucose_alert",
            ok=True,
            data={
                "level": level,
                "value": args.value,
                "target_min": target_min,
                "target_max": target_max,
                "advice": advice,
            },
        )

    def _add_glucose_record(self, args: _AddGlucoseArgs) -> ToolResultDTO:
        preview = {
            "value": args.value,
            "measurement_time": args.measurement_time.value,
            "measurement_method": args.measurement_method.value,
            "notes": args.notes,
        }
        if self.require_confirm_write and not args.confirm:
            return ToolResultDTO(
                name="add_glucose_record",
                ok=True,
                data={"preview": preview},
                requires_confirm=True,
            )

        record = create_glucose_record(
            db=self.db,
            record_in=GlucoseCreate(
                user_id=self.current_user.id,
                value=args.value,
                measurement_time=args.measurement_time,
                measurement_method=args.measurement_method,
                notes=args.notes,
            ),
        )
        return ToolResultDTO(
            name="add_glucose_record",
            ok=True,
            data={"record": _glucose_payload(record)},
        )

    def _list_recent_diet(self, args: _LimitArgs) -> ToolResultDTO:
        page = get_user_diet_records(
            db=self.db,
            user_id=self.current_user.id,
            skip=0,
            limit=args.limit,
        )
        records = [item.model_dump(mode="json") for item in page.data]
        return ToolResultDTO(
            name="list_recent_diet",
            ok=True,
            data={"records": records, "count": len(records), "total": page.total},
        )

    def _search_knowledge(self, args: _SearchKnowledgeArgs) -> ToolResultDTO:
        result = KnowledgeRetriever(self.db).search(args.query, limit=args.limit)
        return ToolResultDTO(
            name="search_knowledge",
            ok=True,
            data=result.model_dump(mode="json"),
        )


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _glucose_payload(record: Any) -> Dict[str, Any]:
    return jsonable_encoder(
        {
            "id": record.id,
            "value": record.value,
            "measurement_time": _enum_value(record.measurement_time),
            "measurement_method": _enum_value(record.measurement_method),
            "measured_at": record.measured_at,
            "notes": record.notes,
        }
    )
