from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.websocket_manager import ConnectionManager
from app.features.pending_conversation.dependencies import get_pending_conversation_service
from app.features.pending_conversation.exceptions import InvalidVisitorIDError
from app.features.pending_conversation.service import PendingConversationService

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/pending-conversation")
async def admin_pending_conversation_ws(
    websocket: WebSocket,
):
    await manager.connect(websocket, "pending_conversation:global")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket, "pending_conversation:global")


@router.websocket("/ws/pending-conversation/{visitor_id}")
async def visitor_pending_conversation_ws(
    websocket: WebSocket,
    visitor_id: str,
    pc_service: PendingConversationService = Depends(get_pending_conversation_service),
):
    room = f"pending_conversation:{visitor_id}"
    await manager.connect(websocket, room)

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "create":
                try:
                    pending_conversation = await pc_service.create_pending_conversation(
                        visitor_id
                    )

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

                except InvalidVisitorIDError as e:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "payload": {
                                "message": str(e),
                            },
                        }
                    )

    except WebSocketDisconnect:
        await manager.disconnect(websocket, room)
