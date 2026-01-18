from typing import Optional

from pydantic import BaseModel, EmailStr


class UserRead(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: Optional[str]
