from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict
from src.core.time import utc_now

from .value_objects import EventType, ReminderType, TaskPriority, TaskStatus


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email: str
    password_hash: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(from_attributes=True)

    def can_authenticate(self) -> bool:

        return self.is_active

    def can_be_accessed_by(self, user_id: UUID) -> bool:

        return self.id == user_id


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    def is_overdue(self) -> bool:

        if self.due_date is None:
            return False
        return utc_now() > self.due_date and self.status != TaskStatus.DONE

    def can_be_modified_by(self, user_id: UUID) -> bool:

        return self.owner_id == user_id

    def can_be_viewed_by(self, user_id: UUID) -> bool:

        return self.owner_id == user_id

    def mark_as_done(self) -> None:

        self.status = TaskStatus.DONE
        self.updated_at = utc_now()

    def mark_as_in_progress(self) -> None:

        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = utc_now()

    def add_tag(self, tag: str) -> bool:

        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = utc_now()
            return True
        return False

    def remove_tag(self, tag: str) -> bool:

        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = utc_now()
            return True
        return False

    def has_tag(self, tag: str) -> bool:

        return tag in self.tags


class Tag(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str

    model_config = ConfigDict(from_attributes=True)


class Attachment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    filename: str
    content_type: str = Field(alias="mime_type")
    size_bytes: int = Field(alias="file_size_bytes")
    storage_path: str = Field(alias="file_path")
    uploaded_by: UUID | None = None
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="allow")

    def is_for_task(self, task_id: UUID) -> bool:

        return self.task_id == task_id

    def is_image(self) -> bool:

        return self.content_type.startswith("image/")

    def is_document(self) -> bool:

        document_types = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/plain",
            "text/csv",
        }
        return self.content_type in document_types

    def size_in_mb(self) -> float:

        return round(self.size_bytes / (1024 * 1024), 2)


class AuditEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    event_type: EventType
    task_id: Optional[UUID] = None
    attachment_id: Optional[UUID] = None
    details: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(from_attributes=True)


class ReminderLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    reminder_type: ReminderType
    sent_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(from_attributes=True)


class RefreshToken(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked: bool = False

    model_config = ConfigDict(from_attributes=True)
