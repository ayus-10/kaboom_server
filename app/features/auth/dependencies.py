from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.features.auth.auth_service import AuthService
from app.features.user.user_service import UserService


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(db, user_service)
