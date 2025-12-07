from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Tag
from src.domain.repositories import TagRepository
from src.infrastructure.database.models import TagModel


class TagRepositoryImpl(TagRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, name: str) -> Tag:

        result = await self.session.execute(select(TagModel).where(TagModel.name == name))
        db_tag = result.scalar_one_or_none()

        if db_tag is None:
            db_tag = TagModel(name=name)
            self.session.add(db_tag)
            await self.session.flush()

        return self._to_entity(db_tag)

    async def get_by_names(self, names: List[str]) -> List[Tag]:

        if not names:
            return []

        result = await self.session.execute(select(TagModel).where(TagModel.name.in_(names)))
        db_tags = result.scalars().all()

        return [self._to_entity(db_tag) for db_tag in db_tags]

    @staticmethod
    def _to_entity(db_tag: TagModel) -> Tag:

        return Tag(id=db_tag.id, name=db_tag.name)
