from datetime import datetime
from typing import List

from pydantic import BaseModel


class PendingConversationRead(BaseModel):
    id: str
    visitor_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class PendingMessageRead(BaseModel):
    id: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class PendingConversationReadWithMessages(BaseModel):
    id: str
    visitor_id: str
    created_at: datetime
    pending_messages: List[PendingMessageRead] = []

    class Config:
        from_attributes = True
