import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import desc, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from app.core.websocket_manager import ws_manager
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
from app.features.conversation.schema import (
    ConversationMessageRead,
    ConversationReadWithLatestMessage,
)
from app.features.visitor.schema import VisitorRead


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
        await self.db.commit()
        await self.db.refresh(new_conversation)

        new_conversation.visitor = visitor

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

        return new_conversation


    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .options(
                selectinload(Conversation.visitor),
            )
            .where(
                Conversation.id == conversation_id,
                Conversation.closed_at.is_(None),
            ),
        )
        return result.scalars().first()

    async def list_conversations(
        self,
        user_id: str,
    ) -> list[ConversationReadWithLatestMessage]:
        latest_message_subq = (
            select(Message)
            .where(Message.conversation_id == Conversation.id)
            .order_by(desc(Message.created_at))
            .limit(1)
            .correlate(Conversation)
            .lateral()
        )

        stmt = (
            select(Conversation)
            .join(latest_message_subq, isouter=True)
            .options(
                contains_eager(Conversation.messages),
                selectinload(Conversation.visitor),
            )
            .where(
                Conversation.user_id == user_id,
                Conversation.closed_at.is_(None),
            )
        )

        result = await self.db.execute(stmt)
        conversation_list_raw = list(result.unique().scalars().all())

        conversation_with_latest_message: list[ConversationReadWithLatestMessage] = []
        for c in conversation_list_raw:
            latest_msg = c.messages[0] if c.messages else None
            conversation_with_latest_message.append(
                ConversationReadWithLatestMessage(
                    id=c.id,
                    created_at=c.created_at,
                    visitor=VisitorRead(
                        id=c.visitor.id,
                        display_id=c.visitor.display_id,
                    ),
                    latest_message=ConversationMessageRead(
                        id=latest_msg.id,
                        content=latest_msg.content,
                        sender_actor_id=latest_msg.sender_actor_id,
                        created_at=latest_msg.created_at,
                    ) if latest_msg else None,
                ),
            )

        return conversation_with_latest_message


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

    async def broadcast_conv_created(self, conv: Conversation):
        await ws_manager.broadcast(
            "conversation:global",
            {
                "type": "conversation.created",
                "payload": {
                    "conversation_id": conv.id,
                    "conversation_visitor_id": conv.visitor.id,
                    "conversation_visitor_display_id": conv.visitor.display_id,
                },
            },
        )

    async def broadcast_conv_closed(self, conv: Conversation):
        await ws_manager.broadcast(
            "conversation:global",
            {
                "type": "conversation.closed",
                "payload": {
                    "conversation_id": conv.id,
                },
            },
        )
