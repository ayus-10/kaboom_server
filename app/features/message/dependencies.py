from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.features.message.service import MessageService


def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    return MessageService(db)
