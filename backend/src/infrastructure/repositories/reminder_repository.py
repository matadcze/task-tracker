from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import ReminderLog
from src.domain.repositories import ReminderLogRepository
from src.domain.value_objects import ReminderType
from src.infrastructure.database.models import ReminderLogModel
from src.core.metrics import reminders_processed_total


class ReminderLogRepositoryImpl(ReminderLogRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, reminder: ReminderLog) -> ReminderLog:

        db_reminder = ReminderLogModel(
            id=reminder.id,
            task_id=reminder.task_id,
            reminder_type=reminder.reminder_type,
            sent_at=reminder.sent_at,
        )
        self.session.add(db_reminder)
        await self.session.flush()
        await self.session.refresh(db_reminder)
        reminders_processed_total.labels(type=reminder.reminder_type.value, status="success").inc()
        return ReminderLog.model_validate(db_reminder)

    async def get_by_task_and_type(
        self, task_id: UUID, reminder_type: ReminderType
    ) -> Optional[ReminderLog]:

        result = await self.session.execute(
            select(ReminderLogModel).where(
                ReminderLogModel.task_id == task_id,
                ReminderLogModel.reminder_type == reminder_type,
            )
        )
        db_reminder = result.scalar_one_or_none()
        return ReminderLog.model_validate(db_reminder) if db_reminder else None
