from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import AuditEvent
from src.domain.repositories import AuditEventRepository
from src.domain.value_objects import EventType
from src.infrastructure.database.models import AuditEventModel


class AuditEventRepositoryImpl(AuditEventRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event: AuditEvent) -> AuditEvent:

        db_event = AuditEventModel(
            id=event.id,
            user_id=event.user_id,
            event_type=event.event_type,
            task_id=event.task_id,
            attachment_id=event.attachment_id,
            details=event.details,
            created_at=event.created_at,
        )
        self.session.add(db_event)
        await self.session.flush()
        await self.session.refresh(db_event)
        return AuditEvent.model_validate(db_event)

    async def list(
        self,
        user_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        event_type: Optional[EventType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditEvent], int]:

        query = select(AuditEventModel)

        filters = []
        if user_id:
            filters.append(AuditEventModel.user_id == user_id)
        if task_id:
            filters.append(AuditEventModel.task_id == task_id)
        if event_type:
            filters.append(AuditEventModel.event_type == event_type)
        if from_date:
            filters.append(AuditEventModel.created_at >= from_date)
        if to_date:
            filters.append(AuditEventModel.created_at <= to_date)

        if filters:
            query = query.where(and_(*filters))

        count_query = select(func.count()).select_from(AuditEventModel)
        if filters:
            count_query = count_query.where(and_(*filters))

        result = await self.session.execute(count_query)
        total = result.scalar()

        query = query.order_by(desc(AuditEventModel.created_at))
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        db_events = result.scalars().all()

        events = [AuditEvent.model_validate(db_event) for db_event in db_events]
        return events, total
