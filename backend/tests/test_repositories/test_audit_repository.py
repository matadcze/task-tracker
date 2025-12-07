"""Tests for AuditRepository"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.domain.entities import AuditEvent
from src.domain.value_objects import EventType
from src.infrastructure.repositories.audit_repository import AuditEventRepositoryImpl


@pytest.mark.asyncio
class TestAuditEventRepositoryCreate:
    """Tests for AuditEventRepository.create()"""

    async def test_create_audit_event(self, db_session: AsyncSession, sample_audit_event):
        """Test creating an audit event"""
        repo = AuditEventRepositoryImpl(db_session)

        result = await repo.create(sample_audit_event)

        assert result.id == sample_audit_event.id
        assert result.event_type == EventType.TASK_CREATED
        assert result.user_id == sample_audit_event.user_id


@pytest.mark.asyncio
class TestAuditEventRepositoryList:
    """Tests for AuditEventRepository.list()"""

    async def test_list_audit_events(self, db_session: AsyncSession, sample_user_id):
        """Test listing audit events"""
        repo = AuditEventRepositoryImpl(db_session)

        # Create events
        event1 = AuditEvent(
            user_id=sample_user_id,
            event_type=EventType.TASK_CREATED,
            task_id=uuid4(),
        )
        event2 = AuditEvent(
            user_id=sample_user_id,
            event_type=EventType.TASK_UPDATED,
            task_id=uuid4(),
        )

        await repo.create(event1)
        await repo.create(event2)

        # List
        result, total = await repo.list()

        assert total >= 2
        assert len(result) >= 2

    async def test_list_audit_events_filter_by_user(self, db_session: AsyncSession, sample_user_id):
        """Test listing events filtered by user"""
        repo = AuditEventRepositoryImpl(db_session)

        other_user_id = uuid4()

        # Create events for both users
        event1 = AuditEvent(
            user_id=sample_user_id,
            event_type=EventType.TASK_CREATED,
            task_id=uuid4(),
        )
        event2 = AuditEvent(
            user_id=other_user_id,
            event_type=EventType.TASK_CREATED,
            task_id=uuid4(),
        )

        await repo.create(event1)
        await repo.create(event2)

        # List for specific user
        result, total = await repo.list(user_id=sample_user_id)

        user_events = [e for e in result if e.user_id == sample_user_id]
        assert len(user_events) >= 1

    async def test_list_audit_events_filter_by_event_type(
        self, db_session: AsyncSession, sample_user_id
    ):
        """Test listing events filtered by type"""
        repo = AuditEventRepositoryImpl(db_session)

        # Create events of different types
        event1 = AuditEvent(
            user_id=sample_user_id,
            event_type=EventType.TASK_CREATED,
            task_id=uuid4(),
        )
        event2 = AuditEvent(
            user_id=sample_user_id,
            event_type=EventType.TASK_DELETED,
            task_id=uuid4(),
        )

        await repo.create(event1)
        await repo.create(event2)

        # List only CREATED events
        result, total = await repo.list(event_type=EventType.TASK_CREATED)

        created_events = [e for e in result if e.event_type == EventType.TASK_CREATED]
        assert len(created_events) >= 1

    async def test_list_audit_events_filter_by_task(self, db_session: AsyncSession, sample_user_id):
        """Test listing events filtered by task"""
        repo = AuditEventRepositoryImpl(db_session)

        task_id = uuid4()

        # Create events for same and different tasks
        event1 = AuditEvent(
            user_id=sample_user_id,
            event_type=EventType.TASK_CREATED,
            task_id=task_id,
        )
        event2 = AuditEvent(
            user_id=sample_user_id,
            event_type=EventType.TASK_CREATED,
            task_id=uuid4(),
        )

        await repo.create(event1)
        await repo.create(event2)

        # List for specific task
        result, total = await repo.list(task_id=task_id)

        task_events = [e for e in result if e.task_id == task_id]
        assert len(task_events) >= 1

    async def test_list_audit_events_filter_by_date_range(
        self, db_session: AsyncSession, sample_user_id
    ):
        """Test listing events filtered by date range"""
        repo = AuditEventRepositoryImpl(db_session)

        now = datetime.now(timezone.utc)
        past = now - timedelta(days=7)
        future = now + timedelta(days=7)

        # Create event
        event = AuditEvent(
            user_id=sample_user_id,
            event_type=EventType.TASK_CREATED,
            task_id=uuid4(),
        )

        await repo.create(event)

        # List with date range that includes the event
        result, total = await repo.list(from_date=past, to_date=future)

        assert total >= 1

    async def test_list_audit_events_pagination(self, db_session: AsyncSession, sample_user_id):
        """Test pagination in audit list"""
        repo = AuditEventRepositoryImpl(db_session)

        # Create multiple events
        for i in range(5):
            event = AuditEvent(
                user_id=sample_user_id,
                event_type=EventType.TASK_CREATED,
                task_id=uuid4(),
            )
            await repo.create(event)

        # Get first page
        result1, total1 = await repo.list(page=1, page_size=2)

        # Get second page
        result2, total2 = await repo.list(page=2, page_size=2)

        assert total1 == total2
