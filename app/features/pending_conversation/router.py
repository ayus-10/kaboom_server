from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user_id as require_admin_user
from app.core.websocket_manager import ws_manager
from app.features.pending_conversation.dependencies import get_pending_conversation_service
from app.features.pending_conversation.exceptions import PendingConversationServiceError
from app.features.pending_conversation.schema import (
    PendingConversationRead,
    PendingConversationReadWithMessages,
)
from app.features.pending_conversation.service import (
    PendingConversationService,
)

router = APIRouter()

@router.get(
    "",
    response_model=List[PendingConversationReadWithMessages],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin_user)],
)
async def list_pending_conversations(
    pc_service: PendingConversationService = Depends(get_pending_conversation_service),
):
    pcs = await pc_service.list_pending_conversations()
    return pcs


@router.post(
    "/{pc_id}/close",
    response_model=PendingConversationRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin_user)],
)
async def close_pending_conversation(
    pc_id: str,
    pc_service: PendingConversationService = Depends(get_pending_conversation_service),
):
    try:
        pc = await pc_service.close_pending_conversation(pc_id)

        await ws_manager.broadcast(
            "pending_conversation:global",
            {
                "type": "pending_conversation.closed",
                "payload": {
                    "pending_conversation_id": pc.id,
                },
            },
        )

        return pc
    except PendingConversationServiceError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending conversation not found",
        )
