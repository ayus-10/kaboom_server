from pydantic import BaseModel


class VisitorRead(BaseModel):
    id: str
    display_id: str

    class Config:
        from_attributes = True
