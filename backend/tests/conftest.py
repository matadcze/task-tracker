"""Pytest configuration and fixtures"""

import sys
from pathlib import Path
from datetime import timedelta
from src.core.time import utc_now
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to Python path so imports work
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.domain.entities import User, Task, Attachment, Tag, AuditEvent, ReminderLog
from src.domain.value_objects import TaskStatus, TaskPriority, EventType, ReminderType
from src.infrastructure.database.models import Base
from src.infrastructure.auth.password import PasswordUtils
from src.infrastructure.auth.jwt_provider import JWTProvider


# ============== Database Fixtures ==============


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite database session for testing"""
    # Use sqlite for testing - it's faster and doesn't require PostgreSQL
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


# ============== Entity Fixtures ==============


@pytest.fixture
def sample_user_id():
    """Generate a sample user ID"""
    return uuid4()


@pytest.fixture
def sample_user(sample_user_id):
    """Create a sample user entity"""
    return User(
        id=sample_user_id,
        email="test@example.com",
        password_hash=PasswordUtils.hash_password("TestPassword123"),
        full_name="Test User",
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_user2():
    """Create another sample user entity"""
    return User(
        id=uuid4(),
        email="other@example.com",
        password_hash=PasswordUtils.hash_password("OtherPassword123"),
        full_name="Other User",
        is_active=True,
    )


@pytest.fixture
def sample_task(sample_user_id):
    """Create a sample task entity"""
    return Task(
        id=uuid4(),
        owner_id=sample_user_id,
        title="Test Task",
        description="This is a test task",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        due_date=utc_now() + timedelta(days=7),
        tags=["work", "important"],
    )


@pytest.fixture
def sample_task_overdue(sample_user_id):
    """Create a sample overdue task"""
    return Task(
        id=uuid4(),
        owner_id=sample_user_id,
        title="Overdue Task",
        description="This task is past due",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        due_date=utc_now() - timedelta(days=1),
    )


@pytest.fixture
def sample_task_done(sample_user_id):
    """Create a completed task"""
    return Task(
        id=uuid4(),
        owner_id=sample_user_id,
        title="Done Task",
        status=TaskStatus.DONE,
        priority=TaskPriority.LOW,
    )


@pytest.fixture
def sample_attachment(sample_user_id):
    """Create a sample attachment entity"""
    task_id = uuid4()
    return Attachment(
        id=uuid4(),
        task_id=task_id,
        filename="test.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        storage_path="/uploads/test_123.pdf",
    )


@pytest.fixture
def sample_tag():
    """Create a sample tag entity"""
    return Tag(id=uuid4(), name="work")


@pytest.fixture
def sample_audit_event(sample_user_id):
    """Create a sample audit event"""
    return AuditEvent(
        id=uuid4(),
        user_id=sample_user_id,
        event_type=EventType.TASK_CREATED,
        task_id=uuid4(),
        details={"title": "New Task"},
    )


# ============== Mock Repository Fixtures ==============


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_task_repository():
    """Create a mock task repository"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.list = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_attachment_repository():
    """Create a mock attachment repository"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.list_by_task = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_audit_repository():
    """Create a mock audit repository"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.list = AsyncMock()
    return repo


@pytest.fixture
def mock_tag_repository():
    """Create a mock tag repository"""
    repo = AsyncMock()
    repo.get_or_create = AsyncMock()
    repo.get_by_names = AsyncMock()
    return repo


@pytest.fixture
def mock_refresh_token_repository():
    """Create a mock refresh token repository"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_token_hash = AsyncMock()
    repo.revoke_by_user_id = AsyncMock()
    repo.revoke_by_token_hash = AsyncMock()
    return repo


# ============== Mock Service Fixtures ==============


@pytest.fixture
def mock_metrics_provider():
    """Create a mock metrics provider"""
    metrics = MagicMock()
    metrics.track_auth_operation = MagicMock()
    metrics.track_task_operation = MagicMock()
    metrics.track_attachment_operation = MagicMock()
    metrics.track_audit_operation = MagicMock()
    return metrics


@pytest.fixture
def mock_storage_provider():
    """Create a mock storage provider"""
    storage = AsyncMock()
    storage.save_file = AsyncMock()
    storage.get_file_path = AsyncMock()
    storage.delete_file = AsyncMock()
    storage.file_exists = AsyncMock()
    return storage


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter"""
    limiter = AsyncMock()
    limiter.check_login_rate_limit = AsyncMock(return_value=True)
    limiter.check_register_rate_limit = AsyncMock(return_value=True)
    limiter.check_refresh_rate_limit = AsyncMock(return_value=True)
    limiter.check_password_change_rate_limit = AsyncMock(return_value=True)
    limiter.is_account_locked = AsyncMock(return_value=(False, 0))
    limiter.record_failed_login = AsyncMock()
    limiter.reset_failed_logins = AsyncMock()
    return limiter


# ============== Auth Token Fixtures ==============


@pytest.fixture
def valid_access_token(sample_user_id):
    """Create a valid access token"""
    return JWTProvider.create_access_token(sample_user_id)


@pytest.fixture
def valid_refresh_token(sample_user_id):
    """Create a valid refresh token"""
    return JWTProvider.create_refresh_token(sample_user_id)


@pytest.fixture
def expired_access_token(sample_user_id):
    """Create an expired access token"""
    expired_delta = timedelta(hours=-1)
    return JWTProvider.create_access_token(sample_user_id, expires_delta=expired_delta)


# ============== Utility Fixtures ==============


@pytest.fixture
def password_utils():
    """Provide password utilities"""
    return PasswordUtils


@pytest.fixture
def jwt_provider():
    """Provide JWT provider"""
    return JWTProvider


# ============== Reminder Fixtures ==============


@pytest.fixture
def sample_reminder_log(sample_user_id):
    """Create a sample reminder log"""
    return ReminderLog(
        id=uuid4(),
        task_id=uuid4(),
        reminder_type=ReminderType.DUE_SOON,
        sent_at=utc_now(),
    )


@pytest.fixture
def mock_reminder_repository():
    """Create a mock reminder log repository"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_task_and_type = AsyncMock()
    repo.list_by_task = AsyncMock()
    repo.delete = AsyncMock()
    return repo
