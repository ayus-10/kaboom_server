from typing import Optional

from pydantic import BaseModel, EmailStr


class VisitorCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class VisitorRead(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    class Config:
        from_attributes = True
