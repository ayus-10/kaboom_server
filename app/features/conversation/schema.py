from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.features.visitor.schema import VisitorRead


class ConversationCreate(BaseModel):
    pending_conversation_id: str


class ConversationRead(BaseModel):
    id: str
    visitor: VisitorRead
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationMessageRead(BaseModel):
    id: str
    sender_actor_id: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationReadWithLatestMessage(ConversationRead):
    latest_message: Optional[ConversationMessageRead]
