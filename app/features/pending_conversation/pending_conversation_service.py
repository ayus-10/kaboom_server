import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.pending_conversation import PendingConversation
from app.db.visitor import Visitor
from app.features.pending_conversation.exceptions import InvalidVisitorIDError


class PendingConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_pending_conversation(self, visitor_id: str) -> PendingConversation:
        result = await self.db.execute(select(Visitor).where(Visitor.id == visitor_id))
        visitor = result.scalars().first()
        if not visitor:
            raise InvalidVisitorIDError("Visitor not found")

        new_pc = PendingConversation(
            id=str(uuid.uuid4()),
            visitor_id=visitor_id,
        )
        self.db.add(new_pc)
        await self.db.commit()
        await self.db.refresh(new_pc)
        return new_pc

    async def list_pending_conversations(self) -> list[PendingConversation]:
        result = await self.db.execute(select(PendingConversation))
        return list(result.scalars().all())

    async def get_pending_conversation(self, pc_id: str) -> PendingConversation | None:
        result = await self.db.execute(
            select(PendingConversation).where(PendingConversation.id == pc_id)
        )
        return result.scalars().first()
