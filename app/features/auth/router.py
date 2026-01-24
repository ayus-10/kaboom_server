from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.constants import GOOGLE_OAUTH_AUTH_URL
from app.core.security import get_current_user_id
from app.features.auth.dependencies import get_auth_service
from app.features.auth.exceptions import (
    InvalidRefreshTokenError,
    OAuthExchangeError,
    TokenVerificationError,
)
from app.features.auth.google_oauth import (
    exchange_code_for_id_token,
    verify_google_id_token,
)
from app.features.auth.service import AuthService

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
            token_data.id_token, token_data.access_token,
        )

        result = await auth_service.login_with_google(google_payload=payload)

        auth_service.set_token_cookie(
            response=response,
            refresh_token=result["tokens"].refresh_token,
            access_token=result["tokens"].access_token,
        )

        redirect_url = (
            f"{settings.CLIENT_URL}/oauth/callback#"
            + urlencode({
                "access_token": result["tokens"].access_token,
                "is_new_user": result["is_new"],
            })
        )


        return RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
            headers=response.headers,
        )


    except OAuthExchangeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code",
        )

    except TokenVerificationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token",
        )


@router.post("/rotate")
async def rotate_tokens(
    response: Response,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    refresh_token: Optional[str] = Cookie(None),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token found",
        )

    try:
        tokens = await auth_service.rotate_auth_tokens(
            user_id=user_id,
            refresh_token=refresh_token,
        )

        auth_service.set_token_cookie(
            response=response,
            refresh_token=tokens.refresh_token,
            access_token=tokens.access_token,
        )

        return {"access_token": tokens.access_token}

    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get("/logout")
async def logout(
    response: Response,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    refresh_token: Optional[str] = Cookie(None),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token found",
        )

    try:
        await auth_service.invalidate_refresh_token(user_id, refresh_token)
        auth_service.delete_token_cookie(response)

        return RedirectResponse(settings.CLIENT_URL)
    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get("/logout-all")
async def logout_all(
    response: Response,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.invalidate_all_refresh_tokens(user_id)
    auth_service.delete_token_cookie(response)

    return RedirectResponse(settings.CLIENT_URL)
