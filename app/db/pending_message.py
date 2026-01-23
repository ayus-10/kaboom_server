from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.pending_conversation import PendingConversation

class PendingMessage(Base):
    __tablename__ = "pending_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    pending_conversation_id: Mapped[str] = mapped_column(
        ForeignKey("pending_conversations.id", ondelete="CASCADE"),
        index=True,
    )

    sender_visitor_id: Mapped[str] = mapped_column(
        ForeignKey("visitors.id", ondelete="CASCADE"),
        index=True,
    )

    content: Mapped[str] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    pending_conversation: Mapped["PendingConversation"] = relationship(
        back_populates="pending_messages"
    )
