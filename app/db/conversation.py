from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.message import Message
    from app.db.pending_conversation import PendingConversation
    from app.db.visitor import Visitor

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    visitor_id: Mapped[str] = mapped_column(
        ForeignKey("visitors.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    pending_conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("pending_conversations.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    visitor: Mapped["Visitor"] = relationship(back_populates="conversations")
    pending_conversation: Mapped["PendingConversation | None"] = relationship(
        back_populates="conversation"
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
