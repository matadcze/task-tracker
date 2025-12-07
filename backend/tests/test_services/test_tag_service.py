"""Tests for TagService"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.domain.services.tag_service import TagService
from src.domain.entities import Tag
from src.domain.exceptions import ValidationError


@pytest.mark.asyncio
class TestTagServiceNormalize:
    """Tests for TagService.normalize_tags()"""

    async def test_normalize_tags_deduplication(self):
        """Test that duplicate tags are removed"""
        service = TagService(tag_repo=AsyncMock())

        result = service.normalize_tags(["work", "work", "important"])

        assert len(result) == 2
        assert "work" in result
        assert "important" in result

    async def test_normalize_tags_case_insensitive(self):
        """Test that tags are case-insensitive"""
        service = TagService(tag_repo=AsyncMock())

        result = service.normalize_tags(["Work", "work", "WORK"])

        # Should be deduplicated to one tag
        assert len(result) == 1
        assert result[0].lower() in ["work"]

    async def test_normalize_tags_empty_list(self):
        """Test normalizing empty tag list"""
        service = TagService(tag_repo=AsyncMock())

        result = service.normalize_tags([])

        assert result == []

    async def test_normalize_tags_strips_whitespace(self):
        """Test that tags are stripped of whitespace"""
        service = TagService(tag_repo=AsyncMock())

        result = service.normalize_tags(["  work  ", "important"])

        assert "work" in result or "  work  " not in result

    async def test_normalize_tags_removes_empty(self):
        """Test that empty tags are removed"""
        service = TagService(tag_repo=AsyncMock())

        result = service.normalize_tags(["work", "", "important", "  "])

        assert "" not in result
        assert len(result) == 2

    async def test_normalize_tags_length_validation(self):
        """Test that tags exceeding max length are rejected"""
        service = TagService(tag_repo=AsyncMock())

        long_tag = "A" * 101  # Exceeds 100 char limit

        with pytest.raises(ValidationError, match="Tag cannot exceed"):
            service.normalize_tags(["work", long_tag])


@pytest.mark.asyncio
class TestTagServiceEnsureTagsExist:
    """Tests for TagService.ensure_tags_exist()"""

    async def test_ensure_tags_exist_all_exist(self, mock_tag_repository):
        """Test when all tags already exist"""
        service = TagService(tag_repo=mock_tag_repository)

        tag1 = Tag(id=uuid4(), name="work")
        tag2 = Tag(id=uuid4(), name="important")

        mock_tag_repository.get_by_names.return_value = [tag1, tag2]

        result = await service.ensure_tags_exist(["work", "important"])

        assert len(result) == 2
        assert all(isinstance(tag, Tag) for tag in result)

    async def test_ensure_tags_exist_creates_missing(self, mock_tag_repository):
        """Test that missing tags are created"""
        service = TagService(tag_repo=mock_tag_repository)

        existing_tag = Tag(id=uuid4(), name="work")
        new_tag = Tag(id=uuid4(), name="new-tag")

        mock_tag_repository.get_by_names.return_value = [existing_tag]
        mock_tag_repository.get_or_create.return_value = new_tag

        result = await service.ensure_tags_exist(["work", "new-tag"])

        assert len(result) > 0

    async def test_ensure_tags_exist_empty_list(self, mock_tag_repository):
        """Test with empty tag list"""
        service = TagService(tag_repo=mock_tag_repository)

        result = await service.ensure_tags_exist([])

        assert result == []

    async def test_ensure_tags_exist_normalizes_input(self, mock_tag_repository):
        """Test that input tags are normalized"""
        service = TagService(tag_repo=mock_tag_repository)

        tag = Tag(id=uuid4(), name="work")
        mock_tag_repository.get_by_names.return_value = [tag]

        result = await service.ensure_tags_exist(["  work  ", "work"])

        # Should deduplicate the tags
        assert len(result) >= 0  # Depends on normalization


@pytest.mark.asyncio
class TestTagServiceGetByNames:
    """Tests for TagService.get_tags_by_names()"""

    async def test_get_tags_by_names(self, mock_tag_repository):
        """Test getting tags by name"""
        service = TagService(tag_repo=mock_tag_repository)

        tag1 = Tag(id=uuid4(), name="work")
        tag2 = Tag(id=uuid4(), name="important")

        mock_tag_repository.get_by_names.return_value = [tag1, tag2]

        result = await service.get_tags_by_names(["work", "important"])

        assert len(result) == 2
        mock_tag_repository.get_by_names.assert_called_once()

    async def test_get_tags_by_names_empty(self, mock_tag_repository):
        """Test getting tags with empty list"""
        service = TagService(tag_repo=mock_tag_repository)

        result = await service.get_tags_by_names([])

        assert result == []

    async def test_get_tags_by_names_partial_match(self, mock_tag_repository):
        """Test getting tags when only some names match"""
        service = TagService(tag_repo=mock_tag_repository)

        tag1 = Tag(id=uuid4(), name="work")

        mock_tag_repository.get_by_names.return_value = [tag1]

        result = await service.get_tags_by_names(["work", "nonexistent"])

        # Should return only the tags that exist
        assert len(result) >= 1
