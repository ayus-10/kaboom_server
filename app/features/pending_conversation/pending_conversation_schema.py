from pydantic import BaseModel


class PendingConversationRead(BaseModel):
    id: str
    visitor_id: str

    class Config:
        orm_mode = True
