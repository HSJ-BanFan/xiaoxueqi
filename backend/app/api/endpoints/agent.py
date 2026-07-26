from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.runtime import HealthAgent
from app.agent.schemas import AgentChatRequest, AgentChatResponse
from app.agent.tools import HealthToolRegistry
from app.api.deps import get_current_user, get_db
from app.db.models import User
from app.services.assistant import get_user_conversation, persist_agent_exchange


router = APIRouter()


@router.post("/chat", response_model=AgentChatResponse)
def chat_with_agent(
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    if request.conversation_id:
        get_user_conversation(db, request.conversation_id, current_user.id)

    registry = HealthToolRegistry(db=db, current_user=current_user)
    result = HealthAgent(registry=registry).run(
        request.message,
        request.history,
        confirm_write=request.confirm_write,
    )

    audit_metadata = {
        "mode": result.mode,
        "model": result.model,
        "rounds": result.rounds,
        "tool_calls": [item.model_dump(mode="json") for item in result.tool_calls],
        "tool_results": [item.model_dump(mode="json") for item in result.tool_results],
    }
    conversation = persist_agent_exchange(
        db,
        user_id=current_user.id,
        user_message=request.message,
        assistant_message=result.reply,
        assistant_metadata=audit_metadata,
        conversation_id=request.conversation_id,
        confirm_write=request.confirm_write,
    )

    return AgentChatResponse(
        **result.model_dump(),
        conversation_id=conversation.id,
    )
