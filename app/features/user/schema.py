from typing import Optional, TypedDict

from pydantic import BaseModel, EmailStr

from app.db.user import User


class UserRead(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: Optional[str]
    user_actor_id:str

class UserWithStatus(TypedDict):
    user: User
    is_new: bool
