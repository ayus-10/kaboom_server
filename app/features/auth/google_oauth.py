import httpx
import logging
from jose import jwt
from app.core.config import settings
from app.core.constants import GOOGLE_OAUTH_TOKEN_URL, GOOGLE_OAUTH_CERTS_URL
from app.features.auth.auth_schema import GooglePayload, GoogleTokenResponse
from app.features.auth.exceptions import OAuthExchangeError, TokenVerificationError


async def exchange_code_for_id_token(code: str) -> GoogleTokenResponse:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                GOOGLE_OAUTH_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            logging.error(f"Error exchanging code for token: {e}", exc_info=True)
            raise OAuthExchangeError("Failed to exchange code for token") from e


async def verify_google_id_token(id_token: str, access_token: str) -> GooglePayload:
    try:
        async with httpx.AsyncClient() as client:
            certs_resp = await client.get(GOOGLE_OAUTH_CERTS_URL, timeout=10.0)
            certs_resp.raise_for_status()
            certs_json = certs_resp.json()

        header = jwt.get_unverified_header(id_token)
        key = next(k for k in certs_json["keys"] if k["kid"] == header["kid"])

        payload = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=settings.GOOGLE_CLIENT_ID,
            access_token=access_token,
        )
        return payload

    except Exception as e:
        logging.error(f"Error verifying ID token: {e}", exc_info=True)
        raise TokenVerificationError("Invalid ID token") from e
