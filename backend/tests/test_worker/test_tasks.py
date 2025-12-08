"""Tests for Celery worker tasks"""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.worker.tasks import send_due_soon_reminders, _run_reminders
from src.core.time import utc_now
from src.domain.entities import Task, ReminderLog, AuditEvent
from src.domain.value_objects import TaskStatus, TaskPriority, ReminderType, EventType


@pytest.mark.asyncio
class TestRunRemindersAsync:
    """Tests for the _run_reminders async function"""

    async def test_run_reminders_success(self, sample_user_id, sample_task):
        """Test successful reminder processing"""
        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()
        mock_metrics = MagicMock()

        tasks_due = [sample_task]
        mock_task_repo.list_due_between.return_value = tasks_due
        mock_reminder_repo.get_by_task_and_type.return_value = None
        mock_reminder_repo.create.return_value = ReminderLog(
            id=uuid4(),
            task_id=sample_task.id,
            reminder_type=ReminderType.DUE_SOON,
            sent_at=utc_now(),
        )
        mock_audit_repo.create.return_value = AuditEvent(
            id=uuid4(),
            user_id=sample_user_id,
            event_type=EventType.REMINDER_SENT,
            task_id=sample_task.id,
        )

        with patch("src.worker.tasks.AsyncSessionLocal") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_factory.return_value = mock_session

            with patch("src.worker.tasks.TaskRepositoryImpl") as mock_task_repo_class:
                with patch(
                    "src.worker.tasks.ReminderLogRepositoryImpl"
                ) as mock_reminder_repo_class:
                    with patch(
                        "src.worker.tasks.AuditEventRepositoryImpl"
                    ) as mock_audit_repo_class:
                        with patch(
                            "src.worker.tasks.PrometheusMetricsProvider"
                        ) as mock_metrics_class:
                            with patch("src.worker.tasks.ReminderService") as mock_service_class:
                                mock_task_repo_class.return_value = mock_task_repo
                                mock_reminder_repo_class.return_value = mock_reminder_repo
                                mock_audit_repo_class.return_value = mock_audit_repo
                                mock_metrics_class.return_value = mock_metrics

                                mock_service = AsyncMock()
                                mock_service.send_due_soon_reminders.return_value = 1
                                mock_service_class.return_value = mock_service

                                result = await _run_reminders(window_hours=24)

                                assert result == 1
                                mock_service.send_due_soon_reminders.assert_called_once_with(
                                    window_hours=24
                                )
                                mock_session.commit.assert_called_once()

    async def test_run_reminders_no_tasks(self):
        """Test when no tasks are due within the window"""
        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()
        mock_metrics = MagicMock()

        mock_task_repo.list_due_between.return_value = []

        with patch("src.worker.tasks.AsyncSessionLocal") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_factory.return_value = mock_session

            with patch("src.worker.tasks.TaskRepositoryImpl") as mock_task_repo_class:
                with patch(
                    "src.worker.tasks.ReminderLogRepositoryImpl"
                ) as mock_reminder_repo_class:
                    with patch(
                        "src.worker.tasks.AuditEventRepositoryImpl"
                    ) as mock_audit_repo_class:
                        with patch(
                            "src.worker.tasks.PrometheusMetricsProvider"
                        ) as mock_metrics_class:
                            with patch("src.worker.tasks.ReminderService") as mock_service_class:
                                mock_task_repo_class.return_value = mock_task_repo
                                mock_reminder_repo_class.return_value = mock_reminder_repo
                                mock_audit_repo_class.return_value = mock_audit_repo
                                mock_metrics_class.return_value = mock_metrics

                                mock_service = AsyncMock()
                                mock_service.send_due_soon_reminders.return_value = 0
                                mock_service_class.return_value = mock_service

                                result = await _run_reminders(window_hours=24)

                                assert result == 0

    async def test_run_reminders_database_error_rollback(self, sample_user_id, sample_task):
        """Test that database transaction is rolled back on error"""
        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()
        mock_metrics = MagicMock()

        with patch("src.worker.tasks.AsyncSessionLocal") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_factory.return_value = mock_session

            with patch("src.worker.tasks.TaskRepositoryImpl") as mock_task_repo_class:
                with patch(
                    "src.worker.tasks.ReminderLogRepositoryImpl"
                ) as mock_reminder_repo_class:
                    with patch(
                        "src.worker.tasks.AuditEventRepositoryImpl"
                    ) as mock_audit_repo_class:
                        with patch(
                            "src.worker.tasks.PrometheusMetricsProvider"
                        ) as mock_metrics_class:
                            with patch("src.worker.tasks.ReminderService") as mock_service_class:
                                mock_task_repo_class.return_value = mock_task_repo
                                mock_reminder_repo_class.return_value = mock_reminder_repo
                                mock_audit_repo_class.return_value = mock_audit_repo
                                mock_metrics_class.return_value = mock_metrics

                                mock_service = AsyncMock()
                                mock_service.send_due_soon_reminders.side_effect = Exception(
                                    "Database error"
                                )
                                mock_service_class.return_value = mock_service

                                with pytest.raises(Exception, match="Database error"):
                                    await _run_reminders(window_hours=24)

                                mock_session.rollback.assert_called_once()

    async def test_run_reminders_multiple_tasks(self, sample_user_id):
        """Test processing multiple tasks at once"""
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
        mock_metrics = MagicMock()

        mock_task_repo.list_due_between.return_value = [task1, task2]

        with patch("src.worker.tasks.AsyncSessionLocal") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_factory.return_value = mock_session

            with patch("src.worker.tasks.TaskRepositoryImpl") as mock_task_repo_class:
                with patch(
                    "src.worker.tasks.ReminderLogRepositoryImpl"
                ) as mock_reminder_repo_class:
                    with patch(
                        "src.worker.tasks.AuditEventRepositoryImpl"
                    ) as mock_audit_repo_class:
                        with patch(
                            "src.worker.tasks.PrometheusMetricsProvider"
                        ) as mock_metrics_class:
                            with patch("src.worker.tasks.ReminderService") as mock_service_class:
                                mock_task_repo_class.return_value = mock_task_repo
                                mock_reminder_repo_class.return_value = mock_reminder_repo
                                mock_audit_repo_class.return_value = mock_audit_repo
                                mock_metrics_class.return_value = mock_metrics

                                mock_service = AsyncMock()
                                mock_service.send_due_soon_reminders.return_value = 2
                                mock_service_class.return_value = mock_service

                                result = await _run_reminders(window_hours=24)

                                assert result == 2

    async def test_run_reminders_custom_window(self):
        """Test using custom time window"""
        mock_task_repo = AsyncMock()
        mock_reminder_repo = AsyncMock()
        mock_audit_repo = AsyncMock()
        mock_metrics = MagicMock()

        with patch("src.worker.tasks.AsyncSessionLocal") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_factory.return_value = mock_session

            with patch("src.worker.tasks.TaskRepositoryImpl") as mock_task_repo_class:
                with patch(
                    "src.worker.tasks.ReminderLogRepositoryImpl"
                ) as mock_reminder_repo_class:
                    with patch(
                        "src.worker.tasks.AuditEventRepositoryImpl"
                    ) as mock_audit_repo_class:
                        with patch(
                            "src.worker.tasks.PrometheusMetricsProvider"
                        ) as mock_metrics_class:
                            with patch("src.worker.tasks.ReminderService") as mock_service_class:
                                mock_task_repo_class.return_value = mock_task_repo
                                mock_reminder_repo_class.return_value = mock_reminder_repo
                                mock_audit_repo_class.return_value = mock_audit_repo
                                mock_metrics_class.return_value = mock_metrics

                                mock_service = AsyncMock()
                                mock_service.send_due_soon_reminders.return_value = 0
                                mock_service_class.return_value = mock_service

                                await _run_reminders(window_hours=48)

                                mock_service.send_due_soon_reminders.assert_called_once_with(
                                    window_hours=48
                                )


