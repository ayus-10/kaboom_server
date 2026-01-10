from app.core.tokens import (
    create_access_token,
    create_refresh_token,
)
from app.features.auth.auth_schema import GooglePayload
from app.features.users.user_service import UserService


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def login_with_google(self, google_payload: GooglePayload):
        user = await self.user_service.get_or_create_google_user(
            email=google_payload.email,
            first_name=google_payload.given_name,
            last_name=google_payload.family_name,
            avatar_url=google_payload.picture,
        )

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def invalidate_all_refresh_tokens(self, user_id: str):
        await self.user_service.invalidate_all_refresh_tokens(user_id)

    def set_refresh_token_cookie(self, response: Response, refresh_token: str):
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
            path="/",
        )
