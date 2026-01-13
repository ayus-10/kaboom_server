from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user_id
from app.features.project.dependencies import get_project_service
from app.features.project.exceptions import ProjectNotFound
from app.features.project.project_schema import ProjectCreate, ProjectOut, ProjectUpdate
from app.features.project.project_service import ProjectService

router = APIRouter()


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    user_id: str = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service)
):
    project = await service.create_project(
        owner_id=user_id,
        title=data.title,
        description=data.description,
    )
    return project

@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service)
):
    try:
        project = await service.get_project(project_id, user_id)
        return project
    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    user_id: str = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service)
):
    try:
        project = await service.update_project(
            project_id=project_id,
            user_id=user_id,
            new_title=data.title,
            new_description=data.description,
        )
        return project
    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service)
):
    try:
        await service.delete_project(project_id, user_id)
        return None

    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

@router.get("/", response_model=List[ProjectOut])
async def list_projects(
    user_id: str = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service)
):
    projects = await service.get_all_projects(user_id)
    return projects
