import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.project import Project
from app.db.widget import Widget
from app.features.project.exceptions import ProjectNotFoundError


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(
        self,
        owner_id: str,
        title: str,
        description: Optional[str],
    ) -> Project:
        project = Project(
            id=str(uuid.uuid4()),
            owner_id=owner_id,
            title=title,
            description=description,
        )

        self.db.add(project)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_project(
        self,
        project_id: str,
        user_id: str,
    ) -> Project:
        result = await self.db.execute(
            select(Project)
            .where(
                Project.id == project_id,
                Project.deleted_at.is_(None),
                Project.owner_id == user_id,
            ),
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ProjectNotFoundError()

        return project

    async def get_all_projects(
        self,
        user_id: str,
    ) -> list[Project]:
        result = await self.db.execute(
            select(Project)
            .where(
                Project.owner_id == user_id,
                Project.deleted_at.is_(None),
            )
            .order_by(Project.title),
        )

        return list(result.scalars().all())

    async def update_project(
        self,
        project_id: str,
        user_id: str,
        new_title: Optional[str],
        new_description: Optional[str],
    ) -> Project:
        project = await self.get_project(project_id, user_id)

        if new_title:
            project.title = new_title
        project.description = new_description

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(
        self,
        project_id: str,
        user_id: str,
    ) -> None:
        project = await self.get_project(project_id, user_id)

        now = datetime.now(UTC)

        project.deleted_at = now

        await self.db.execute(
            update(Widget)
            .where(Widget.project_id == project_id)
            .values(deleted_at = now),
        )

        await self.db.commit()
