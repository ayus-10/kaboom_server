from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.websocket_manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/pending-conversation")
async def admin_pending_conversation_ws(
    websocket: WebSocket,
):
    room = "pending_conversation:global"
    await websocket.accept()
    await manager.connect(websocket, room)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, room)
