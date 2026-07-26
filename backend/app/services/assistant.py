from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
import json

from app.db.models import Conversation, Message, KnowledgeBase, User
from app.models.assistant import (
    ConversationCreate, ConversationUpdate, Conversation as ConversationSchema,
    MessageCreate, Message as MessageSchema, MessageRoleEnum,
    AssistantResponse, KnowledgeBaseCreate, KnowledgeBaseUpdate
)


_legacy_llm_service = None


def _get_legacy_llm_service():
    """Load the old local-model stack only when an old endpoint actually uses it."""
    global _legacy_llm_service
    if _legacy_llm_service is None:
        from app.ml.llm_service import LLMService

        _legacy_llm_service = LLMService()
    return _legacy_llm_service


def create_conversation(db: Session, conv_in: ConversationCreate) -> Conversation:
    """创建新的对话"""
    # 检查用户是否存在
    user = db.query(User).filter(User.id == conv_in.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 创建对话
    db_conversation = Conversation(
        id=str(uuid.uuid4()),
        user_id=conv_in.user_id,
        title=conv_in.title,
        is_active=True
    )

    # 保存到数据库
    db.add(db_conversation)
    db.flush()

    # 如果有初始消息，添加用户消息
    if conv_in.initial_message:
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=db_conversation.id,
            role=MessageRoleEnum.USER,
            content=conv_in.initial_message,
            timestamp=datetime.now()
        )
        db.add(user_message)

        # 生成助手回复
        try:
            assistant_response = generate_assistant_response(db, user_message.content, db_conversation.user_id)

            # 添加助手消息
            assistant_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=db_conversation.id,
                role=MessageRoleEnum.ASSISTANT,
                content=assistant_response.message,
                timestamp=datetime.now(),
                message_metadata={"sources": assistant_response.sources} if assistant_response.sources else None
            )
            db.add(assistant_message)
        except Exception as e:
            # 如果生成回复失败，添加错误消息
            error_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=db_conversation.id,
                role=MessageRoleEnum.ASSISTANT,
                content="抱歉，我无法处理您的请求。请稍后再试。",
                timestamp=datetime.now(),
                message_metadata={"error": str(e)}
            )
            db.add(error_message)

    db.refresh(db_conversation)
    return db_conversation


def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
    """通过ID获取对话"""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def get_user_conversation(db: Session, conversation_id: str, user_id: str) -> Conversation:
    """Resolve a conversation and enforce ownership in the service layer."""
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在",
        )
    if conversation.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此对话",
        )
    return conversation


def persist_agent_exchange(
    db: Session,
    *,
    user_id: str,
    user_message: str,
    assistant_message: str,
    assistant_metadata: Dict[str, Any],
    conversation_id: Optional[str] = None,
    confirm_write: bool = False,
) -> Conversation:
    """Persist one Agent request/response pair and its tool audit metadata."""
    if conversation_id:
        conversation = get_user_conversation(db, conversation_id, user_id)
    else:
        title = user_message[:20] + ("..." if len(user_message) > 20 else "")
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title or "新对话",
            is_active=True,
        )
        db.add(conversation)
        db.flush()

    now = datetime.now()
    db.add_all(
        [
            Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role=MessageRoleEnum.USER,
                content=user_message,
                timestamp=now,
                message_metadata={
                    "source": "agent_chat",
                    "confirm_write": confirm_write,
                },
            ),
            Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role=MessageRoleEnum.ASSISTANT,
                content=assistant_message,
                timestamp=now,
                message_metadata=assistant_metadata,
            ),
        ]
    )
    conversation.updated_at = now

    try:
        db.commit()
        db.refresh(conversation)
        return conversation
    except Exception:
        db.rollback()
        raise


def get_user_conversations(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
    """获取用户的所有对话"""
    return db.query(Conversation).filter(Conversation.user_id == user_id).order_by(
        desc(Conversation.updated_at)
    ).offset(skip).limit(limit).all()


def update_conversation(db: Session, conversation_id: str, conv_in: ConversationUpdate) -> Conversation:
    """更新对话信息"""
    # 获取对话
    db_conversation = get_conversation(db, conversation_id)
    if not db_conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    # 更新对话
    update_data = conv_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(db_conversation, field) and value is not None:
            setattr(db_conversation, field, value)

    # 保存到数据库
    db.add(db_conversation)
    db.refresh(db_conversation)

    return db_conversation


def delete_conversation(db: Session, conversation_id: str) -> bool:
    """删除对话"""
    db_conversation = get_conversation(db, conversation_id)
    if not db_conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    # 删除相关消息
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()

    # 删除对话
    db.delete(db_conversation)

    return True


def create_message(db: Session, message_in: MessageCreate) -> Message:
    """创建新消息并生成助手回复"""
    # 检查对话是否存在
    conversation = get_conversation(db, message_in.conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    # 创建用户消息
    db_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=message_in.conversation_id,
        role=message_in.role,
        content=message_in.content,
        timestamp=datetime.now(),
        message_metadata=message_in.message_metadata
    )

    # 保存到数据库
    db.add(db_message)
    db.flush()
    db.refresh(db_message)

    # 如果是用户消息，生成助手回复
    if message_in.role == MessageRoleEnum.USER:
        try:
            # 获取用户ID
            user_id = conversation.user_id

            # 生成助手回复
            assistant_response = generate_assistant_response(db, message_in.content, user_id)

            # 创建助手消息
            assistant_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=message_in.conversation_id,
                role=MessageRoleEnum.ASSISTANT,
                content=assistant_response.message,
                timestamp=datetime.now(),
                message_metadata={"sources": assistant_response.sources} if assistant_response.sources else None
            )

            # 保存到数据库
            db.add(assistant_message)
            db.flush()
            db.refresh(assistant_message)

            # 更新对话的更新时间
            conversation.updated_at = datetime.now()
            db.add(conversation)

            return assistant_message
        except Exception as e:
            # 如果生成回复失败，添加错误消息
            error_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=message_in.conversation_id,
                role=MessageRoleEnum.ASSISTANT,
                content="抱歉，我无法处理您的请求。请稍后再试。",
                timestamp=datetime.now(),
                message_metadata={"error": str(e)}
            )
            db.add(error_message)
            db.flush()
            db.refresh(error_message)

            # 更新对话的更新时间
            conversation.updated_at = datetime.now()
            db.add(conversation)

            return error_message

    return db_message


