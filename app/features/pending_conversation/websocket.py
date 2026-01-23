from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import get_current_user_id_ws
from app.core.websocket_manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/pending-conversation")
async def admin_pending_conversation_ws(
    websocket: WebSocket,
):
    user_id = await get_current_user_id_ws(websocket)
    if not user_id:
        return None

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
