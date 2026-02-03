from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.conversation import Conversation
    from app.db.pending_conversation import PendingConversation
    from app.db.project import Project

class Widget(Base):
    __tablename__ = "widgets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )

    site_url: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
    )

    project: Mapped["Project"] = relationship(back_populates="widgets")

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="widget",
        cascade="all, delete-orphan",
    )
    pending_conversations: Mapped[list["PendingConversation"]] = relationship(
        back_populates="widget",
        cascade="all, delete-orphan",
    )