def get_conversation_messages(db: Session, conversation_id: str, skip: int = 0, limit: int = 100) -> List[Message]:
    """获取对话的所有消息"""
    return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(
        Message.timestamp
    ).offset(skip).limit(limit).all()


def generate_assistant_response(db: Session, user_message: str, user_id: str) -> AssistantResponse:
    """生成助手回复"""
    try:
        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 构建用户上下文
        user_context = {
            "name": user.name,
            "gender": user.gender.value if user.gender else None,
            "age": (datetime.now() - user.birth_date).days // 365 if user.birth_date else None,
            "diabetes_type": user.diabetes_type.value if user.diabetes_type else None,
            "diagnosis_date": user.diagnosis_date.isoformat() if user.diagnosis_date else None,
            "height": user.height,
            "weight": user.weight,
            "target_glucose_min": user.target_glucose_min,
            "target_glucose_max": user.target_glucose_max
        }

        # 查询相关知识库
        llm_service = _get_legacy_llm_service()
        knowledge_results = llm_service.search_knowledge_base(user_message)

        # 生成回复
        response_text, sources = llm_service.generate_response(
            user_message,
            user_context=user_context,
            knowledge_sources=knowledge_results
        )

        return AssistantResponse(
            message=response_text,
            sources=sources,
            message_metadata={"user_context": user_context}
        )
    except Exception as e:
        # 记录错误并返回通用错误消息
        print(f"Error generating response: {str(e)}")
        return AssistantResponse(
            message="抱歉，我暂时无法回答您的问题。请稍后再试。",
            message_metadata={"error": str(e)}
        )


def create_knowledge_base_entry(db: Session, entry_in: KnowledgeBaseCreate) -> KnowledgeBase:
    """创建知识库条目"""
    # 创建知识库条目
    db_entry = KnowledgeBase(
        id=str(uuid.uuid4()),
        title=entry_in.title,
        content=entry_in.content,
        source=entry_in.source,
        tags=entry_in.tags
    )

    # 保存到数据库
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    # 更新向量索引
    try:
        _get_legacy_llm_service().add_to_knowledge_base(db_entry.id, db_entry.title, db_entry.content)
    except Exception as e:
        # 如果向量索引更新失败，记录错误但不回滚事务
        print(f"Error updating vector index: {str(e)}")

    return db_entry


def get_knowledge_base_entry(db: Session, entry_id: str) -> Optional[KnowledgeBase]:
    """通过ID获取知识库条目"""
    return db.query(KnowledgeBase).filter(KnowledgeBase.id == entry_id).first()


def get_knowledge_base_entries(db: Session, skip: int = 0, limit: int = 100, tag: Optional[str] = None) -> List[KnowledgeBase]:
    """获取知识库条目"""
    query = db.query(KnowledgeBase)

    # 如果指定了标签，过滤结果
    if tag:
        # 注意：这种方式在PostgreSQL中有效，但在其他数据库中可能需要不同的实现
        query = query.filter(KnowledgeBase.tags.contains([tag]))

    return query.order_by(desc(KnowledgeBase.updated_at)).offset(skip).limit(limit).all()


def update_knowledge_base_entry(db: Session, entry_id: str, entry_in: KnowledgeBaseUpdate) -> KnowledgeBase:
    """更新知识库条目"""
    # 获取条目
    db_entry = get_knowledge_base_entry(db, entry_id)
    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库条目不存在"
        )

    # 更新条目
    update_data = entry_in.model_dump(exclude_unset=True)
    content_updated = "content" in update_data

    for field, value in update_data.items():
        if hasattr(db_entry, field) and value is not None:
            setattr(db_entry, field, value)

    # 保存到数据库
    db.commit()
    db.refresh(db_entry)

    # 如果内容更新了，更新向量索引
    if content_updated:
        try:
            _get_legacy_llm_service().update_knowledge_base(db_entry.id, db_entry.title, db_entry.content)
        except Exception as e:
            # 如果向量索引更新失败，记录错误但不回滚事务
            print(f"Error updating vector index: {str(e)}")

    return db_entry


def delete_knowledge_base_entry(db: Session, entry_id: str) -> bool:
    """删除知识库条目"""
    db_entry = get_knowledge_base_entry(db, entry_id)
    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库条目不存在"
        )

    # 从向量索引中删除
    try:
        _get_legacy_llm_service().delete_from_knowledge_base(entry_id)
    except Exception as e:
        # 如果向量索引删除失败，记录错误但继续删除数据库记录
        print(f"Error deleting from vector index: {str(e)}")

    # 删除数据库记录
    db.delete(db_entry)
    db.commit()

    return True
