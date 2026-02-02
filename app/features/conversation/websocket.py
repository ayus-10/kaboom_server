from json import JSONDecodeError

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.constants import WS_POLICY_VIOLATION
from app.core.security import get_current_user_id_ws
from app.core.utils import get_sanitized_bool, get_sanitized_str
from app.core.websocket_manager import ws_manager
from app.features.conversation.dependencies import get_conversation_service
from app.features.conversation.service import ConversationService
from app.features.message.dependencies import get_message_service
from app.features.message.exceptions import MessageAuthorizationError
from app.features.message.service import MessageService

router = APIRouter()

# This endpoint is only used to connect an admin to global room.
@router.websocket("/ws/conversation")
async def admin_conversation_ws(websocket: WebSocket):
    await websocket.accept()
    user_id = await get_current_user_id_ws(websocket)
    if not user_id:
        await websocket.close(code=WS_POLICY_VIOLATION)
        return None

    room = "conversation:global"
    await ws_manager.connect(websocket, room)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, room)


# This endpoint is used to establish direct connection between
# an admin and a visitor, for some conversation_id.
@router.websocket("/ws/conversation/{conversation_id}")
async def conversation_ws(
    websocket: WebSocket,
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
    message_service: MessageService = Depends(get_message_service),
):
    await websocket.accept()

    user_id = await get_current_user_id_ws(websocket)
    visitor_id = websocket.query_params.get("visitor_id")

    if not (bool(user_id) ^ bool(visitor_id)):
        await websocket.close(code=WS_POLICY_VIOLATION)
        return None

    client_id = user_id or visitor_id
    assert client_id is not None

    room = f"conversation:{conversation_id}"
    await ws_manager.connect(websocket, room)

    await conversation_service.broadcast_client_online_status(
        conversation_id=conversation_id,
        client_id=client_id,
        status=True,
    )

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": "Invalid JSON"},
                })
                continue

            message_type = get_sanitized_str(data, "type")

            if message_type == "typing":
                is_typing = get_sanitized_bool(data, "is_typing")
                if is_typing is not None:
                    await conversation_service.broadcast_client_typing_status(
                        conversation_id=conversation_id,
                        client_id=client_id,
                        status=is_typing,
                    )

            if message_type == "send-message":
                try:
                    msg_content = get_sanitized_str(data, "message")
                    if not msg_content:
                        continue

                    new_msg = await message_service.create_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        visitor_id=visitor_id,
                        content=msg_content,
                    )
                    await conversation_service.broadcast_msg_created(new_msg)
                except MessageAuthorizationError:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Not authorized to send message"},
                    })

    except WebSocketDisconnect:
        pass

    finally:
        await ws_manager.disconnect(websocket, room)
        await conversation_service.broadcast_client_online_status(
            conversation_id=conversation_id,
            client_id=client_id,
            status=False,
        )
