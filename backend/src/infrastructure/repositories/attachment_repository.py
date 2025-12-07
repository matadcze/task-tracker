from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Attachment
from src.domain.repositories import AttachmentRepository
from src.infrastructure.database.models import AttachmentModel


class AttachmentRepositoryImpl(AttachmentRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, attachment: Attachment) -> Attachment:

        db_attachment = AttachmentModel(
            id=attachment.id,
            task_id=attachment.task_id,
            filename=attachment.filename,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            storage_path=attachment.storage_path,
            created_at=attachment.created_at,
        )
        self.session.add(db_attachment)
        await self.session.flush()
        await self.session.refresh(db_attachment)
        return Attachment.model_validate(db_attachment)

    async def get_by_id(self, attachment_id: UUID) -> Optional[Attachment]:

        result = await self.session.execute(
            select(AttachmentModel).where(AttachmentModel.id == attachment_id)
        )
        db_attachment = result.scalar_one_or_none()
        return Attachment.model_validate(db_attachment) if db_attachment else None

    async def list_by_task(self, task_id: UUID) -> List[Attachment]:

        result = await self.session.execute(
            select(AttachmentModel).where(AttachmentModel.task_id == task_id)
        )
        db_attachments = result.scalars().all()
        return [Attachment.model_validate(db_att) for db_att in db_attachments]

    async def delete(self, attachment_id: UUID) -> None:

        result = await self.session.execute(
            select(AttachmentModel).where(AttachmentModel.id == attachment_id)
        )
        db_attachment = result.scalar_one_or_none()

        if db_attachment:
            await self.session.delete(db_attachment)
            await self.session.flush()
