import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.conversation import Conversation
from app.db.message import Message
from app.features.message.exceptions import MessageAuthorizationError


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
        self,
        conversation_id: str,
        sender_actor_id: str,
        content: str,
    ) -> Message:
        has_access = await self._verify_conversation_access(conversation_id, sender_actor_id)

        if not has_access:
            raise MessageAuthorizationError()

        new_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
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
        actor_id: str,
    ) -> list[Message]:
        has_access = await self._verify_conversation_access(conversation_id, actor_id)

        if not has_access:
            raise MessageAuthorizationError()

        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at),
        )
        return list(result.scalars().all())

    async def _verify_conversation_access(self, conversation_id: str, actor_id: str) -> bool:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                ((Conversation.user_id == actor_id) | (Conversation.visitor_id == actor_id)),
            ),
        )
        conversation = result.scalar_one_or_none()
        return conversation is not None