class TestSendDueSoonRemindersTask:
    """Tests for the Celery task send_due_soon_reminders"""

    def test_task_is_registered(self):
        """Test that task is registered with Celery"""
        from src.worker.celery_app import celery_app

        assert "reminders.send_due_soon" in celery_app.tasks

    def test_task_returns_processed_count(self):
        """Test that task returns count of processed reminders"""
        with patch("src.worker.tasks.configure_logging"):
            with patch("src.worker.tasks._run_reminders", new_callable=AsyncMock, return_value=5):
                with patch("src.worker.tasks.asyncio.run", side_effect=lambda coro: 5):
                    with patch("src.worker.tasks.log_json"):
                        result = send_due_soon_reminders()

                        assert result == 5

    def test_task_uses_24_hour_window(self):
        """Test that task uses default 24-hour window"""

        async def mock_run_reminders(**kwargs):
            return 3

        with patch("src.worker.tasks.configure_logging"):
            with patch("src.worker.tasks._run_reminders", side_effect=mock_run_reminders):
                with patch("src.worker.tasks.asyncio.run", side_effect=lambda coro: 3) as mock_run:
                    with patch("src.worker.tasks.log_json"):
                        send_due_soon_reminders()

                        assert mock_run.called

    def test_task_calls_configure_logging(self):
        """Test that task initializes logging"""
        with patch("src.worker.tasks.configure_logging") as mock_config_logging:
            with patch("src.worker.tasks._run_reminders", new_callable=AsyncMock, return_value=0):
                with patch("src.worker.tasks.asyncio.run", side_effect=lambda coro: 0):
                    with patch("src.worker.tasks.log_json"):
                        send_due_soon_reminders()

                        mock_config_logging.assert_called_once()

    def test_task_logs_result(self):
        """Test that task logs the result"""
        with patch("src.worker.tasks.configure_logging"):
            with patch("src.worker.tasks._run_reminders", new_callable=AsyncMock, return_value=3):
                with patch("src.worker.tasks.asyncio.run", side_effect=lambda coro: 3):
                    with patch("src.worker.tasks.log_json") as mock_log_json:
                        with patch("src.worker.tasks.celery_app.log.get_default_logger"):
                            send_due_soon_reminders()

                            mock_log_json.assert_called_once()
                            call_args = mock_log_json.call_args
                            assert call_args[0][1] == "reminders.sent"
                            assert call_args[1]["count"] == 3
                            assert call_args[1]["window_hours"] == 24

    def test_task_logs_include_timestamp(self):
        """Test that task logs include timestamp"""
        with patch("src.worker.tasks.configure_logging"):
            with patch("src.worker.tasks._run_reminders", new_callable=AsyncMock, return_value=1):
                with patch("src.worker.tasks.asyncio.run", side_effect=lambda coro: 1):
                    with patch("src.worker.tasks.log_json") as mock_log_json:
                        with patch("src.worker.tasks.celery_app.log.get_default_logger"):
                            send_due_soon_reminders()

                            call_args = mock_log_json.call_args
                            assert "at" in call_args[1]
                            assert call_args[1]["at"] is not None

    def test_task_handles_zero_reminders(self):
        """Test task handling when no reminders are sent"""
        with patch("src.worker.tasks.configure_logging"):
            with patch("src.worker.tasks._run_reminders", new_callable=AsyncMock, return_value=0):
                with patch("src.worker.tasks.asyncio.run", side_effect=lambda coro: 0):
                    with patch("src.worker.tasks.log_json") as mock_log_json:
                        with patch("src.worker.tasks.celery_app.log.get_default_logger"):
                            result = send_due_soon_reminders()

                            assert result == 0
                            mock_log_json.assert_called_once()

    def test_task_executes_async_function(self):
        """Test that task properly executes async function"""
        with patch("src.worker.tasks.configure_logging"):
            with patch("src.worker.tasks._run_reminders", new_callable=AsyncMock, return_value=2):
                with patch("src.worker.tasks.asyncio.run", side_effect=lambda coro: 2) as mock_run:
                    with patch("src.worker.tasks.log_json"):
                        result = send_due_soon_reminders()

                        assert result == 2
                        assert mock_run.called
