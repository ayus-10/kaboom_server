from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.constants import WS_POLICY_VIOLATION
from app.core.security import get_current_user_id_ws
from app.core.websocket_manager import ws_manager

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
async def conversation_ws(websocket: WebSocket, conversation_id: UUID):
    await websocket.accept()

    user_id = await get_current_user_id_ws(websocket)
    visitor_id = websocket.query_params.get("visitor_id")

    if not (bool(user_id) ^ bool(visitor_id)):
        await websocket.close(code=WS_POLICY_VIOLATION)
        return None

    room = f"conversation:{conversation_id}"
    await ws_manager.connect(websocket, room)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, room)
