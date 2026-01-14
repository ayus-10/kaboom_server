from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user_id
from app.features.user.dependencies import get_user_service
from app.features.user.exceptions import UserServiceError
from app.features.user.user_service import UserService

router = APIRouter()


@router.get("/me")
async def get_me(
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    try:
        user = await user_service.get_me(user_id)

        return {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "avatar_url": user.avatar_url,
        }
    except UserServiceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in to continue",
        )
