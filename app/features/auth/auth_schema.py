from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Optional


class AuthTokenPair(BaseModel):
    refresh_token: str
    access_token: str


class GooglePayload(BaseModel):
    iss: str
    azp: str
    aud: str
    sub: str
    email: EmailStr
    email_verified: bool
    at_hash: Optional[str]
    name: Optional[str]
    picture: Optional[HttpUrl]
    given_name: Optional[str]
    family_name: Optional[str]
    iat: int
    exp: int


class GoogleTokenResponse(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str
    scope: str
    token_type: str
    id_token: str
