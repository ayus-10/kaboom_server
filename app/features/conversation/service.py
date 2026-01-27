import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.conversation import Conversation
from app.db.message import Message
from app.db.pending_conversation import PendingConversation
from app.db.visitor import Visitor
from app.features.conversation.exceptions import (
    ConversationAlreadyExistsError,
    ConversationAuthorizationError,
    ConversationNotFoundError,
    ConversationServiceError,
    PendingConversationNotFoundError,
)


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_from_pending(
        self,
        pending_conversation_id: str,
        user_id: str,
    ) -> Conversation:
        result = await self.db.execute(
            select(PendingConversation)
            .where(
                PendingConversation.id == pending_conversation_id,
                PendingConversation.closed_at.is_(None),
            )
            .options(selectinload(PendingConversation.pending_messages)),
        )

        pending_conv = result.scalar_one_or_none()
        if not pending_conv:
            raise PendingConversationNotFoundError()

        if pending_conv.accepted_at is not None:
            raise ConversationAlreadyExistsError()

        pending_conv.accepted_at = datetime.now(UTC)

        visitor = await self.db.get(Visitor, pending_conv.visitor_id)
        if not visitor:
            raise ConversationServiceError()

        new_conversation = Conversation(
            id=str(uuid.uuid4()),
            visitor_id=pending_conv.visitor_id,
            user_id=user_id,
            pending_conversation_id=pending_conv.id,
        )
        self.db.add(new_conversation)

        messages_payload = [
            {
                "id": str(uuid.uuid4()),
                "conversation_id": new_conversation.id,
                "sender_actor_id": visitor.actor_id,
                "content": msg.content,
            }
            for msg in pending_conv.pending_messages
        ]

        if messages_payload:
            await self.db.execute(insert(Message), messages_payload)

        await self.db.commit()
        await self.db.refresh(new_conversation)

        return new_conversation


    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.closed_at.is_(None),
            ),
        )
        return result.scalars().first()

    async def list_conversations(self, user_id: str) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.closed_at.is_(None),
            ),
        )
        return list(result.scalars().all())

    async def close_conversation(self, conversation_id: str, user_id: str) -> Conversation:
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ConversationNotFoundError()

        if conversation.user_id != user_id:
            raise ConversationAuthorizationError()

        conversation.closed_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation
