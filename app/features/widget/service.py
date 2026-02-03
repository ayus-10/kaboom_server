from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.project import Project
from app.db.widget import Widget

from app.features.widget.exceptions import WidgetAccessDeniedError, WidgetNotFoundError


class WidgetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_widget(
        self,
        project_id: UUID,
        user_id: str,
        site_url: HttpUrl,
        title: str,
        description: Optional[str],
    ) -> Widget:
        result = await self.db.execute(
            select(Project)
            .where(
                Project.id == str(project_id),
                Project.owner_id == user_id,
                Project.deleted_at.is_(None),
            ),
        )

        project = result.scalar_one_or_none()
        if not project:
            raise WidgetAccessDeniedError()

        widget = Widget(
            id=str(uuid4()),
            project_id=str(project_id),
            title=title,
            description=description,
            site_url=str(site_url),
        )

        self.db.add(widget)
        await self.db.commit()
        await self.db.refresh(widget)
        return widget


    async def get_widget(
        self,
        widget_id: str,
        user_id: str,
    ) -> Optional[Widget]:
        result = await self.db.execute(
            select(Widget)
            .join(Project, Widget.project_id == Project.id)
            .where(
                Widget.id == widget_id,
                Widget.deleted_at.is_(None),
                Project.owner_id == user_id,
                Project.deleted_at.is_(None),
            ),
        )

        widget = result.scalar_one_or_none()

        return widget


    async def get_all_widgets_for_project(
        self,
        user_id: str,
        project_id: UUID,
    ) -> list[Widget]:
        result = await self.db.execute(
            select(Widget)
            .join(Project, Widget.project_id == Project.id)
            .where(
                Widget.project_id == str(project_id),
                Widget.deleted_at.is_(None),
                Project.owner_id == user_id,
                Project.deleted_at.is_(None),
            )
            .order_by(Widget.title),
        )

        return list(result.scalars().all())

    async def update_widget(
        self,
        widget_id: str,
        user_id: str,
        new_title: Optional[str],
        new_description: Optional[str],
    ) -> Widget:
        widget = await self.get_widget(widget_id, user_id)
        if not widget:
            raise WidgetNotFoundError()

        if new_title:
            widget.title = new_title
        widget.description = new_description

        await self.db.commit()
        await self.db.refresh(widget)
        return widget

    async def delete_widget(
        self,
        widget_id: str,
        user_id: str,
    ) -> None:
        widget = await self.get_widget(widget_id, user_id)
        if not widget:
            raise WidgetNotFoundError()

        widget.deleted_at = datetime.now(UTC)
        await self.db.commit()
