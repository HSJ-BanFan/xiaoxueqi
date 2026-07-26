from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentHistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class AgentChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    history: List[AgentHistoryMessage] = Field(default_factory=list, max_length=50)
    confirm_write: bool = False


class ToolCallDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolResultDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    ok: bool
    data: Optional[Any] = None
    requires_confirm: bool = False
    error: Optional[str] = None


class AgentRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: str
    mode: Literal["agent", "fallback", "disabled"]
    model: Optional[str] = None
    rounds: int = 0
    tool_calls: List[ToolCallDTO] = Field(default_factory=list)
    tool_results: List[ToolResultDTO] = Field(default_factory=list)
    disclaimer: str


class AgentChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: str
    conversation_id: str
    mode: Literal["agent", "fallback", "disabled"]
    model: Optional[str] = None
    rounds: int = 0
    tool_calls: List[ToolCallDTO] = Field(default_factory=list)
    tool_results: List[ToolResultDTO] = Field(default_factory=list)
    disclaimer: str
