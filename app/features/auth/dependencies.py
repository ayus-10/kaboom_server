from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.features.auth.service import AuthService
from app.features.user.dependencies import get_user_service
from app.features.user.service import UserService


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(db, user_service)
