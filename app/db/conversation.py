from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.message import Message
    from app.db.pending_conversation import PendingConversation
    from app.db.user import User
    from app.db.visitor import Visitor

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    visitor_id: Mapped[str] = mapped_column(
        ForeignKey("visitors.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    pending_conversation_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("pending_conversations.id", ondelete="SET NULL"),
        unique=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
    )

    visitor: Mapped["Visitor"] = relationship(back_populates="conversations")
    user: Mapped["User"] = relationship(back_populates="conversations")

    pending_conversation: Mapped[Optional["PendingConversation"]] = relationship(
        back_populates="conversation",
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
