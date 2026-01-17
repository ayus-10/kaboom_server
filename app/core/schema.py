from typing import Any, Literal, TypedDict
from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str
    exp: int

class WSMessage(TypedDict):
    type: Literal[
        "pending_conversation.created",
        "pending_conversation.taken_over",
        "conversation.closed",
        "message.received",
        "conversation.typing",
    ]
    payload: dict[str, Any]
