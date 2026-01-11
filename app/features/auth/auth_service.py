import hashlib
import uuid
from datetime import UTC, datetime

from fastapi import Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import REFRESH_TOKEN_EXPIRE_SECONDS
from app.core.tokens import create_access_token, create_refresh_token
from app.db.refresh_token import RefreshToken
from app.features.auth.auth_schema import AuthTokenPair, GooglePayload
from app.features.auth.exceptions import AuthServiceError, InvalidRefreshTokenError
from app.features.users.user_service import UserService


class AuthService:
    def __init__(self, db: AsyncSession, user_service: UserService):
        self.db = db
        self.user_service = user_service

    async def login_with_google(self, google_payload: GooglePayload) -> AuthTokenPair:
        user = await self.user_service.get_or_create_google_user(
            email=google_payload.email,
            first_name=google_payload.given_name,
            last_name=google_payload.family_name,
            avatar_url=google_payload.picture,
        )

        tokens = self._generate_token_pair(str(user.id))
        await self._save_refresh_token(
            user_id=str(user.id),
            refresh_token=tokens.refresh_token,
        )

        return tokens

    async def rotate_auth_tokens(self, user_id: str, refresh_token: str) -> AuthTokenPair:
        try:
            token_hash = self._get_token_hash(refresh_token)

            is_token_valid = await self._verify_refresh_token(
                user_id=user_id,
                token_hash=token_hash,
            )
            if not is_token_valid:
                raise InvalidRefreshTokenError("Refresh token invalid")

        except InvalidRefreshTokenError:
            raise

    async def invalidate_refresh_token(self, user_id: str, refresh_token: str) -> None:
        try:
            token_hash = self._get_token_hash(refresh_token)

            is_token_valid = await self._verify_refresh_token(
                user_id=user_id,
                token_hash=token_hash,
                verify_expiry=False
            )
            if not is_token_valid:
                raise InvalidRefreshTokenError("Refresh token invalid")

            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.refresh_token_hash == token_hash)
                .values(is_revoked=True)
            )
            await self.db.commit()

        except InvalidRefreshTokenError:
            raise

    async def invalidate_all_refresh_tokens(self, user_id: str) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.commit()

    def set_refresh_token_cookie(self, response: Response, refresh_token: str) -> None:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_SECONDS,
            path="/",
        )

    def delete_refresh_token_cookie(self, response: Response) -> None:
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="lax",
            path="/",
        )

    def _generate_token_pair(self, user_id: str) -> AuthTokenPair:
        try:
            token_pair = {
                "access_token": create_access_token(user_id),
                "refresh_token": create_refresh_token(user_id),
            }
            return AuthTokenPair(**token_pair)
        except Exception as e:
            raise AuthServiceError("Error generating tokens") from e

    async def _save_refresh_token(
        self,
        user_id: str,
        refresh_token: str,
        ip_address: str | None = None,
    ) -> None:
        try:
            token_hash = self._get_token_hash(refresh_token)

            new_refresh_token = RefreshToken(
                id=str(uuid.uuid4()),
                user_id=user_id,
                refresh_token_hash=token_hash,
                is_revoked=False,
                ip_address=ip_address,
            )

            self.db.add(new_refresh_token)
            await self.db.commit()

        except Exception as e:
            raise AuthServiceError("Error saving refresh token") from e

    def _get_token_hash(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def _verify_refresh_token(
        self,
        user_id: str,
        token_hash: str,
        verify_expiry: bool = True
    ) -> bool:
        token_obj_query = await self.db.execute(
            select(RefreshToken).where(
                (RefreshToken.refresh_token_hash == token_hash)
                & (RefreshToken.user_id == user_id)
                & (~RefreshToken.is_revoked)
            )
        )
        token_obj = token_obj_query.scalar_one_or_none()

        if not token_obj:
            return False

        is_expired = token_obj.expires_at <= datetime.now(UTC)

        if verify_expiry and is_expired:
            return False

        return True
