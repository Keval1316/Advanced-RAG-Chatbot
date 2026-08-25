import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.rag import Citation


class ConversationCreate(BaseModel):
    title: Optional[str] = Field("New Conversation", max_length=255)
    knowledge_base_id: uuid.UUID


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    knowledge_base_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    citations: Optional[List[Citation]] = Field(default_factory=list)
    msg_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime


class SendMessageRequest(BaseModel):
    knowledge_base_id: uuid.UUID
    message: str = Field(..., min_length=1)
    conversation_id: Optional[uuid.UUID] = None


class SendMessageResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    citations: List[Citation]
    metadata: Dict[str, Any]
