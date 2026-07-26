from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from enum import Enum


class MessageRoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: MessageRoleEnum
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    message_metadata: Optional[Dict[str, Any]] = None


class ConversationBase(BaseModel):
    user_id: str
    title: str
    messages: List[Message]
    is_active: bool = True


class ConversationCreate(BaseModel):
    user_id: str
    title: str = "新对话"
    initial_message: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None


class Conversation(ConversationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    conversation_id: str
    content: str
    role: MessageRoleEnum = MessageRoleEnum.USER
    message_metadata: Optional[Dict[str, Any]] = None


class AssistantResponse(BaseModel):
    message: str
    sources: Optional[List[Dict[str, Any]]] = None
    message_metadata: Optional[Dict[str, Any]] = None


class KnowledgeBase(BaseModel):
    id: str
    title: str
    content: str
    source: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseCreate(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    tags: List[str] = []


class KnowledgeBaseUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
