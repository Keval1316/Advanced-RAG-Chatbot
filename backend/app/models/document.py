import uuid
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, GUID, utc_now

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.knowledge_base import KnowledgeBase


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, index=True
    )
    filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    content_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="uploaded", nullable=False, index=True
    )  # uploaded, processing, ready, failed
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True
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
    knowledge_base: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", back_populates="documents")
    user: Mapped["User"] = relationship("User", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename} status={self.status}>"
