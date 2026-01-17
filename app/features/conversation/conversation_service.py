import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.conversation import Conversation
from app.db.pending_conversation import PendingConversation
from app.features.conversation.exceptions import ConversationServiceError


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_from_pending(
        self,
        pending_conversation_id: str,
        user_id: str,
    ) -> Conversation:
        result = await self.db.execute(
            select(PendingConversation).where(
                PendingConversation.id == pending_conversation_id
            )
        )
        pending = result.scalars().first()

        if not pending:
            raise ConversationServiceError("Pending conversation not found")

        result = await self.db.execute(
            select(Conversation).where(
                Conversation.pending_conversation_id == pending_conversation_id
            )
        )
        if result.scalars().first():
            raise ConversationServiceError("Conversation already created")

        new_conversation = Conversation(
            id=str(uuid.uuid4()),
            visitor_id=pending.visitor_id,
            user_id=user_id,
            pending_conversation_id=pending.id,
        )

        self.db.add(new_conversation)
        await self.db.commit()
        await self.db.refresh(new_conversation)
        return new_conversation

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.closed_at.is_(None),
            )
        )
        return result.scalars().first()

    async def list_conversations(self, user_id: str) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.closed_at.is_(None)
            )
        )
        return list(result.scalars().all())

    async def close_conversation(self, conversation_id: str) -> Conversation:
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ConversationServiceError("Conversation not found")

        conversation.closed_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation
