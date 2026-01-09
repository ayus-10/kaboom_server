from app.core.tokens import (
    create_access_token,
    create_refresh_token,
)

# from app.modules.users.user_service import UserService


class AuthService:
    # def __init__(self, user_service: UserService):
    #     self.user_service = user_service

    async def login_with_google(self, google_payload: dict):
        # user = await self.user_service.get_or_create_google_user(
        #     google_id=google_payload["sub"],
        #     email=google_payload["email"],
        #     name=google_payload.get("name"),
        #     avatar=google_payload.get("picture"),
        # )

        return {
            "access_token": create_access_token(str(google_payload["sub"])),
            "refresh_token": create_refresh_token(str(google_payload["sub"])),
        }
