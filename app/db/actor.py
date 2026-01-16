from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Actor(Base):
    __tablename__ = "actors"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(
        Enum("user", "visitor", name="actor_type"),
        index=True,
    )
