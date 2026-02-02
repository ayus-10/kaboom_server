from json import JSONDecodeError
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.constants import WS_POLICY_VIOLATION
from app.core.security import get_current_user_id_ws
from app.core.websocket_manager import ws_manager
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
    conversation_id: UUID,
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

    await ws_manager.broadcast(
        room,
        {
            "type": "conversation.status",
            "payload": {
                "client_id": client_id,
                "status": "online",
            },
        },
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

            message_type = data.get("type")

            if message_type == "typing":
                is_typing = data.get("isTyping")

                if isinstance(is_typing, bool):
                    await ws_manager.broadcast(
                        room,
                        {
                            "type": "conversation.typing",
                            "payload": {
                                "client_id": client_id,
                                "status": is_typing,
                            },
                        },
                    )

            if message_type == "send-message":
                try:
                    msg_content = data.get("message")
                    if not isinstance(msg_content, str) or not msg_content.strip():
                        continue

                    new_msg = await message_service.create_message(
                        conversation_id=str(conversation_id),
                        user_id=user_id,
                        visitor_id=visitor_id,
                        content=msg_content.strip(),
                    )

                    await ws_manager.broadcast(
                        room,
                        {
                            "type": "conversation.message_created",
                            "payload": {
                                "id": new_msg.id,
                                "sender_actor_id": new_msg.sender_actor_id,
                                "content": new_msg.content,
                            },
                        },
                    )
                except MessageAuthorizationError:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Not authorized to send message"},
                    })
                except Exception:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Unable to send message"},
                    })


    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, room)
        await ws_manager.broadcast(
            room,
            {
                "type": "conversation.status",
                "payload": {
                    "client_id": client_id,
                    "status": "offline",
                },
            },
        )
