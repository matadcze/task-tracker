from datetime import datetime
from typing import List, Optional, Set
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.entities import Task
from src.domain.repositories import TaskRepository
from src.domain.value_objects import TaskPriority, TaskStatus
from src.infrastructure.database.models import TagModel, TaskModel


ALLOWED_SORT_FIELDS: Set[str] = {
    "created_at",
    "updated_at",
    "title",
    "priority",
    "status",
    "due_date",
}


class TaskRepositoryImpl(TaskRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task: Task) -> Task:

        db_task = TaskModel(
            id=task.id,
            owner_id=task.owner_id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

        self.session.add(db_task)
        db_task.tags = []

        if task.tags:
            for tag_name in task.tags:
                result = await self.session.execute(
                    select(TagModel).where(TagModel.name == tag_name)
                )
                tag = result.scalar_one_or_none()
                if not tag:
                    tag = TagModel(name=tag_name)
                    self.session.add(tag)
                db_task.tags.append(tag)

        await self.session.flush()
        await self.session.refresh(db_task, ["tags"])

        return self._to_entity(db_task)

    async def get_by_id(self, task_id: UUID) -> Optional[Task]:

        result = await self.session.execute(
            select(TaskModel).options(joinedload(TaskModel.tags)).where(TaskModel.id == task_id)
        )
        db_task = result.scalars().unique().first()
        return self._to_entity(db_task) if db_task else None

    async def list(
        self,
        owner_id: Optional[UUID] = None,
        search: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        tags: Optional[List[str]] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Task], int]:

        query = select(TaskModel).options(joinedload(TaskModel.tags))

        filters = []

        if owner_id:
            filters.append(TaskModel.owner_id == owner_id)

        if search:
            search_filter = or_(
                TaskModel.title.ilike(f"%{search}%"),
                TaskModel.description.ilike(f"%{search}%"),
            )
            filters.append(search_filter)

        if status:
            filters.append(TaskModel.status == status)

        if priority:
            filters.append(TaskModel.priority == priority)

        if tags:
            query = query.join(TaskModel.tags).where(TagModel.name.in_(tags))

        if due_after:
            filters.append(TaskModel.due_date >= due_after)

        if due_before:
            filters.append(TaskModel.due_date <= due_before)

        if filters:
            query = query.where(and_(*filters))

        count_query = select(func.count()).select_from(TaskModel)
        if filters:
            count_query = count_query.where(and_(*filters))
        if tags:
            count_query = count_query.join(TaskModel.tags).where(TagModel.name.in_(tags))

        result = await self.session.execute(count_query)
        total = result.scalar()

        if sort_by and sort_by in ALLOWED_SORT_FIELDS:
            column = getattr(TaskModel, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(column)
        else:
            query = query.order_by(desc(TaskModel.created_at))

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        db_tasks = result.scalars().unique().all()

        tasks = [self._to_entity(db_task) for db_task in db_tasks]
        return tasks, total

    async def list_due_between(
        self,
        due_after: datetime,
        due_before: datetime,
    ) -> List[Task]:

        query = (
            select(TaskModel)
            .options(joinedload(TaskModel.tags))
            .where(
                TaskModel.due_date.isnot(None),
                TaskModel.due_date >= due_after,
                TaskModel.due_date <= due_before,
                TaskModel.status != TaskStatus.DONE,
            )
        )

        result = await self.session.execute(query)
        db_tasks = result.scalars().unique().all()
        return [self._to_entity(db_task) for db_task in db_tasks]

    async def update(self, task: Task) -> Task:

        result = await self.session.execute(
            select(TaskModel).options(joinedload(TaskModel.tags)).where(TaskModel.id == task.id)
        )
        db_task = result.scalars().unique().first()

        if db_task is None:
            raise ValueError(f"Task {task.id} not found")

        db_task.title = task.title
        db_task.description = task.description
        db_task.status = task.status
        db_task.priority = task.priority
        db_task.due_date = task.due_date
        db_task.updated_at = task.updated_at

        db_task.tags.clear()
        if task.tags:
            for tag_name in task.tags:
                result = await self.session.execute(
                    select(TagModel).where(TagModel.name == tag_name)
                )
                tag = result.scalar_one_or_none()
                if not tag:
                    tag = TagModel(name=tag_name)
                    self.session.add(tag)
                db_task.tags.append(tag)

        await self.session.flush()
        await self.session.refresh(db_task, ["tags"])

        return self._to_entity(db_task)

    async def delete(self, task_id: UUID) -> None:

        result = await self.session.execute(select(TaskModel).where(TaskModel.id == task_id))
        db_task = result.scalar_one_or_none()

        if db_task:
            await self.session.delete(db_task)
            await self.session.flush()

    @staticmethod
    def _to_entity(db_task: TaskModel) -> Task:

        return Task(
            id=db_task.id,
            owner_id=db_task.owner_id,
            title=db_task.title,
            description=db_task.description,
            status=db_task.status,
            priority=db_task.priority,
            due_date=db_task.due_date,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at,
            tags=[tag.name for tag in db_task.tags],
        )
