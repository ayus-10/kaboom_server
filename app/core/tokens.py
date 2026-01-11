from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.core.constants import (
    ACCESS_TOKEN_EXPIRE_SECONDS,
    JWT_ALGORITHM,
    REFRESH_TOKEN_EXPIRE_SECONDS,
)
from app.core.schema import TokenPayload


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(UTC) + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS),
    }
    return jwt.encode(payload, settings.ACCESS_TOKEN_SECRET, JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(UTC) + timedelta(seconds=REFRESH_TOKEN_EXPIRE_SECONDS),
    }
    return jwt.encode(payload, settings.REFRESH_TOKEN_SECRET, JWT_ALGORITHM)


def verify_access_token(token: str) -> TokenPayload:
    payload = jwt.decode(
        token,
        settings.ACCESS_TOKEN_SECRET,
        algorithms=[JWT_ALGORITHM],
    )
    return TokenPayload(**payload)


def verify_refresh_token(token: str) -> TokenPayload:
    payload = jwt.decode(
        token,
        settings.REFRESH_TOKEN_SECRET,
        algorithms=[JWT_ALGORITHM],
    )
    return TokenPayload(**payload)
