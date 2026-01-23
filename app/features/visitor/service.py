import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.actor import Actor
from app.db.visitor import Visitor


class VisitorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_visitor(self, name: Optional[str], email: Optional[str]) -> Visitor:
        new_actor = Actor(id=str(uuid.uuid4()), type="visitor")
        self.db.add(new_actor)
        await self.db.flush()

        new_visitor = Visitor(
            id=str(uuid.uuid4()),
            actor_id=new_actor.id,
            name=name,
            email=email,
        )
        self.db.add(new_visitor)
        await self.db.commit()
        await self.db.refresh(new_visitor)
        return new_visitor

    async def get_visitor(self, visitor_id: str) -> Optional[Visitor]:
        result = await self.db.execute(
            select(Visitor).where(Visitor.id == visitor_id),
        )
        return result.scalars().first()

    async def list_visitors(self) -> list[Visitor]:
        result = await self.db.execute(select(Visitor))
        return list(result.scalars().all())
