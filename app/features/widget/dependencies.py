from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.features.widget.service import WidgetService


def get_widget_service(db: AsyncSession = Depends(get_db)) -> WidgetService:
    return WidgetService(db)
