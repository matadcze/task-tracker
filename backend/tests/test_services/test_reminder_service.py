"""Tests for ReminderService"""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.domain.services.reminder_service import ReminderService
from src.domain.entities import Task, ReminderLog, AuditEvent
from src.domain.value_objects import TaskStatus, TaskPriority, ReminderType, EventType
from src.core.time import utc_now


@pytest.mark.asyncio
class TestReminderServiceSendDueSoonReminders:
    """Tests for ReminderService.send_due_soon_reminders()"""

    async def test_send_due_soon_reminders_success(self, sample_user_id, mock_metrics_provider):
        """Test successful sending of due-soon reminders"""
        task_due_soon = Task(
            id=uuid4(),
            owner_id=sample_user_id,
            title="Task Due Soon",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            due_date=utc_now() + timedelta(hours=6),
        )

        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()

        mock_task_repo.list_due_between.return_value = [task_due_soon]
        mock_reminder_repo.get_by_task_and_type.return_value = None
        mock_reminder_repo.create.return_value = ReminderLog(
            id=uuid4(),
            task_id=task_due_soon.id,
            reminder_type=ReminderType.DUE_SOON,
            sent_at=utc_now(),
        )
        mock_audit_repo.create.return_value = AuditEvent(
            id=uuid4(),
            user_id=sample_user_id,
            event_type=EventType.REMINDER_SENT,
            task_id=task_due_soon.id,
        )

        service = ReminderService(
            task_repo=mock_task_repo,
            reminder_repo=mock_reminder_repo,
            audit_repo=mock_audit_repo,
            metrics=mock_metrics_provider,
        )

        result = await service.send_due_soon_reminders(window_hours=24)

        assert result == 1
        mock_task_repo.list_due_between.assert_called_once()
        mock_reminder_repo.create.assert_called_once()
        mock_audit_repo.create.assert_called_once()
        mock_metrics_provider.track_audit_event.assert_called_once_with(EventType.REMINDER_SENT.value)

    async def test_send_due_soon_reminders_no_tasks(self, mock_metrics_provider):
        """Test when no tasks are due soon"""
        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()

        mock_task_repo.list_due_between.return_value = []

        service = ReminderService(
            task_repo=mock_task_repo,
            reminder_repo=mock_reminder_repo,
            audit_repo=mock_audit_repo,
            metrics=mock_metrics_provider,
        )

        result = await service.send_due_soon_reminders(window_hours=24)

        assert result == 0
        mock_reminder_repo.create.assert_not_called()
        mock_audit_repo.create.assert_not_called()

    async def test_send_due_soon_reminders_skips_existing(self, sample_user_id, mock_metrics_provider):
        """Test that reminders are not sent twice for same task"""
        task = Task(
            id=uuid4(),
            owner_id=sample_user_id,
            title="Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=utc_now() + timedelta(hours=12),
        )

        existing_reminder = ReminderLog(
            id=uuid4(),
            task_id=task.id,
            reminder_type=ReminderType.DUE_SOON,
            sent_at=utc_now() - timedelta(hours=1),
        )

        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()

        mock_task_repo.list_due_between.return_value = [task]
        mock_reminder_repo.get_by_task_and_type.return_value = existing_reminder

        service = ReminderService(
            task_repo=mock_task_repo,
            reminder_repo=mock_reminder_repo,
            audit_repo=mock_audit_repo,
            metrics=mock_metrics_provider,
        )

        result = await service.send_due_soon_reminders(window_hours=24)

        assert result == 0
        mock_reminder_repo.create.assert_not_called()
        mock_audit_repo.create.assert_not_called()

    async def test_send_due_soon_reminders_custom_window(self, sample_user_id, mock_metrics_provider):
        """Test using custom time window"""
        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()

        mock_task_repo.list_due_between.return_value = []

        service = ReminderService(
            task_repo=mock_task_repo,
            reminder_repo=mock_reminder_repo,
            audit_repo=mock_audit_repo,
            metrics=mock_metrics_provider,
        )

        await service.send_due_soon_reminders(window_hours=48)

        # Verify list_due_between was called with correct window
        mock_task_repo.list_due_between.assert_called_once()
        call_args = mock_task_repo.list_due_between.call_args[0]
        start_time = call_args[0]
        end_time = call_args[1]
        time_diff = end_time - start_time
        assert time_diff.total_seconds() == 48 * 3600

    async def test_send_due_soon_reminders_multiple_tasks(self, sample_user_id, mock_metrics_provider):
        """Test sending reminders for multiple tasks"""
        task1 = Task(
            id=uuid4(),
            owner_id=sample_user_id,
            title="Task 1",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            due_date=utc_now() + timedelta(hours=6),
        )
        task2 = Task(
            id=uuid4(),
            owner_id=sample_user_id,
            title="Task 2",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=utc_now() + timedelta(hours=12),
        )

        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()

        mock_task_repo.list_due_between.return_value = [task1, task2]
        mock_reminder_repo.get_by_task_and_type.return_value = None
        mock_reminder_repo.create.return_value = None
        mock_audit_repo.create.return_value = None

        service = ReminderService(
            task_repo=mock_task_repo,
            reminder_repo=mock_reminder_repo,
            audit_repo=mock_audit_repo,
            metrics=mock_metrics_provider,
        )

        result = await service.send_due_soon_reminders(window_hours=24)

        assert result == 2
        assert mock_reminder_repo.create.call_count == 2
        assert mock_audit_repo.create.call_count == 2

    async def test_send_due_soon_reminders_continues_on_error(self, sample_user_id, mock_metrics_provider):
        """Test that processing continues if one reminder fails"""
        task1 = Task(
            id=uuid4(),
            owner_id=sample_user_id,
            title="Task 1",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            due_date=utc_now() + timedelta(hours=6),
        )
        task2 = Task(
            id=uuid4(),
            owner_id=sample_user_id,
            title="Task 2",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=utc_now() + timedelta(hours=12),
        )

        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()

        mock_task_repo.list_due_between.return_value = [task1, task2]
        mock_reminder_repo.get_by_task_and_type.return_value = None

        # First reminder fails, second succeeds
        mock_reminder_repo.create.side_effect = [Exception("Database error"), None]
        mock_audit_repo.create.return_value = None

        service = ReminderService(
            task_repo=mock_task_repo,
            reminder_repo=mock_reminder_repo,
            audit_repo=mock_audit_repo,
            metrics=mock_metrics_provider,
        )

        result = await service.send_due_soon_reminders(window_hours=24)

        # Only one reminder should succeed
        assert result == 1
        assert mock_reminder_repo.create.call_count == 2
        # Second task's audit event should still be created
        assert mock_audit_repo.create.call_count == 1

    async def test_send_due_soon_reminders_audit_event_details(self, sample_user_id, mock_metrics_provider):
        """Test that audit event includes task due date in details"""
        task = Task(
            id=uuid4(),
            owner_id=sample_user_id,
            title="Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=utc_now() + timedelta(days=1),
        )

        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()

        mock_task_repo.list_due_between.return_value = [task]
        mock_reminder_repo.get_by_task_and_type.return_value = None
        mock_reminder_repo.create.return_value = None

        created_audit_event = None

        async def capture_audit_event(event):
            nonlocal created_audit_event
            created_audit_event = event

        mock_audit_repo.create.side_effect = capture_audit_event

        service = ReminderService(
            task_repo=mock_task_repo,
            reminder_repo=mock_reminder_repo,
            audit_repo=mock_audit_repo,
            metrics=mock_metrics_provider,
        )

        await service.send_due_soon_reminders(window_hours=24)

        assert created_audit_event is not None
        assert created_audit_event.event_type == EventType.REMINDER_SENT
        assert "due_date" in created_audit_event.details

    async def test_send_due_soon_reminders_creates_reminder_with_correct_type(
        self, sample_user_id, mock_metrics_provider
    ):
        """Test that reminders are created with DUE_SOON type"""
        task = Task(
            id=uuid4(),
            owner_id=sample_user_id,
            title="Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=utc_now() + timedelta(hours=12),
        )

        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()

        mock_task_repo.list_due_between.return_value = [task]
        mock_reminder_repo.get_by_task_and_type.return_value = None

        created_reminder = None

        async def capture_reminder(reminder):
            nonlocal created_reminder
            created_reminder = reminder

        mock_reminder_repo.create.side_effect = capture_reminder
        mock_audit_repo.create.return_value = None

        service = ReminderService(
            task_repo=mock_task_repo,
            reminder_repo=mock_reminder_repo,
            audit_repo=mock_audit_repo,
            metrics=mock_metrics_provider,
        )

        await service.send_due_soon_reminders(window_hours=24)

        assert created_reminder is not None
        assert created_reminder.reminder_type == ReminderType.DUE_SOON
        assert created_reminder.task_id == task.id

    async def test_send_due_soon_reminders_tracks_metrics(self, sample_user_id, mock_metrics_provider):
        """Test that metrics are tracked for each reminder sent"""
        task = Task(
            id=uuid4(),
            owner_id=sample_user_id,
            title="Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=utc_now() + timedelta(hours=12),
        )

        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()

        mock_task_repo.list_due_between.return_value = [task]
        mock_reminder_repo.get_by_task_and_type.return_value = None
        mock_reminder_repo.create.return_value = None
        mock_audit_repo.create.return_value = None

        service = ReminderService(
            task_repo=mock_task_repo,
            reminder_repo=mock_reminder_repo,
            audit_repo=mock_audit_repo,
            metrics=mock_metrics_provider,
        )

        await service.send_due_soon_reminders(window_hours=24)

        mock_metrics_provider.track_audit_event.assert_called_once_with(EventType.REMINDER_SENT.value)

    async def test_send_due_soon_reminders_empty_window_hours(self, mock_metrics_provider):
        """Test behavior with minimal window (edge case)"""
        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()

        mock_task_repo.list_due_between.return_value = []

        service = ReminderService(
            task_repo=mock_task_repo,
            reminder_repo=mock_reminder_repo,
            audit_repo=mock_audit_repo,
            metrics=mock_metrics_provider,
        )

        result = await service.send_due_soon_reminders(window_hours=1)

        assert result == 0
        mock_task_repo.list_due_between.assert_called_once()
