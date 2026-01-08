from fastapi import APIRouter, Depends
from app.modules.users.service import UsersService
from app.modules.users.schemas import User

router = APIRouter()

@router.get("/", response_model=list[User])
def get_users(service: UsersService = Depends()):
    return service.get_all_users()
