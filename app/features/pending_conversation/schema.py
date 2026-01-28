from datetime import datetime
from typing import List, TypedDict

from pydantic import BaseModel

from app.db.pending_conversation import PendingConversation
from app.features.visitor.schema import VisitorRead


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
    created_at: datetime
    pending_messages: List[PendingMessageRead] = []
    visitor: VisitorRead

    class Config:
        from_attributes = True

class CreateOrGetPendingConversationResult(TypedDict):
    pc: PendingConversation
    visitor_display_id: str
