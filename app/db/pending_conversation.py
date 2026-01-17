from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.conversation import Conversation
    from app.db.visitor import Visitor

class PendingConversation(Base):
    __tablename__ = "pending_conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    visitor_id: Mapped[str] = mapped_column(
        ForeignKey("visitors.id", ondelete="CASCADE"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
    )

    visitor: Mapped["Visitor"] = relationship(back_populates="pending_conversations")
    conversation: Mapped[Optional["Conversation"]] = relationship(
        back_populates="pending_conversation",
        uselist=False,
    )
