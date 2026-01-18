from typing import Any, TypedDict

from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str
    exp: int

class WSMessage(TypedDict):
    type: str
    payload: dict[str, Any]
