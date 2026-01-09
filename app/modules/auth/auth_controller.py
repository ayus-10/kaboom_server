from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from app.modules.auth.auth_service import AuthService
from app.modules.auth.google_oauth import (
    exchange_code_for_id_token,
    verify_google_id_token,
)
from app.core.constants import GOOGLE_OAUTH_AUTH_URL
from app.core.config import settings
from .exceptions import OAuthExchangeError, TokenVerificationError

router = APIRouter()


@router.get("/google")
async def google_login():
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{GOOGLE_OAUTH_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    auth_service: AuthService = Depends(),
):
    try:
        token_data = await exchange_code_for_id_token(code)

        id_token = token_data["id_token"]
        access_token = token_data["access_token"]

        payload = await verify_google_id_token(id_token, access_token)

        return await auth_service.login_with_google(payload)

    except OAuthExchangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code.",
        )

    except TokenVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token."
        )
