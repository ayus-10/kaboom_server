from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.core.security import get_current_user_id
from app.features.widget.dependencies import get_widget_service
from app.features.widget.exceptions import WidgetAccessDeniedError, WidgetNotFoundError
from app.features.widget.schema import WidgetCreate, WidgetOut, WidgetUpdate
from app.features.widget.service import WidgetService

router = APIRouter()


@router.post("/", response_model=WidgetOut, status_code=status.HTTP_201_CREATED)
async def create_widget(
    payload: WidgetCreate,
    project_id: UUID = Path(...),
    user_id: str = Depends(get_current_user_id),
    widget_service: WidgetService = Depends(get_widget_service),
):
    try:
        widget = await widget_service.create_widget(
            project_id=project_id,
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            site_url=payload.site_url,
        )

        return widget
    except WidgetAccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get("/{widget_id}", response_model=WidgetOut)
async def get_widget(
    widget_id: str,
    user_id: str = Depends(get_current_user_id),
    widget_service: WidgetService = Depends(get_widget_service),
):
    try:
        widget = await widget_service.get_widget(widget_id, user_id)
        return widget
    except WidgetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")


@router.patch("/{widget_id}", response_model=WidgetOut)
async def update_widget(
    widget_id: str,
    payload: WidgetUpdate,
    user_id: str = Depends(get_current_user_id),
    widget_service: WidgetService = Depends(get_widget_service),
):
    try:
        widget = await widget_service.update_widget(
            widget_id=widget_id,
            user_id=user_id,
            new_title=payload.title,
            new_description=payload.description,
        )
        return widget
    except WidgetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")


@router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    widget_id: str,
    user_id: str = Depends(get_current_user_id),
    widget_service: WidgetService = Depends(get_widget_service),
):
    try:
        await widget_service.delete_widget(widget_id, user_id)
        return None
    except WidgetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")


@router.get("/", response_model=List[WidgetOut])
async def get_widgets(
    user_id: str = Depends(get_current_user_id),
    widget_service: WidgetService = Depends(get_widget_service),
    project_id: UUID = Path(...),
):
    widgets = await widget_service.get_all_widgets_for_project(user_id, project_id)
    return widgets
