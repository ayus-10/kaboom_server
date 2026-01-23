from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user_id
from app.features.conversation.dependencies import get_conversation_service
from app.features.conversation.exceptions import (
    ConversationAlreadyExistsError,
    ConversationAuthorizationError,
    ConversationNotFoundError,
    PendingConversationNotFoundError,
)
from app.features.conversation.schema import ConversationCreate, ConversationRead
from app.features.conversation.service import ConversationService

router = APIRouter()

@router.post(
    "",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreate,
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return await conversation_service.create_from_pending(
            pending_conversation_id=payload.pending_conversation_id,
            user_id=user_id,
        )

    except ConversationAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation already exists",
        )

    except PendingConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending Conversation not found",
        )

@router.get(
    "/{conversation_id}",
    response_model=ConversationRead,
    status_code=status.HTTP_200_OK,
)
async def get_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    conversation = await conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation

@router.get(
    "",
    response_model=list[ConversationRead],
    status_code=status.HTTP_200_OK,
)
async def list_conversations(
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: str = Depends(get_current_user_id),
):
    return await conversation_service.list_conversations(user_id)

@router.patch(
    "/{conversation_id}/close",
    response_model=ConversationRead,
    status_code=status.HTTP_200_OK,
)
async def close_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return await conversation_service.close_conversation(conversation_id, user_id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    except ConversationAuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to close the conversation",
        )
