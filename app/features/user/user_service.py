import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.actor import Actor
from app.db.user import User
from app.features.user.exceptions import (
    UserNotFoundError,
    UserServiceError,
)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_me(self, user_id: str) -> User:
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            if not user:
                raise UserNotFoundError("User not found")
            return user
        except Exception as e:
            raise UserServiceError("Error while getting user") from e

    async def get_or_create_google_user(
        self,
        email: str,
        first_name: str | None,
        last_name: str | None,
        avatar_url: str | None,
    ) -> User:
        try:
            result = await self.db.execute(select(User).where(User.email == email))
            user = result.scalars().first()

            if user:
                return user

            new_actor = Actor(
                id=str(uuid.uuid4()),
                type="user",
            )
            self.db.add(new_actor)
            await self.db.flush()

            new_user = User(
                id=str(uuid.uuid4()),
                email=email,
                first_name=first_name,
                last_name=last_name,
                avatar_url=avatar_url,
                actor_id=new_actor.id,
            )

            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)

            return new_user

        except Exception as e:
            raise UserServiceError("Error while creating user") from e
