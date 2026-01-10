from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.constants import GOOGLE_OAUTH_AUTH_URL
from app.core.security import get_current_user_id
from app.features.auth.auth_service import AuthService
from app.features.auth.dependencies import get_auth_service
from app.features.auth.exceptions import (
    AuthServiceError,
    InvalidRefreshTokenError,
    OAuthExchangeError,
    TokenVerificationError,
)
from app.features.auth.google_oauth import (
    exchange_code_for_id_token,
    verify_google_id_token,
)
from app.features.users.exceptions import UserServiceError

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
    response: Response,
    code: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        token_data = await exchange_code_for_id_token(code)

        payload = await verify_google_id_token(
            token_data.id_token, token_data.access_token
        )

        tokens = await auth_service.login_with_google(google_payload=payload)

        auth_service.set_refresh_token_cookie(response, tokens["refresh_token"])

        return {"access_token": tokens["access_token"]}

    except OAuthExchangeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code",
        )

    except TokenVerificationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token"
        )

    except (UserServiceError, AuthServiceError, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/logout")
async def logout(
    response: Response,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    refresh_token: str | None = Cookie(None),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token found",
        )

    try:
        await auth_service.invalidate_refresh_token(user_id, refresh_token)
        auth_service.delete_refresh_token_cookie(response)

        return {"detail": "Logged out successfully"}

    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token",
        )

    except (AuthServiceError, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/logout-all")
async def logout_all(
    response: Response,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        await auth_service.invalidate_all_refresh_tokens(user_id)
        auth_service.delete_refresh_token_cookie(response)

        return {"detail": "Logged out from all devices"}

    except (AuthServiceError, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
