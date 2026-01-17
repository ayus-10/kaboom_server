from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class WidgetCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    site_url: HttpUrl

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()

class WidgetUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    site_url: HttpUrl

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v

class WidgetOut(BaseModel):
    id: str
    project_id: str
    slug: str
    title: str
    description: Optional[str] = None
    site_url: HttpUrl

    class Config:
        from_attributes = True
