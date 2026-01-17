from typing import List

from fastapi import APIRouter, Cookie, Depends, HTTPException, status

from app.core.security import get_current_user_id as require_admin_user
from app.features.pending_conversation.dependencies import get_pending_conversation_service
from app.features.pending_conversation.exceptions import InvalidVisitorIDError
from app.features.pending_conversation.pending_conversation_schema import PendingConversationRead
from app.features.pending_conversation.pending_conversation_service import (
    PendingConversationService,
)

router = APIRouter()


@router.post(
    "",
    response_model=PendingConversationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_pending_conversation(
    visitor_id: str | None = Cookie(default=None),
    pc_service: PendingConversationService = Depends(get_pending_conversation_service),
):
    if not visitor_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Visitor ID missing")

    try:
        pc = await pc_service.create_pending_conversation(visitor_id)
        return pc
    except InvalidVisitorIDError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Visitor ID")


@router.get(
    "",
    response_model=List[PendingConversationRead],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin_user)],
)
async def list_pending_conversations(
    pc_service: PendingConversationService = Depends(get_pending_conversation_service),
):
    pcs = await pc_service.list_pending_conversations()
    return pcs


@router.get(
    "/{pc_id}",
    response_model=PendingConversationRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin_user)],
)
async def get_pending_conversation(
    pc_id: str,
    pc_service: PendingConversationService = Depends(get_pending_conversation_service),
):
    pc = await pc_service.get_pending_conversation(pc_id)
    if not pc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending conversation not found"
        )
    return pc
