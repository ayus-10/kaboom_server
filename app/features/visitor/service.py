import uuid
from typing import Optional

from nanoid import generate
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import MAX_RETRIES, NANO_ALPHABET, NANO_LENGTH
from app.db.actor import Actor
from app.db.visitor import Visitor


class VisitorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_visitor(self, name: Optional[str], email: Optional[str]) -> Visitor:
        new_actor = Actor(id=str(uuid.uuid4()), type="visitor")
        self.db.add(new_actor)
        await self.db.flush()

        attempt = 0
        while True:
            new_visitor = Visitor(
                id=str(uuid.uuid4()),
                actor_id=new_actor.id,
                display_id=generate(NANO_ALPHABET, NANO_LENGTH),
                name=name,
                email=email,
            )
            self.db.add(new_visitor)

            try:
                await self.db.flush()
                await self.db.refresh(new_visitor)
                return new_visitor

            except IntegrityError as e:
                await self.db.rollback()
                attempt += 1

                if attempt >= MAX_RETRIES:
                    raise RuntimeError(
                        "Failed to generate unique display_id",
                    ) from e

    async def get_visitor(self, visitor_id: str) -> Optional[Visitor]:
        result = await self.db.execute(
            select(Visitor).where(Visitor.id == visitor_id),
        )
        return result.scalars().first()

    async def list_visitors(self) -> list[Visitor]:
        result = await self.db.execute(select(Visitor))
        return list(result.scalars().all())
