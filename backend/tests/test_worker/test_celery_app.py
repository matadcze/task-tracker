"""Tests for Celery app configuration"""

import pytest
from src.worker.celery_app import celery_app
from src.core.config import settings


class TestCeleryAppConfiguration:
    """Tests for Celery app settings and configuration"""

    def test_celery_app_is_configured(self):
        """Test that Celery app is properly initialized"""
        assert celery_app is not None
        assert celery_app.main == "tasktracker"

    def test_celery_app_broker_url(self):
        """Test that broker URL is set from settings"""
        assert celery_app.conf.broker_url == settings.celery_broker_url

    def test_celery_app_result_backend(self):
        """Test that result backend is set from settings"""
        assert celery_app.conf.result_backend == settings.celery_result_backend

    def test_celery_app_serializer_settings(self):
        """Test that JSON serialization is configured"""
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert "json" in celery_app.conf.accept_content

    def test_celery_app_timezone_settings(self):
        """Test that timezone is set to UTC"""
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True

    def test_celery_app_includes_tasks(self):
        """Test that task modules are included"""
        assert "src.worker.tasks" in celery_app.conf.include

    def test_celery_beat_schedule_configured(self):
        """Test that beat schedule is configured after importing tasks"""
        # Import tasks to trigger beat schedule registration
        import src.worker.tasks  # noqa: F401

        assert hasattr(celery_app.conf, "beat_schedule")
        assert "due-soon-reminders" in celery_app.conf.beat_schedule

    def test_beat_schedule_task_name(self):
        """Test that beat schedule references correct task"""
        # Import tasks to trigger beat schedule registration
        import src.worker.tasks  # noqa: F401

        schedule = celery_app.conf.beat_schedule["due-soon-reminders"]
        assert schedule["task"] == "reminders.send_due_soon"

    def test_beat_schedule_interval(self):
        """Test that beat schedule has crontab interval"""
        # Import tasks to trigger beat schedule registration
        import src.worker.tasks  # noqa: F401

        schedule = celery_app.conf.beat_schedule["due-soon-reminders"]
        assert "schedule" in schedule
        assert schedule["schedule"] is not None
