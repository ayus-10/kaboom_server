from json import JSONDecodeError

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.websocket_manager import ws_manager
from app.features.pending_conversation.dependencies import get_pending_conversation_service
from app.features.pending_conversation.exceptions import InvalidVisitorIDError
from app.features.pending_conversation.service import PendingConversationService
from app.features.visitor.dependencies import get_visitor_service
from app.features.visitor.service import VisitorService

router = APIRouter()

"""
This endpoint is used to:
    1. Create a visitor on connection
    2. Create a pending conversation (on event "create"), broadcast to pending_conversation:global
    3. Create a pending message (on event "send-message"), broadcast to pending_conversation:global
"""
@router.websocket("/ws/visitor")
async def visitor_ws(
    websocket: WebSocket,
    visitor_service: VisitorService = Depends(get_visitor_service),
    pc_service: PendingConversationService = Depends(get_pending_conversation_service),
):
    await websocket.accept()

    visitor_id = websocket.query_params.get("visitor_id")

    if not visitor_id:
        # TODO: figure this out
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

    room = f"pending_conversation:{visitor_id}"
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

            message_type = data.get("type")

            if message_type == "create":
                try:
                    pending_conversation = await pc_service.create_or_get_pending_conversation(
                        visitor_id,
                    )

                    await ws_manager.broadcast(
                        "pending_conversation:global",
                        {
                            "type": "pending_conversation.created",
                            "payload": {
                                "pending_conversation_id": pending_conversation.id,
                                "visitor_id": visitor_id,
                            },
                        },
                    )

                    await websocket.send_json({
                        "type": "pending_conversation.created",
                        "payload": {"pending_conversation_id": pending_conversation.id},
                    })

                except InvalidVisitorIDError:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Unable to initiate conversation"},
                    })
            elif message_type == "send-message":
                msg_content = data.get("message")
                if not msg_content:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "No message content"},
                    })
                    continue

                pc = await pc_service.get_pending_conversation(visitor_id=visitor_id)
                if not pc:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "No pending conversation found"},
                    })
                    continue

                pm = await pc_service.send_pending_message(
                    visitor_id=visitor_id,
                    content=msg_content,
                    pc_id=pc.id,
                )

                await ws_manager.broadcast(
                    "pending_conversation:global",
                    {
                        "type": "pending_message.created",
                        "payload": {
                            "pending_conversation_id": pc.id,
                            "pending_message_id": pm.id,
                        },
                    },
                )

                await websocket.send_json({
                    "type": "pending_message.created",
                    "payload": {"pending_message_id": pm.id},
                })
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": f"Unknown message type: {message_type}"},
                })

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, room)
