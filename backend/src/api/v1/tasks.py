from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.schemas import (
    AttachmentSummary,
    TaskCreate,
    TaskDetailResponse,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from src.domain.exceptions import AuthorizationError, NotFoundError, ValidationError
from src.domain.services import TaskService
from src.domain.value_objects import TaskPriority, TaskStatus
from src.infrastructure.auth.dependencies import get_current_user_id
from src.infrastructure.dependencies import (
    get_attachment_repository,
    get_task_service,
)
from src.infrastructure.repositories import AttachmentRepositoryImpl

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        created_task = await task_service.create_task(
            owner_id=current_user_id,
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            due_date=task_data.due_date,
            tags=task_data.tags,
        )

        return TaskResponse.model_validate(created_task)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[TaskStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    due_before: Optional[datetime] = Query(None, description="Tasks due before this date"),
    due_after: Optional[datetime] = Query(None, description="Tasks due after this date"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else None

        tasks, total = await task_service.list_tasks(
            owner_id=current_user_id,
            search=search,
            status=status_filter,
            priority=priority,
            tags=tag_list,
            due_before=due_before,
            due_after=due_after,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

        return TaskListResponse(
            items=[TaskResponse.model_validate(task) for task in tasks],
            page=page,
            page_size=page_size,
            total=total,
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
    attachment_repo: AttachmentRepositoryImpl = Depends(get_attachment_repository),
):
    try:
        task = await task_service.get_task_by_id(task_id, current_user_id)

        attachments = await attachment_repo.list_by_task(task_id)

        return TaskDetailResponse(
            task=TaskResponse.model_validate(task),
            attachments=[AttachmentSummary.model_validate(att) for att in attachments],
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        updated_task, changes = await task_service.update_task(
            task_id=task_id,
            user_id=current_user_id,
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            due_date=task_data.due_date,
            tags=task_data.tags,
        )

        return TaskResponse.model_validate(updated_task)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        await task_service.delete_task(task_id=task_id, user_id=current_user_id)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
