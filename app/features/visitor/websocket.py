from json import JSONDecodeError

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.utils import get_sanitized_str
from app.core.websocket_manager import ws_manager
from app.features.message.dependencies import get_message_service
from app.features.message.exceptions import MessageAuthorizationError
from app.features.message.service import MessageService
from app.features.pending_conversation.dependencies import get_pending_conversation_service
from app.features.pending_conversation.exceptions import (
    InvalidVisitorIDError,
    PendingMessageAuthorizationError,
)
from app.features.pending_conversation.service import PendingConversationService
from app.features.visitor.dependencies import get_visitor_service
from app.features.visitor.service import VisitorService

router = APIRouter()

# This endpoint is used to:
# 1. Create a visitor on connection
# 2. Create a pending conversation (on event "create")
# 3. Create a pending message (on event "send-pending-message")
# 4. Create a message (on event "send-message")
@router.websocket("/ws/visitor")
async def visitor_ws(
    websocket: WebSocket,
    visitor_service: VisitorService = Depends(get_visitor_service),
    pc_service: PendingConversationService = Depends(get_pending_conversation_service),
    message_service: MessageService = Depends(get_message_service),
):
    await websocket.accept()

    visitor_id = websocket.query_params.get("visitor_id")

    if not visitor_id:
        visitor = await visitor_service.create_visitor(name=None, email=None)
        visitor_id = visitor.id
        await websocket.send_json({
            "type": "visitor.created",
            "payload": {"visitor_id": visitor_id, "visitor_actor_id": visitor.actor_id},
        })
    else:
        visitor = await visitor_service.get_visitor(visitor_id)
        if not visitor:
            await websocket.send_json({
                "type": "error",
                "payload": {"message": "Invalid visitor ID"},
            })
            await websocket.close()
            return
        await websocket.send_json({
            "type": "visitor.found",
            "payload": {"visitor_id": visitor_id, "visitor_actor_id": visitor.actor_id},
        })

    room = f"visitor:{visitor_id}"
    await ws_manager.connect(websocket, room)

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

            if message_type == "create":
                try:
                    pc = await pc_service.create_or_get_pending_conversation(
                        visitor_id,
                    )
                    await pc_service.broadcast_pc_created(pc)
                    await websocket.send_json({
                        "type": "pending_conversation.created",
                        "payload": {
                            "pending_conversation_id": pc.id,
                            "visitor_id": visitor_id,
                            "visitor_display_id": pc.visitor.display_id,
                        },
                    })
                except InvalidVisitorIDError:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Unable to initiate conversation"},
                    })
                    continue

            elif message_type == "send-pending-message":
                msg_content = get_sanitized_str(data, "message")
                if msg_content is None:
                    continue

                pc = await pc_service.get_pending_conversation(visitor_id=visitor_id)
                if not pc:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "No pending conversation found"},
                    })
                    continue

                try:
                    pm = await pc_service.send_pending_message(
                        visitor_id=visitor_id,
                        content=msg_content,
                        pc_id=pc.id,
                    )
                    await pc_service.broadcast_pm_created(pm)
                    await websocket.send_json({
                        "type": "pending_message.created",
                        "payload": {"pending_message_id": pm.id},
                    })
                except PendingMessageAuthorizationError:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Invalid pending conversation ID"},
                    })
                    continue

            elif message_type == "send-message":
                msg_content = get_sanitized_str(data, "message")
                conv_id = get_sanitized_str(data, "conversation_id")

                if msg_content is None or conv_id is None:
                    continue

                try:
                    msg = await message_service.create_message(
                        conversation_id=conv_id,
                        visitor_id=visitor_id,
                        user_id=None,
                        content=msg_content,
                    )
                    await message_service.broadcast_msg_created(msg)
                    await websocket.send_json({
                        "type": "message.created",
                        "payload": {"message_id": msg.id},
                    })
                except MessageAuthorizationError:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Invalid conversation ID"},
                    })
                    continue
            else:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": f"Unknown message type: {message_type}"},
                })

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, room)
