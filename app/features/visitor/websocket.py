from json import JSONDecodeError

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.websocket_manager import ConnectionManager
from app.features.pending_conversation.dependencies import get_pending_conversation_service
from app.features.pending_conversation.exceptions import (
    ExistingPendingConversationError,
    InvalidVisitorIDError,
)
from app.features.pending_conversation.service import PendingConversationService
from app.features.visitor.dependencies import get_visitor_service
from app.features.visitor.service import VisitorService

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/visitor")
async def visitor_ws(
    websocket: WebSocket,
    visitor_service: VisitorService = Depends(get_visitor_service),
    pc_service: PendingConversationService = Depends(get_pending_conversation_service),
):
    await websocket.accept()

    # Get or create visitor
    visitor_id = websocket.query_params.get("visitor_id")

    if not visitor_id:
        # TODO: figure this out
        visitor = await visitor_service.create_visitor(name=None, email=None)
        visitor_id = visitor.id
        await websocket.send_json({
            "type": "visitor.created",
            "payload": {"visitor_id": visitor_id},
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

    room = f"pending_conversation:{visitor_id}"
    await manager.connect(websocket, room)

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
                    # Check for existing pending conversation
                    existing = await pc_service.get_pending_conversation(visitor_id)
                    if existing:
                        await websocket.send_json({
                            "type": "pending_conversation.exists",
                            "payload": {"pending_conversation_id": existing.id},
                        })
                        continue

                    pending_conversation = await pc_service.create_pending_conversation(visitor_id)

                    # Broadcast to admins
                    await manager.broadcast(
                        "pending_conversation:global",
                        {
                            "type": "pending_conversation.created",
                            "payload": {
                                "pending_conversation_id": pending_conversation.id,
                                "visitor_id": visitor_id,
                            },
                        },
                    )

                    # Notify visitor
                    await websocket.send_json({
                        "type": "pending_conversation.created",
                        "payload": {"pending_conversation_id": pending_conversation.id},
                    })

                except ExistingPendingConversationError:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Unable to re-initiate conversation"},
                    })

                except InvalidVisitorIDError:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Unable to initiate conversation"},
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
        await manager.disconnect(websocket, room)
