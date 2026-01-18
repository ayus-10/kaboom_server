from datetime import UTC, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.actor import Actor
    from app.db.conversation import Conversation
    from app.db.refresh_token import RefreshToken


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    first_name: Mapped[Optional[str]]
    last_name: Mapped[Optional[str]]
    avatar_url: Mapped[Optional[str]]

    actor_id: Mapped[str] = mapped_column(
        ForeignKey("actors.id"),
        unique=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    actor: Mapped["Actor"] = relationship()

    conversations: Mapped[List["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
