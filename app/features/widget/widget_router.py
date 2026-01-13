from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user_id
from app.features.widget.dependencies import get_widget_service
from app.features.widget.exceptions import WidgetAccessDenied, WidgetNotFound
from app.features.widget.widget_schema import WidgetCreate, WidgetOut, WidgetUpdate
from app.features.widget.widget_service import WidgetService

router = APIRouter()


@router.post("/", response_model=WidgetOut, status_code=status.HTTP_201_CREATED)
async def create_widget(
    data: WidgetCreate,
    user_id: str = Depends(get_current_user_id),
    widget_service: WidgetService = Depends(get_widget_service),
):
    try:
        widget = await widget_service.create_widget(
            project_id=data.project_id,
            user_id=user_id,
            title=data.title,
            description=data.description,
            site_url=data.site_url,
        )

        return widget
    except WidgetAccessDenied:
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
    except WidgetNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")


@router.patch("/{widget_id}", response_model=WidgetOut)
async def update_widget(
    widget_id: str,
    data: WidgetUpdate,
    user_id: str = Depends(get_current_user_id),
    widget_service: WidgetService = Depends(get_widget_service),
):
    try:
        widget = await widget_service.update_widget(
            widget_id=widget_id,
            user_id=user_id,
            new_title=data.title,
            new_description=data.description
        )
        return widget
    except WidgetNotFound:
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
    except WidgetNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")


# @router.get("/", response_model=List[WidgetOut])
# async def list_widgets(
#     user_id: str = Depends(get_current_user_id),
#     widget_service: WidgetService = Depends(get_widget_service),
# ):
#     widgets = await widget_service.get_all_widgets_for_project(user_id)
#     return widgets
