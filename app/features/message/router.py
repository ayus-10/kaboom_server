from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.core.security import get_current_user_id
from app.features.message.dependencies import get_message_service
from app.features.message.exceptions import MessageAuthorizationError
from app.features.message.schema import MessageCreate, MessageRead
from app.features.message.service import MessageService

router = APIRouter()


@router.post(
    "",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    payload: MessageCreate,
    message_service: MessageService = Depends(get_message_service),
    current_user_id: str = Depends(get_current_user_id),
    conversation_id: str = Path(...),
):
    try:
        message = await message_service.create_message(
            conversation_id=conversation_id,
            user_id=current_user_id,
            visitor_id=None,
            content=payload.content,
        )
        return message
    except MessageAuthorizationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")


@router.get(
    "",
    response_model=List[MessageRead],
    status_code=status.HTTP_200_OK,
)
async def list_messages(
    conversation_id: str = Path(...),
    message_service: MessageService = Depends(get_message_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        messages = await message_service.list_messages_by_conversation(
            conversation_id=conversation_id,
            user_id=current_user_id,
        )
        return messages
    except MessageAuthorizationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
