import uuid
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, GUID, utc_now

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.document import Document
    from backend.app.models.conversation import Conversation


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="knowledge_bases")
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="knowledge_base", cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="knowledge_base", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBase id={self.id} name={self.name} user_id={self.user_id}>"
