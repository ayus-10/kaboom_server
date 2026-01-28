from typing import Optional

from pydantic import BaseModel, EmailStr


class VisitorRead(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    display_id: str

    class Config:
        from_attributes = True
