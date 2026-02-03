import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket_manager import ws_manager
from app.db.conversation import Conversation
from app.db.message import Message
from app.db.user import User
from app.db.visitor import Visitor
from app.features.message.exceptions import MessageAuthorizationError


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
        self,
        conversation_id: str,
        user_id: Optional[str],
        visitor_id: Optional[str],
        content: str,
    ) -> Message:
        conversation = await self._get_self_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            visitor_id=visitor_id,
        )

        if conversation is None:
            raise MessageAuthorizationError()

        sender_actor_id = await self._get_self_actor_id(
            user_id=user_id,
            visitor_id=visitor_id,
        )

        new_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            sender_actor_id=sender_actor_id,
            content=content,
        )
        self.db.add(new_message)
        await self.db.commit()
        await self.db.refresh(new_message)

        return new_message

    async def list_messages_by_conversation(
        self,
        conversation_id: str,
        user_id: str,
    ) -> list[Message]:
        conversation = await self._get_self_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            visitor_id=None,
        )

        if conversation is None:
            raise MessageAuthorizationError()

        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at),
        )
        return list(result.scalars().all())

    async def _get_self_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str],
        visitor_id: Optional[str],
    ) -> Optional[Conversation]:
        if user_id is None and visitor_id is None:
            return None

        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.closed_at.is_(None),
        )

        if user_id:
            stmt = stmt.where(Conversation.user_id == user_id)
        else:
            stmt = stmt.where(Conversation.visitor_id == visitor_id)

        result = await self.db.execute(stmt)
        conversation = result.scalars().one_or_none()
        return conversation

    async def _get_self_actor_id(
        self,
        user_id: Optional[str],
        visitor_id: Optional[str],
    ) -> Optional[str]:
        if not (user_id or visitor_id):
            return None

        if user_id:
            user = await self.db.get(User, user_id)
            return user.actor_id if user else None

        visitor = await self.db.get(Visitor, visitor_id)
        return visitor.actor_id if visitor else None



    async def broadcast_msg_created(self, msg: Message) -> None:
        await ws_manager.broadcast(
            f"conversation:{msg.conversation_id}",
            {
                "type": "conversation.message_created",
                "payload": {
                    "message_id": msg.id,
                    "message_sender_actor_id": msg.sender_actor_id,
                    "message_content": msg.content,
                },
            },
        )
