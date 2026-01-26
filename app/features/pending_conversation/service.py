import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.pending_conversation import PendingConversation
from app.db.pending_message import PendingMessage
from app.db.visitor import Visitor
from app.features.pending_conversation.exceptions import (
    InvalidVisitorIDError,
    PendingConversationServiceError,
)
from app.features.visitor.service import VisitorService


class PendingConversationService:
    def __init__(self, db: AsyncSession, visitor_service: VisitorService):
        self.db = db
        self.visitor_service  = visitor_service

    async def create_or_get_pending_conversation(self, visitor_id: str) -> PendingConversation:
        result = await self.db.execute(select(Visitor).where(Visitor.id == visitor_id))
        visitor = result.scalars().first()
        if not visitor:
            raise InvalidVisitorIDError()

        result = await self.db.execute(
            select(PendingConversation)
            .where(PendingConversation.visitor_id == visitor_id)
            .where(PendingConversation.closed_at.is_(None)),
        )
        existing_pc = result.scalars().first()
        if existing_pc:
            return existing_pc

        new_pc = PendingConversation(
            id=str(uuid.uuid4()),
            visitor_id=visitor_id,
        )
        self.db.add(new_pc)
        await self.db.commit()
        await self.db.refresh(new_pc)
        return new_pc

    async def list_pending_conversations(self) -> list[PendingConversation]:
        result = await self.db.execute(
            select(PendingConversation).where(PendingConversation.closed_at.is_(None)),
        )
        return list(result.scalars().all())

    async def get_pending_conversation(
        self,
        pc_id: Optional[str] = None,
        visitor_id: Optional[str] = None,
    ) -> Optional[PendingConversation]:
        if pc_id is None and visitor_id is None:
            return None

        stmt = select(PendingConversation).where(
            PendingConversation.closed_at.is_(None),
        )

        if pc_id is not None:
            stmt = stmt.where(PendingConversation.id == pc_id)

        if visitor_id is not None:
            stmt = stmt.where(PendingConversation.visitor_id == visitor_id)

        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def close_pending_conversation(self, pc_id: str) -> PendingConversation:
        pc = await self.get_pending_conversation(pc_id=pc_id)
        if not pc:
            raise PendingConversationServiceError()

        pc.closed_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(pc)
        return pc

    async def send_pending_message(
        self,
        pc_id: str,
        visitor_id: str,
        content: str,
    ) -> PendingMessage:
        pc = await self.get_pending_conversation(pc_id=pc_id)
        if not pc:
            raise PendingConversationServiceError()

        visitor = await self.visitor_service.get_visitor(visitor_id)
        if not visitor:
            raise PendingConversationServiceError()

        new_pm = PendingMessage(
            id=str(uuid.uuid4()),
            pending_conversation_id=pc.id,
            sender_visitor_id=visitor.id,
            content=content,
        )
        self.db.add(new_pm)
        await self.db.commit()
        await self.db.refresh(new_pm)
        return new_pm
