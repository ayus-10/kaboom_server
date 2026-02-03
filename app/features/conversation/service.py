import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import desc, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
            widget_id=pending_conv.widget_id,
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
            select(
                Message.conversation_id,
                Message.id.label("latest_message_id"),
                Message.content.label("latest_message_content"),
                Message.sender_actor_id.label("latest_message_sender_actor_id"),
                Message.created_at.label("latest_message_created_at"),
            )
            .where(Message.conversation_id == Conversation.id)
            .order_by(desc(Message.created_at))
            .limit(1)
            .correlate(Conversation)
            .lateral()
        )

        stmt = (
            select(
                Conversation,
                latest_message_subq.c.latest_message_id,
                latest_message_subq.c.latest_message_content,
                latest_message_subq.c.latest_message_sender_actor_id,
                latest_message_subq.c.latest_message_created_at,
            )
            .where(
                Conversation.user_id == user_id,
                Conversation.closed_at.is_(None),
            )
            .join(latest_message_subq, isouter=True)
            .options(selectinload(Conversation.visitor))
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        conversation_with_latest_message: list[ConversationReadWithLatestMessage] = []
        for conv, msg_id, msg_content, msg_sender, msg_created_at in rows:
            conversation_with_latest_message.append(
                ConversationReadWithLatestMessage(
                    id=conv.id,
                    created_at=conv.created_at,
                    visitor=VisitorRead(
                        id=conv.visitor.id,
                        display_id=conv.visitor.display_id,
                    ),
                    latest_message=ConversationMessageRead(
                        id=msg_id,
                        content=msg_content,
                        sender_actor_id=msg_sender,
                        created_at=msg_created_at,
                    ) if msg_id else None,
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

    async def broadcast_conv_created(self, conv: Conversation) -> None:
        await ws_manager.broadcast(
            f"visitor:{conv.visitor_id}",
            {
                "type": "conversation.created",
                "payload": {
                    "conversation_id": conv.id,
                },
            },
        )
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

    async def broadcast_conv_closed(self, conv: Conversation) -> None:
        await ws_manager.broadcast(
            "conversation:global",
            {
                "type": "conversation.closed",
                "payload": {
                    "conversation_id": conv.id,
                },
            },
        )

    async def broadcast_client_online_status(
        self,
        conversation_id: str,
        client_id: str,
        status: bool,
    ) -> None:
        await ws_manager.broadcast(
            f"conversation:{conversation_id}",
            {
                "type": "conversation.status",
                "payload": {
                    "client_id": client_id,
                    "status": "online" if status else "offline",
                },
            },
        )

    async def broadcast_client_typing_status(
        self,
        conversation_id: str,
        client_id: str,
        status: bool,
    ) -> None:
        await ws_manager.broadcast(
            f"conversation:{conversation_id}",
            {
                "type": "conversation.typing",
                "payload": {
                    "client_id": client_id,
                    "status": status,
                },
            },
        )
