from datetime import timedelta
import logging

from src.core.time import utc_now
from src.domain.entities import AuditEvent, ReminderLog
from src.domain.repositories import (
    AuditEventRepository,
    ReminderLogRepository,
    TaskRepository,
)
from src.domain.value_objects import EventType, ReminderType
from .metrics_provider import MetricsProvider

logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(
        self,
        task_repo: TaskRepository,
        reminder_repo: ReminderLogRepository,
        audit_repo: AuditEventRepository,
        metrics: MetricsProvider,
    ):
        self.task_repo = task_repo
        self.reminder_repo = reminder_repo
        self.audit_repo = audit_repo
        self.metrics = metrics

    async def send_due_soon_reminders(self, window_hours: int = 24) -> int:
        """Send reminders for tasks due within the next window_hours.

        Idempotent: skips tasks with existing reminder logs of type DUE_SOON.
        """
        now = utc_now()
        window_end = now + timedelta(hours=window_hours)

        tasks = await self.task_repo.list_due_between(now, window_end)
        processed = 0

        for task in tasks:
            existing = await self.reminder_repo.get_by_task_and_type(task.id, ReminderType.DUE_SOON)
            if existing:
                continue

            reminder = ReminderLog(
                task_id=task.id,
                reminder_type=ReminderType.DUE_SOON,
                sent_at=utc_now(),
            )

            try:
                await self.reminder_repo.create(reminder)
                await self.audit_repo.create(
                    AuditEvent(
                        user_id=task.owner_id,
                        event_type=EventType.REMINDER_SENT,
                        task_id=task.id,
                        details={"due_date": task.due_date.isoformat() if task.due_date else None},
                    )
                )
                self.metrics.track_audit_event(EventType.REMINDER_SENT.value)
                processed += 1
            except Exception as exc:
                logger.exception(
                    "Failed to record reminder", extra={"task_id": str(task.id), "error": str(exc)}
                )
                continue

        return processed
