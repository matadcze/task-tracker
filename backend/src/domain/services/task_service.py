import time
import inspect
from datetime import datetime, timezone
from src.core.time import utc_now
from typing import List, Optional, Tuple
from uuid import UUID

from ..entities import AuditEvent, Task
from ..exceptions import AuthorizationError, NotFoundError, ValidationError
from ..repositories import AuditEventRepository, TaskRepository
from ..value_objects import EventType, TaskPriority, TaskStatus
from .metrics_provider import MetricsProvider
from .tag_service import TagService


class TaskService:
    @staticmethod
    def _utcnow() -> datetime:
        return utc_now()

    @staticmethod
    def _normalize_datetime(dt: datetime) -> datetime:
        if dt.tzinfo:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.replace(tzinfo=None)

    def __init__(
        self,
        task_repo: TaskRepository,
        audit_repo: AuditEventRepository,
        tag_service: TagService,
        metrics: MetricsProvider,
    ):
        self.task_repo = task_repo
        self.audit_repo = audit_repo
        self.tag_service = tag_service
        self.metrics = metrics

    async def create_task(
        self,
        owner_id: UUID,
        title: str,
        description: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
    ) -> Task:
        start_time = time.time()

        try:
            if not title or not title.strip():
                raise ValueError("Title cannot be empty")

            if len(title) > 500:
                raise ValueError("Title cannot exceed 500 characters")

            normalized_due_date = None
            if due_date:
                normalized_due_date = self._normalize_datetime(due_date)

                if normalized_due_date < self._utcnow():
                    raise ValidationError("Due date cannot be in the past")

            normalized_tags = self.tag_service.ensure_tags_exist(tags)
            if inspect.isawaitable(normalized_tags):
                normalized_tags = await normalized_tags
            normalized_tag_names = [
                tag.name if hasattr(tag, "name") else tag for tag in normalized_tags
            ]

            task = Task(
                owner_id=owner_id,
                title=title.strip(),
                description=description.strip() if description else None,
                status=status or TaskStatus.TODO,
                priority=priority or TaskPriority.MEDIUM,
                due_date=normalized_due_date,
                tags=normalized_tag_names,
            )

            created_task = await self.task_repo.create(task)

            await self.audit_repo.create(
                AuditEvent(
                    user_id=owner_id,
                    event_type=EventType.TASK_CREATED,
                    task_id=created_task.id,
                    details={
                        "title": created_task.title,
                        "status": created_task.status.value,
                        "priority": created_task.priority.value,
                    },
                )
            )

            duration = time.time() - start_time
            self.metrics.track_task_operation("create", "success", duration)
            self.metrics.increment_task_count(created_task.status)
            self.metrics.track_audit_event(EventType.TASK_CREATED.value)

            return created_task

        except (ValidationError, NotFoundError, AuthorizationError, ValueError):
            duration = time.time() - start_time
            self.metrics.track_task_operation("create", "error", duration)
            raise
        except Exception:
            duration = time.time() - start_time
            self.metrics.track_task_operation("create", "error", duration)
            raise

    async def get_task_by_id(self, task_id: UUID, user_id: UUID) -> Task:
        task = await self.task_repo.get_by_id(task_id)

        if not task:
            raise NotFoundError("Task not found")

        if not task.can_be_viewed_by(user_id):
            raise AuthorizationError("Not authorized")

        return task

    async def list_tasks(
        self,
        owner_id: UUID,
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
    ) -> Tuple[List[Task], int]:
        # Validate sort_by to prevent SQL injection
        allowed_sort_fields = {
            "created_at",
            "updated_at",
            "title",
            "priority",
            "status",
            "due_date",
        }
        if sort_by not in allowed_sort_fields:
            raise ValidationError(f"Invalid sort field: {sort_by}")

        # Validate sort_order
        if sort_order not in {"asc", "desc"}:
            raise ValidationError("Sort order must be 'asc' or 'desc'")

        if page < 1:
            raise ValidationError("Page number must be at least 1")

        if page_size < 1 or page_size > 100:
            raise ValidationError("Page size must be between 1 and 100")

        normalized_due_before = None
        normalized_due_after = None

        if due_before:
            normalized_due_before = self._normalize_datetime(due_before)

        if due_after:
            normalized_due_after = self._normalize_datetime(due_after)

        if (
            normalized_due_before
            and normalized_due_after
            and normalized_due_before < normalized_due_after
        ):
            raise ValidationError("due_before must be after due_after")

        normalized_tags = None
        if tags is not None:
            normalized_tags = self.tag_service.normalize_tags(tags)

        tasks, total = await self.task_repo.list(
            owner_id=owner_id,
            search=search,
            status=status,
            priority=priority,
            tags=normalized_tags,
            due_before=normalized_due_before,
            due_after=normalized_due_after,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

        return tasks, total

    async def update_task(
        self,
        task_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
    ) -> tuple[Task, dict]:
        start_time = time.time()

        try:
            task = await self.get_task_by_id(task_id, user_id)

            old_status = task.status

            changes = {}

            if title is not None:
                if not title.strip():
                    raise ValidationError("Task title cannot be empty")
                if len(title) > 500:
                    raise ValidationError("Task title cannot exceed 500 characters")
                if title.strip() != task.title:
                    changes["title"] = {"old": task.title, "new": title.strip()}
                    task.title = title.strip()

            if description is not None:
                normalized_desc = description.strip() if description else None
                if normalized_desc != task.description:
                    changes["description"] = {
                        "old": task.description,
                        "new": normalized_desc,
                    }
                    task.description = normalized_desc

            if status is not None and status != task.status:
                if task.status == TaskStatus.DONE and status != TaskStatus.DONE:
                    raise ValidationError(
                        "Cannot reopen a completed task. Create a new task instead."
                    )

                changes["status"] = {"old": task.status.value, "new": status.value}
                if status == TaskStatus.DONE:
                    task.mark_as_done()
                elif status == TaskStatus.IN_PROGRESS:
                    task.mark_as_in_progress()
                else:
                    task.status = status
                    task.updated_at = self._utcnow()

            if priority is not None and priority != task.priority:
                changes["priority"] = {
                    "old": task.priority.value,
                    "new": priority.value,
                }
                task.priority = priority

            if due_date is not None:
                normalized_due_date = self._normalize_datetime(due_date)

                if status == TaskStatus.IN_PROGRESS and normalized_due_date < self._utcnow():
                    raise ValidationError("Cannot set a past due date for in-progress tasks")

                if normalized_due_date != task.due_date:
                    changes["due_date"] = {
                        "old": task.due_date.isoformat() if task.due_date else None,
                        "new": normalized_due_date.isoformat(),
                    }
                    task.due_date = normalized_due_date

            if tags is not None:
                normalized_tags = self.tag_service.ensure_tags_exist(tags)
                if inspect.isawaitable(normalized_tags):
                    normalized_tags = await normalized_tags
                if normalized_tags != task.tags:
                    changes["tags"] = {"old": task.tags, "new": normalized_tags}
                    task.tags = normalized_tags

            if not changes:
                return task, {}

            task.updated_at = self._utcnow()

            updated_task = await self.task_repo.update(task)

            await self.audit_repo.create(
                AuditEvent(
                    user_id=user_id,
                    event_type=EventType.TASK_UPDATED,
                    task_id=task_id,
                    details={"changes": changes},
                )
            )

            duration = time.time() - start_time
            self.metrics.track_task_operation("update", "success", duration)
            self.metrics.track_audit_event(EventType.TASK_UPDATED.value)

            if status is not None and old_status != status:
                self.metrics.decrement_task_count(old_status)
                self.metrics.increment_task_count(status)

            return updated_task, changes

        except (ValidationError, NotFoundError, AuthorizationError):
            duration = time.time() - start_time
            self.metrics.track_task_operation("update", "error", duration)
            raise
        except Exception:
            duration = time.time() - start_time
            self.metrics.track_task_operation("update", "error", duration)
            raise

    async def delete_task(self, task_id: UUID, user_id: UUID) -> None:
        start_time = time.time()

        try:
            task = await self.get_task_by_id(task_id, user_id)

            task_status = task.status

            await self.audit_repo.create(
                AuditEvent(
                    user_id=user_id,
                    event_type=EventType.TASK_DELETED,
                    task_id=task_id,
                    details={"title": task.title, "status": task.status.value},
                )
            )

            await self.task_repo.delete(task_id)

            duration = time.time() - start_time
            self.metrics.track_task_operation("delete", "success", duration)
            self.metrics.decrement_task_count(task_status)
            self.metrics.track_audit_event(EventType.TASK_DELETED.value)

        except (NotFoundError, AuthorizationError):
            duration = time.time() - start_time
            self.metrics.track_task_operation("delete", "error", duration)
            raise
        except Exception:
            duration = time.time() - start_time
            self.metrics.track_task_operation("delete", "error", duration)
            raise

    async def delete_tasks_for_owner(self, owner_id: UUID) -> None:
        await self.task_repo.delete_by_owner(owner_id)
