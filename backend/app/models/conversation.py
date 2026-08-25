import uuid
from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, GUID, utc_now

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.knowledge_base import KnowledgeBase
    from backend.app.models.message import Message


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, index=True
    )
    title: Mapped[str] = mapped_column(
        String(255), default="New Conversation", nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    knowledge_base: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} title={self.title} kb_id={self.knowledge_base_id}>"
