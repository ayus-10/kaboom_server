from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.features.pending_conversation.service import (
    PendingConversationService,
)


def get_pending_conversation_service(
    db: AsyncSession = Depends(get_db)
) -> PendingConversationService:
    return PendingConversationService(db)
