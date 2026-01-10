from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.features.auth.auth_service import AuthService
from app.features.auth.google_oauth import (
    exchange_code_for_id_token,
    verify_google_id_token,
)
from app.core.constants import GOOGLE_OAUTH_AUTH_URL
from app.core.config import settings
from app.features.auth.dependencies import get_auth_service
from app.features.auth.exceptions import OAuthExchangeError, TokenVerificationError
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
    code: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        token_data = await exchange_code_for_id_token(code)

        payload = await verify_google_id_token(
            token_data.id_token, token_data.access_token
        )

        return await auth_service.login_with_google(payload)

    except OAuthExchangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code",
        )

    except TokenVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token"
        )

    except (UserServiceError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
