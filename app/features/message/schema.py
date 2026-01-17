from datetime import datetime

from pydantic import BaseModel


class MessageBase(BaseModel):
    conversation_id: str
    content: str


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: str
    sender_actor_id: str
    created_at: datetime

    class Config:
        from_attributes = True
