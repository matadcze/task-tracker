from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from .entities import (
    Attachment,
    AuditEvent,
    RefreshToken,
    ReminderLog,
    Tag,
    Task,
    User,
)
from .value_objects import EventType, ReminderType, TaskPriority, TaskStatus


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        pass


class TaskRepository(ABC):
    @abstractmethod
    async def create(self, task: Task) -> Task:
        pass

    @abstractmethod
    async def get_by_id(self, task_id: UUID) -> Optional[Task]:
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def list_due_between(
        self,
        due_after: datetime,
        due_before: datetime,
    ) -> List[Task]:
        """Return tasks due between two timestamps (inclusive)."""
        pass

    @abstractmethod
    async def update(self, task: Task) -> Task:
        pass

    @abstractmethod
    async def delete(self, task_id: UUID) -> None:
        pass


class TagRepository(ABC):
    @abstractmethod
    async def get_or_create(self, name: str) -> Tag:
        pass

    @abstractmethod
    async def get_by_names(self, names: List[str]) -> List[Tag]:
        pass


class AttachmentRepository(ABC):
    @abstractmethod
    async def create(self, attachment: Attachment) -> Attachment:
        pass

    @abstractmethod
    async def get_by_id(self, attachment_id: UUID) -> Optional[Attachment]:
        pass

    @abstractmethod
    async def list_by_task(self, task_id: UUID) -> List[Attachment]:
        pass

    @abstractmethod
    async def delete(self, attachment_id: UUID) -> None:
        pass


class AuditEventRepository(ABC):
    @abstractmethod
    async def create(self, event: AuditEvent) -> AuditEvent:
        pass

    @abstractmethod
    async def list(
        self,
        user_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        event_type: Optional[EventType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[AuditEvent], int]:
        pass


class ReminderLogRepository(ABC):
    @abstractmethod
    async def create(self, reminder: ReminderLog) -> ReminderLog:
        pass

    @abstractmethod
    async def get_by_task_and_type(
        self, task_id: UUID, reminder_type: ReminderType
    ) -> Optional[ReminderLog]:
        pass


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def create(self, token: RefreshToken) -> RefreshToken:
        pass

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        pass

    @abstractmethod
    async def revoke_by_user_id(self, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def revoke_by_token_hash(self, token_hash: str) -> None:
        pass
