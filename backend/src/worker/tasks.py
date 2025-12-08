import asyncio

from celery.schedules import crontab

from src.core.config import settings
from src.core.logging import configure_logging, log_json
from src.core.time import utc_now
from src.domain.services.reminder_service import ReminderService
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.metrics import PrometheusMetricsProvider
from src.infrastructure.repositories import (
    AuditEventRepositoryImpl,
    ReminderLogRepositoryImpl,
    TaskRepositoryImpl,
)
from .celery_app import celery_app


async def _run_reminders(window_hours: int) -> int:
    async with AsyncSessionLocal() as session:
        try:
            task_repo = TaskRepositoryImpl(session)
            reminder_repo = ReminderLogRepositoryImpl(session)
            audit_repo = AuditEventRepositoryImpl(session)
            metrics = PrometheusMetricsProvider()
            service = ReminderService(task_repo, reminder_repo, audit_repo, metrics)
            processed = await service.send_due_soon_reminders(window_hours=window_hours)
            await session.commit()
            return processed
        except Exception:
            await session.rollback()
            raise


@celery_app.task(name="reminders.send_due_soon")
def send_due_soon_reminders() -> int:
    """Celery task entrypoint for due-soon reminders (idempotent)."""
    configure_logging()
    window_hours = 24
    processed = asyncio.run(_run_reminders(window_hours=window_hours))
    log_json(
        celery_app.log.get_default_logger(),
        "reminders.sent",
        count=processed,
        window_hours=window_hours,
        at=str(utc_now()),
    )
    return processed


# Beat schedule: run every reminder_check_interval_minutes
celery_app.conf.beat_schedule = {
    "due-soon-reminders": {
        "task": "reminders.send_due_soon",
        "schedule": crontab(minute=f"*/{settings.reminder_check_interval_minutes}"),
    }
}
