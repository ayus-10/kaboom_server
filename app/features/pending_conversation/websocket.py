
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.constants import WS_POLICY_VIOLATION
from app.core.security import get_current_user_id_ws
from app.core.websocket_manager import ws_manager

router = APIRouter()

"""
This endpoint is only used to connect an admin to global room.
"""
@router.websocket("/ws/pending-conversation")
async def admin_pending_conversation_ws(websocket: WebSocket):
    await websocket.accept()
    user_id = await get_current_user_id_ws(websocket)
    if not user_id:
        await websocket.close(code=WS_POLICY_VIOLATION)
        return None

    room = "pending_conversation:global"
    await ws_manager.connect(websocket, room)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, room)
