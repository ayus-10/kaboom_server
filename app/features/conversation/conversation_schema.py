from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ConversationRead(BaseModel):
    id: str
    visitor_id: str
    user_id: Optional[str]
    created_at: datetime
    deleted_at: datetime | None

    class Config:
        from_attributes = True
