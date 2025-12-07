from typing import List, Optional

from ..entities import Tag
from ..exceptions import ValidationError
from ..repositories import TagRepository


class TagService:
    MAX_TAG_LENGTH = 100

    def __init__(self, tag_repo: TagRepository):
        self.tag_repo = tag_repo

    def normalize_tags(self, tags: Optional[List[str]]) -> List[str]:
        if tags is None:
            return []

        normalized_tags: List[str] = []
        seen_tags = set()

        for tag in tags:
            if tag is None:
                continue

            normalized_tag = tag.strip()
            if not normalized_tag:
                continue

            if len(normalized_tag) > self.MAX_TAG_LENGTH:
                raise ValidationError(f"Tag cannot exceed {self.MAX_TAG_LENGTH} characters")

            dedupe_key = normalized_tag.lower()
            if dedupe_key not in seen_tags:
                seen_tags.add(dedupe_key)
                normalized_tags.append(normalized_tag)

        return normalized_tags

    async def ensure_tags_exist(self, tags: Optional[List[str]]) -> List[Tag]:
        normalized_tags = self.normalize_tags(tags)

        if not normalized_tags:
            return []

        existing = {
            tag.name.lower(): tag for tag in await self.tag_repo.get_by_names(normalized_tags)
        }
        result: List[Tag] = []

        for tag_name in normalized_tags:
            existing_tag = existing.get(tag_name.lower())
            if existing_tag:
                result.append(existing_tag)
            else:
                created = await self.tag_repo.get_or_create(tag_name)
                result.append(created)

        return result

    async def get_tags_by_names(self, names: List[str]) -> List[Tag]:
        normalized_names = self.normalize_tags(names)

        if not normalized_names:
            return []

        return await self.tag_repo.get_by_names(normalized_names)
