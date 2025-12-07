import uuid
from src.core.time import utc_now

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.domain.value_objects import EventType, ReminderType, TaskPriority, TaskStatus

from .session import Base

task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE")),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE")),
)


class UserModel(Base):

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    tasks = relationship("TaskModel", back_populates="owner", cascade="all, delete-orphan")
    audit_events = relationship("AuditEventModel", back_populates="user")
    refresh_tokens = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan"
    )


class TaskModel(Base):

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False, index=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False, index=True)
    due_date = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("UserModel", back_populates="tasks")
    tags = relationship("TagModel", secondary=task_tags, back_populates="tasks")
    attachments = relationship(
        "AttachmentModel", back_populates="task", cascade="all, delete-orphan"
    )
    audit_events = relationship("AuditEventModel", back_populates="task")
    reminder_logs = relationship(
        "ReminderLogModel", back_populates="task", cascade="all, delete-orphan"
    )


class TagModel(Base):

    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)

    tasks = relationship("TaskModel", secondary=task_tags, back_populates="tags")


class AttachmentModel(Base):

    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    task = relationship("TaskModel", back_populates="attachments")
    audit_events = relationship("AuditEventModel", back_populates="attachment")


class AuditEventModel(Base):

    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type = Column(Enum(EventType), nullable=False, index=True)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    attachment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attachments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Use portable JSON type so SQLite test database can compile schema
    details = Column(JSON, default={}, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    user = relationship("UserModel", back_populates="audit_events")
    task = relationship("TaskModel", back_populates="audit_events")
    attachment = relationship("AttachmentModel", back_populates="audit_events")


class ReminderLogModel(Base):

    __tablename__ = "reminder_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reminder_type = Column(Enum(ReminderType), nullable=False)
    sent_at = Column(DateTime, default=utc_now, nullable=False)

    task = relationship("TaskModel", back_populates="reminder_logs")

    __table_args__ = (UniqueConstraint("task_id", "reminder_type", name="uq_task_reminder_type"),)


class RefreshTokenModel(Base):

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked = Column(Boolean, default=False, nullable=False, index=True)

    user = relationship("UserModel", back_populates="refresh_tokens")
