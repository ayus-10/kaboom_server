from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    pending_conversation_id: str


class ConversationRead(BaseModel):
    id: str
    visitor_id: str
    user_id: str
    created_at: datetime
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True
