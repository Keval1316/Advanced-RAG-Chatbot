import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, GUID, utc_now

if TYPE_CHECKING:
    from backend.app.models.conversation import Conversation


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, index=True
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    citations: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, nullable=True, default=list
    )
    msg_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata", JSON, nullable=True, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role} conv_id={self.conversation_id}>"
