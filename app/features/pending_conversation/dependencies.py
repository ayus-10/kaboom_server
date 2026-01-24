from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.features.pending_conversation.service import (
    PendingConversationService,
)
from app.features.visitor.dependencies import get_visitor_service
from app.features.visitor.service import VisitorService


def get_pending_conversation_service(
    db: AsyncSession = Depends(get_db),
    visitor_service: VisitorService = Depends(get_visitor_service),
) -> PendingConversationService:
    return PendingConversationService(db, visitor_service)
