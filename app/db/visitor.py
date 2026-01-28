from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.actor import Actor
    from app.db.conversation import Conversation
    from app.db.pending_conversation import PendingConversation

class Visitor(Base):
    __tablename__ = "visitors"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    display_id: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))

    actor_id: Mapped[str] = mapped_column(
        ForeignKey("actors.id"),
        unique=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    pending_conversations: Mapped[list["PendingConversation"]] = relationship(
        back_populates="visitor",
        cascade="all, delete-orphan",
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="visitor",
    )

    actor: Mapped["Actor"] = relationship()
