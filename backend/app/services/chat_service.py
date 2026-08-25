import uuid
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import NotFoundException, ForbiddenException
from backend.app.core.logging import logger
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.schemas.chat import ConversationResponse
from backend.app.schemas.rag import ChatResponse
from backend.app.rag.pipeline import rag_pipeline


class ChatService:
    @staticmethod
    def create_conversation(
        db: Session,
        user_id: uuid.UUID,
        kb_id: uuid.UUID,
        title: Optional[str] = "New Conversation"
    ) -> Conversation:
        # Validate KB ownership
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise NotFoundException(message=f"Knowledge base {kb_id} not found.")
        if kb.user_id != user_id:
            raise ForbiddenException(message="You do not have permission to access this knowledge base.")

        conv = Conversation(
            title=title or "New Conversation",
            user_id=user_id,
            knowledge_base_id=kb_id
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        logger.info(f"Created conversation '{conv.title}' ({conv.id}) for user {user_id}")
        return conv

    @staticmethod
    def get_conversation(
        db: Session,
        conv_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Conversation:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv:
            raise NotFoundException(message=f"Conversation {conv_id} not found.")
        if conv.user_id != user_id:
            raise ForbiddenException(message="You do not have permission to access this conversation.")
        return conv

    @staticmethod
    def list_conversations(
        db: Session,
        user_id: uuid.UUID,
        kb_id: Optional[uuid.UUID] = None
    ) -> List[ConversationResponse]:
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        if kb_id:
            query = query.filter(Conversation.knowledge_base_id == kb_id)
        conversations = query.order_by(Conversation.updated_at.desc()).all()

        results = []
        for c in conversations:
            msg_count = db.query(Message).filter(Message.conversation_id == c.id).count()
            results.append(
                ConversationResponse(
                    id=c.id,
                    title=c.title,
                    knowledge_base_id=c.knowledge_base_id,
                    user_id=c.user_id,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    message_count=msg_count
                )
            )
        return results

    @classmethod
    def delete_conversation(
        cls,
        db: Session,
        conv_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        conv = cls.get_conversation(db, conv_id, user_id)
        db.delete(conv)
        db.commit()
        logger.info(f"Deleted conversation {conv_id} for user {user_id}")
        return True

    @classmethod
    def get_messages(
        cls,
        db: Session,
        conv_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50
    ) -> List[Message]:
        conv = cls.get_conversation(db, conv_id, user_id)
        return db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.asc()).limit(limit).all()

    @classmethod
    def send_message(
        cls,
        db: Session,
        user_id: uuid.UUID,
        kb_id: uuid.UUID,
        message_text: str,
        conv_id: Optional[uuid.UUID] = None
    ) -> Tuple[Conversation, Message, Message, ChatResponse]:
        # 1. Get or Create conversation
        if conv_id:
            conv = cls.get_conversation(db, conv_id, user_id)
        else:
            title = message_text[:40] + ("..." if len(message_text) > 40 else "")
            conv = cls.create_conversation(db, user_id, kb_id, title=title)

        # 2. Store user message in DB
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=message_text.strip(),
            citations=[],
            msg_metadata={}
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # 3. Load recent conversation history (sliding window)
        past_messages = db.query(Message).filter(
            Message.conversation_id == conv.id,
            Message.id != user_msg.id
        ).order_by(Message.created_at.asc()).all()

        history_payload: List[Dict[str, str]] = []
        for m in past_messages[-settings.MAX_HISTORY_MESSAGES:]:
            history_payload.append({"role": m.role, "content": m.content})

        # 4. Execute Advanced RAG Pipeline
        rag_response = rag_pipeline.execute(
            query=message_text.strip(),
            user_id=user_id,
            kb_id=kb_id,
            conversation_id=conv.id,
            conversation_history=history_payload
        )

        # 5. Store assistant message in DB
        citations_data = [c.model_dump(mode="json") for c in rag_response.citations]
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=rag_response.answer,
            citations=citations_data,
            msg_metadata=rag_response.metadata
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        return conv, user_msg, assistant_msg, rag_response


chat_service = ChatService()
