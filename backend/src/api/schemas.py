from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.domain.value_objects import EventType, TaskPriority, TaskStatus


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    components: Dict[str, str]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., max_length=72, description="User password")


class TokenResponse(BaseModel):

    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class RefreshTokenRequest(BaseModel):

    refresh_token: str = Field(..., description="Refresh token")


class ChangePasswordRequest(BaseModel):

    current_password: str = Field(..., max_length=72, description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=72, description="New password (8-72 characters)"
    )


class UpdateProfileRequest(BaseModel):

    full_name: str = Field(..., min_length=1, max_length=100, description="Updated full name")


class UserResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: Optional[str]
    created_at: datetime


class TaskCreate(BaseModel):

    title: str = Field(..., max_length=500, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: Optional[TaskStatus] = Field(TaskStatus.TODO, description="Task status")
    priority: Optional[TaskPriority] = Field(TaskPriority.MEDIUM, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    tags: List[str] = Field(default_factory=list, description="Task tags")


class TaskUpdate(BaseModel):

    title: Optional[str] = Field(None, max_length=500, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    priority: Optional[TaskPriority] = Field(None, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    tags: Optional[List[str]] = Field(None, description="Task tags")


class TaskResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    tags: List[str]
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):

    items: List[TaskResponse]
    page: int
    page_size: int
    total: int


class ChatMessageRequest(BaseModel):

    message: str = Field(..., min_length=1, max_length=1000, description="User chat message")


class ChatMessageResponse(BaseModel):

    reply: str
    created_task: Optional[TaskResponse] = None


class AttachmentSummary(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    size_bytes: int
    content_type: str
    created_at: datetime


class TaskDetailResponse(BaseModel):

    task: TaskResponse
    attachments: List[AttachmentSummary]


class AttachmentResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class AttachmentListResponse(BaseModel):

    items: List[AttachmentResponse]


class AuditEventResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID]
    event_type: EventType
    task_id: Optional[UUID]
    attachment_id: Optional[UUID]
    details: Dict[str, Any]
    created_at: datetime


class AuditEventListResponse(BaseModel):

    items: List[AuditEventResponse]
    page: int
    page_size: int
    total: int
