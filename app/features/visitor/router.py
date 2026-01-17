from typing import List

from fastapi import APIRouter, Depends, status

from app.core.security import get_current_user_id as require_admin_user
from app.features.visitor.dependencies import get_visitor_service
from app.features.visitor.schema import VisitorRead
from app.features.visitor.service import VisitorService

router = APIRouter()


@router.get(
    "",
    response_model=List[VisitorRead],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin_user)],
)
async def list_visitors(visitor_service: VisitorService = Depends(get_visitor_service)):
    visitors = await visitor_service.list_visitors()
    return visitors
