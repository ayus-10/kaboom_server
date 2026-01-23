from typing import Optional

from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.tokens import verify_access_token

POLICY_VIOLATION = 1008

security = HTTPBearer()

async def get_current_user_id_ws(websocket: WebSocket) -> Optional[str]:
    token = websocket.cookies.get("access_token")

    if not token:
        await websocket.close(code=POLICY_VIOLATION)
        return None

    user = verify_access_token(token)
    if not user:
        await websocket.close(code=POLICY_VIOLATION)
        return None

    return user.sub


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    try:
        payload = verify_access_token(token)
        user_id = payload.sub
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )
        return user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
