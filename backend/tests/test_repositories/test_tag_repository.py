"""Tests for TagRepository"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.repositories.tag_repository import TagRepositoryImpl


@pytest.mark.asyncio
class TestTagRepositoryGetOrCreate:
    """Tests for TagRepository.get_or_create()"""

    async def test_get_or_create_new_tag(self, db_session: AsyncSession):
        """Test creating a new tag"""
        repo = TagRepositoryImpl(db_session)

        result = await repo.get_or_create("work")

        assert result.name == "work"

    async def test_get_or_create_existing_tag(self, db_session: AsyncSession):
        """Test retrieving an existing tag"""
        repo = TagRepositoryImpl(db_session)

        # Create first
        created = await repo.get_or_create("work")
        created_id = created.id

        # Get again
        result = await repo.get_or_create("work")

        assert result.id == created_id
        assert result.name == "work"

    async def test_get_or_create_multiple_tags(self, db_session: AsyncSession):
        """Test creating multiple different tags"""
        repo = TagRepositoryImpl(db_session)

        tag1 = await repo.get_or_create("work")
        tag2 = await repo.get_or_create("personal")
        tag3 = await repo.get_or_create("urgent")

        assert tag1.id != tag2.id
        assert tag2.id != tag3.id
        assert tag1.name == "work"
        assert tag2.name == "personal"
        assert tag3.name == "urgent"


@pytest.mark.asyncio
class TestTagRepositoryGetByNames:
    """Tests for TagRepository.get_by_names()"""

    async def test_get_by_names_existing(self, db_session: AsyncSession):
        """Test getting tags by names"""
        repo = TagRepositoryImpl(db_session)

        # Create tags
        tag1 = await repo.get_or_create("work")
        tag2 = await repo.get_or_create("personal")

        # Get by names
        result = await repo.get_by_names(["work", "personal"])

        assert len(result) >= 2
        tag_names = [t.name for t in result]
        assert "work" in tag_names
        assert "personal" in tag_names

    async def test_get_by_names_empty_list(self, db_session: AsyncSession):
        """Test getting tags with empty list"""
        repo = TagRepositoryImpl(db_session)

        result = await repo.get_by_names([])

        assert result == []

    async def test_get_by_names_partial_match(self, db_session: AsyncSession):
        """Test getting tags when only some exist"""
        repo = TagRepositoryImpl(db_session)

        # Create one tag
        await repo.get_or_create("work")

        # Get by names (one exists, one doesn't)
        result = await repo.get_by_names(["work", "nonexistent"])

        # Should return only the existing one
        assert len(result) >= 1
        tag_names = [t.name for t in result]
        assert "work" in tag_names
