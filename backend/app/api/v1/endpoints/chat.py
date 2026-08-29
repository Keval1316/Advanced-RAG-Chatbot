import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_active_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.common import APIResponse
from backend.app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse
)
from backend.app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["Chat & Conversations"])


@router.post(
    "/message",
    response_model=APIResponse[SendMessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Send a message to the RAG Knowledge Assistant"
)
def send_chat_message(
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[SendMessageResponse]:
    conv, user_msg, assistant_msg, rag_response = chat_service.send_message(
        db=db,
        user_id=current_user.id,
        kb_id=payload.knowledge_base_id,
        message_text=payload.message,
        conv_id=payload.conversation_id
    )

    response_data = SendMessageResponse(
        conversation_id=conv.id,
        message_id=assistant_msg.id,
        answer=rag_response.answer,
        citations=rag_response.citations,
        metadata=rag_response.metadata
    )

    return APIResponse(
        success=True,
        message="Message processed successfully.",
        data=response_data
    )


@router.post(
    "/conversations",
    response_model=APIResponse[ConversationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation thread"
)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[ConversationResponse]:
    conv = chat_service.create_conversation(
        db=db,
        user_id=current_user.id,
        kb_id=payload.knowledge_base_id,
        title=payload.title
    )
    return APIResponse(
        success=True,
        message="Conversation created successfully.",
        data=ConversationResponse(
            id=conv.id,
            title=conv.title,
            knowledge_base_id=conv.knowledge_base_id,
            user_id=conv.user_id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=0
        )
    )


@router.get(
    "/conversations",
    response_model=APIResponse[List[ConversationResponse]],
    status_code=status.HTTP_200_OK,
    summary="List conversations owned by authenticated user"
)
def list_conversations(
    kb_id: Optional[uuid.UUID] = Query(None, description="Filter by Knowledge Base UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[List[ConversationResponse]]:
    conversations = chat_service.list_conversations(
        db=db,
        user_id=current_user.id,
        kb_id=kb_id
    )
    return APIResponse(
        success=True,
        message="Conversations retrieved successfully.",
        data=conversations
    )


@router.get(
    "/conversations/{conv_id}/messages",
    response_model=APIResponse[List[MessageResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get all messages in a conversation"
)
def get_conversation_messages(
    conv_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[List[MessageResponse]]:
    messages = chat_service.get_messages(
        db=db,
        conv_id=conv_id,
        user_id=current_user.id,
        limit=limit
    )
    message_responses = [
        MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            citations=m.citations or [],
            msg_metadata=m.msg_metadata or {},
            created_at=m.created_at
        )
        for m in messages
    ]
    return APIResponse(
        success=True,
        message="Conversation messages retrieved successfully.",
        data=message_responses
    )


@router.delete(
    "/conversations/{conv_id}",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete conversation thread and associated messages"
)
def delete_conversation(
    conv_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[dict]:
    chat_service.delete_conversation(
        db=db,
        conv_id=conv_id,
        user_id=current_user.id
    )
    return APIResponse(
        success=True,
        message="Conversation deleted successfully.",
        data={"id": str(conv_id)}
    )


@router.post(
    "/generate-direct",
    summary="Direct generation endpoint via backend Groq failover pool"
)
async def generate_direct(payload: dict):
    from backend.app.services.llm_service import llm_service
    messages = payload.get("messages", [])
    model = payload.get("model")
    temperature = payload.get("temperature", 0.1)
    max_tokens = payload.get("max_tokens", 2048)

    try:
        content = llm_service.generate_chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

