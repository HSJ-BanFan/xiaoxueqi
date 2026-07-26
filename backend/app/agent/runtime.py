from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence

from app.agent.llm_client import LLMClientError, OpenAICompatibleClient
from app.agent.prompts import DISCLAIMER, SYSTEM_PROMPT, with_disclaimer
from app.agent.schemas import (
    AgentHistoryMessage,
    AgentRunResult,
    ToolCallDTO,
    ToolResultDTO,
)
from app.agent.tools import HealthToolRegistry
from app.core.config import settings
from app.models.glucose import MeasurementTimeEnum


logger = logging.getLogger(__name__)

_RECORD_PATTERNS = (
    re.compile(r"(?:记录|添加|录入)(?:一下)?(?:我的)?(?:血糖)?\s*(?:为|是|[:：])?\s*(\d{1,2}(?:\.\d+)?)"),
    re.compile(r"血糖\s*(?:为|是|[:：])?\s*(\d{1,2}(?:\.\d+)?)\s*(?:，|,|。|\s)*(?:请)?(?:帮我)?(?:记录|添加|录入)"),
)


class HealthAgent:
    def __init__(
        self,
        registry: HealthToolRegistry,
        client: Optional[Any] = None,
        *,
        enabled: Optional[bool] = None,
        model: Optional[str] = None,
        max_rounds: Optional[int] = None,
    ) -> None:
        self.registry = registry
        self.enabled = settings.AGENT_ENABLED if enabled is None else enabled
        self.model = model or settings.LLM_MODEL
        self.max_rounds = max_rounds or settings.LLM_MAX_TOOL_ROUNDS
        self.client = client or OpenAICompatibleClient(model=self.model)

    def run(
        self,
        message: str,
        history: Optional[Sequence[AgentHistoryMessage | Dict[str, str]]] = None,
        *,
        confirm_write: bool = False,
    ) -> AgentRunResult:
        if not self.enabled:
            return AgentRunResult(
                reply=with_disclaimer("智能助理当前已停用，你仍可使用血糖与健康记录接口。"),
                mode="disabled",
                model=self.model,
                rounds=0,
                disclaimer=DISCLAIMER,
            )

        messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self._history_payload(history or []))
        messages.append({"role": "user", "content": message})

        tool_calls: List[ToolCallDTO] = []
        tool_results: List[ToolResultDTO] = []
        rounds = 0

        try:
            while rounds < self.max_rounds:
                rounds += 1
                assistant_message = self.client.chat(
                    messages,
                    self.registry.openai_schemas(),
                    model=self.model,
                )
                raw_tool_calls = assistant_message.get("tool_calls") or []

                if not raw_tool_calls:
                    content = assistant_message.get("content")
                    if not isinstance(content, str) or not content.strip():
                        raise LLMClientError("模型未返回有效文本")
                    if self._needs_write_fallback(message, tool_results):
                        return self.fallback(
                            message,
                            confirm_write=confirm_write,
                            rounds=rounds,
                        )
                    return AgentRunResult(
                        reply=with_disclaimer(content),
                        mode="agent",
                        model=self.model,
                        rounds=rounds,
                        tool_calls=tool_calls,
                        tool_results=tool_results,
                        disclaimer=DISCLAIMER,
                    )

                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_message.get("content"),
                        "tool_calls": raw_tool_calls,
                    }
                )

                for raw_call in raw_tool_calls:
                    call, parse_error = self._parse_tool_call(raw_call, len(tool_calls) + 1)
                    arguments = dict(call.arguments)
                    if call.name == "add_glucose_record":
                        # A model can propose a write, but only the authenticated API
                        # request can grant confirmation.
                        arguments["confirm"] = bool(confirm_write)
                        call = call.model_copy(update={"arguments": arguments})

                    tool_calls.append(call)
                    if parse_error:
                        result = ToolResultDTO(name=call.name, ok=False, error=parse_error)
                    else:
                        result = self.registry.dispatch(call.name, arguments)
                    tool_results.append(result)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "name": call.name,
                            "content": json.dumps(
                                result.model_dump(mode="json"),
                                ensure_ascii=False,
                            ),
                        }
                    )

                write_reply = self._write_guard_reply(tool_results)
                if write_reply is not None:
                    return AgentRunResult(
                        reply=with_disclaimer(write_reply),
                        mode="agent",
                        model=self.model,
                        rounds=rounds,
                        tool_calls=tool_calls,
                        tool_results=tool_results,
                        disclaimer=DISCLAIMER,
                    )

            if self._needs_write_fallback(message, tool_results):
                return self.fallback(
                    message,
                    confirm_write=confirm_write,
                    rounds=rounds,
                )
            return AgentRunResult(
                reply=with_disclaimer(self._render_results(tool_results, "工具调用轮数已达上限。")),
                mode="agent",
                model=self.model,
                rounds=rounds,
                tool_calls=tool_calls,
                tool_results=tool_results,
                disclaimer=DISCLAIMER,
            )
        except Exception as exc:
            logger.info("Agent LLM path fell back after %s", exc.__class__.__name__)
            return self.fallback(
                message,
                confirm_write=confirm_write,
                rounds=rounds,
            )

    def fallback(
        self,
        message: str,
        *,
        confirm_write: bool = False,
        rounds: int = 0,
    ) -> AgentRunResult:
        call: Optional[ToolCallDTO] = None
        result: Optional[ToolResultDTO] = None

        value = self._extract_glucose_value(message)
        if value is not None:
            arguments = {
                "value": value,
                "measurement_time": self._measurement_time(message).value,
                "confirm": confirm_write,
            }
            call = ToolCallDTO(name="add_glucose_record", arguments=arguments)
            result = self.registry.dispatch(call.name, arguments)
            reply = self._write_guard_reply([result]) or self._render_results([result])
        elif any(keyword in message for keyword in ("统计", "达标", "周报", "平均")):
            arguments = {"period": self._stats_period(message)}
            call = ToolCallDTO(name="get_glucose_stats", arguments=arguments)
            result = self.registry.dispatch(call.name, arguments)
            reply = self._render_stats(result)
        elif any(keyword in message for keyword in ("最近血糖", "查血糖", "血糖记录")):
            arguments = {"limit": 10}
            call = ToolCallDTO(name="list_recent_glucose", arguments=arguments)
            result = self.registry.dispatch(call.name, arguments)
            reply = self._render_recent_glucose(result)
        else:
            reply = (
                "当前处于规则模式。你可以说：“最近血糖”、“本周血糖统计”，"
                "或“记录血糖 6.5 空腹”；写入时需再次携带 confirm_write=true 确认。"
            )

        return AgentRunResult(
            reply=with_disclaimer(reply),
            mode="fallback",
            model=self.model,
            rounds=rounds,
            tool_calls=[call] if call else [],
            tool_results=[result] if result else [],
            disclaimer=DISCLAIMER,
        )

    @staticmethod
    def _history_payload(
        history: Iterable[AgentHistoryMessage | Dict[str, str]],
    ) -> List[Dict[str, str]]:
        payload: List[Dict[str, str]] = []
        for item in history:
            parsed = item if isinstance(item, AgentHistoryMessage) else AgentHistoryMessage.model_validate(item)
            payload.append(parsed.model_dump())
        return payload

    @staticmethod
    def _parse_tool_call(raw_call: Any, index: int) -> tuple[ToolCallDTO, Optional[str]]:
        if not isinstance(raw_call, dict):
            return ToolCallDTO(id=f"call_{index}", name="invalid_tool", arguments={}), "工具调用格式无效"

        function = raw_call.get("function")
        if not isinstance(function, dict):
            return ToolCallDTO(id=str(raw_call.get("id") or f"call_{index}"), name="invalid_tool", arguments={}), "工具调用缺少 function"

        name = str(function.get("name") or "invalid_tool")
        raw_arguments = function.get("arguments", {})
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
                parse_error = "工具参数不是有效 JSON"
            else:
                parse_error = None
        elif isinstance(raw_arguments, dict):
            arguments = raw_arguments
            parse_error = None
        else:
            arguments = {}
            parse_error = "工具参数必须是对象"

        if not isinstance(arguments, dict):
            arguments = {}
            parse_error = "工具参数必须是对象"

        return (
            ToolCallDTO(
                id=str(raw_call.get("id") or f"call_{index}"),
                name=name,
                arguments=arguments,
            ),
            parse_error,
        )

    @staticmethod
    def _extract_glucose_value(message: str) -> Optional[float]:
        for pattern in _RECORD_PATTERNS:
            match = pattern.search(message)
            if match:
                return float(match.group(1))
        return None

    @classmethod
    def _needs_write_fallback(
        cls,
        message: str,
        results: Sequence[ToolResultDTO],
    ) -> bool:
        return cls._extract_glucose_value(message) is not None and not any(
            result.name == "add_glucose_record" for result in results
        )

    @staticmethod
    def _measurement_time(message: str) -> MeasurementTimeEnum:
        mappings = (
            (("早餐后", "早饭后"), MeasurementTimeEnum.AFTER_BREAKFAST),
            (("午餐后", "午饭后"), MeasurementTimeEnum.AFTER_LUNCH),
            (("晚餐后", "晚饭后"), MeasurementTimeEnum.AFTER_DINNER),
            (("早餐前", "早饭前", "空腹"), MeasurementTimeEnum.BEFORE_BREAKFAST),
            (("午餐前", "午饭前"), MeasurementTimeEnum.BEFORE_LUNCH),
            (("晚餐前", "晚饭前"), MeasurementTimeEnum.BEFORE_DINNER),
            (("睡前",), MeasurementTimeEnum.BEFORE_SLEEP),
            (("凌晨", "半夜"), MeasurementTimeEnum.MIDNIGHT),
            (("餐后",), MeasurementTimeEnum.AFTER_BREAKFAST),
        )
        for keywords, measurement_time in mappings:
            if any(keyword in message for keyword in keywords):
                return measurement_time
        return MeasurementTimeEnum.OTHER

    @staticmethod
    def _stats_period(message: str) -> str:
        if any(keyword in message for keyword in ("季度", "三个月", "近90天")):
            return "quarter"
        if any(keyword in message for keyword in ("月", "30天")):
            return "month"
        if any(keyword in message for keyword in ("今天", "今日", "当天")):
            return "day"
        return "week"

    @staticmethod
    def _write_guard_reply(results: Sequence[ToolResultDTO]) -> Optional[str]:
        writes = [result for result in results if result.name == "add_glucose_record"]
        if not writes:
            return None
        result = writes[-1]
        if result.requires_confirm:
            preview = (result.data or {}).get("preview", {}) if isinstance(result.data, dict) else {}
            return (
                f"准备记录血糖 {preview.get('value')} mmol/L，测量时段为 "
                f"{preview.get('measurement_time')}。当前尚未写入数据库；请确认后重试。"
            )
        if not result.ok:
            return f"血糖记录未写入：{result.error or '工具执行失败'}。"
        record = (result.data or {}).get("record", {}) if isinstance(result.data, dict) else {}
        return (
            f"已记录血糖 {record.get('value')} mmol/L，测量时段为 "
            f"{record.get('measurement_time')}。"
        )

    @staticmethod
    def _render_stats(result: ToolResultDTO) -> str:
        if not result.ok or not isinstance(result.data, dict):
            return f"暂时无法计算血糖统计：{result.error or '没有可用结果'}。"
        data = result.data
        if data.get("count", 0) == 0:
            return f"{data.get('period', '当前周期')}内还没有血糖记录。"
        return (
            f"{data.get('period')}血糖共 {data.get('count')} 条，平均 {data.get('average')} mmol/L，"
            f"最低 {data.get('min')}、最高 {data.get('max')} mmol/L，"
            f"达标率 {data.get('in_range_percentage')}%。"
        )

    @staticmethod
    def _render_recent_glucose(result: ToolResultDTO) -> str:
        if not result.ok or not isinstance(result.data, dict):
            return f"暂时无法读取最近血糖：{result.error or '没有可用结果'}。"
        records = result.data.get("records") or []
        if not records:
            return "还没有可显示的血糖记录。"
        lines = ["最近血糖记录："]
        for record in records[:5]:
            lines.append(
                f"- {record.get('measured_at')}：{record.get('value')} mmol/L（{record.get('measurement_time')}）"
            )
        if len(records) > 5:
            lines.append(f"另有 {len(records) - 5} 条记录未展开。")
        return "\n".join(lines)

    @classmethod
    def _render_results(cls, results: Sequence[ToolResultDTO], prefix: str = "") -> str:
        if results:
            latest = results[-1]
            if latest.name == "get_glucose_stats":
                rendered = cls._render_stats(latest)
            elif latest.name == "list_recent_glucose":
                rendered = cls._render_recent_glucose(latest)
            elif latest.ok:
                rendered = "工具已执行，结果可在本次响应的 tool_results 中查看。"
            else:
                rendered = f"工具执行失败：{latest.error or '未知错误'}。"
        else:
            rendered = "没有可用的工具结果。"
        return f"{prefix}\n{rendered}".strip()
