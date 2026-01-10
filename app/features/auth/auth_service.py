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

        return {
            "access_token": create_access_token(str(user.id)),
            "refresh_token": create_refresh_token(str(user.id)),
        }
