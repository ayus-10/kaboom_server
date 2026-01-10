from typing import TypedDict


class TokenPayload(TypedDict):
    sub: str
    exp: int
