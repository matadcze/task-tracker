"""Tests for TaskService"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.domain.services.task_service import TaskService
from src.domain.entities import Task
from src.domain.value_objects import TaskStatus, TaskPriority
from src.domain.exceptions import NotFoundError, AuthorizationError


@pytest.mark.asyncio
class TestTaskServiceCreate:
    """Tests for TaskService.create_task()"""

    async def test_create_task_success(
        self,
        sample_user_id,
        mock_task_repository,
        mock_audit_repository,
        mock_tag_repository,
        mock_metrics_provider,
    ):
        """Test successful task creation"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        task_id = uuid4()
        created_task = Task(
            id=task_id,
            owner_id=sample_user_id,
            title="New Task",
            description="Task description",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
        )

        mock_task_repository.create.return_value = created_task
        mock_audit_repository.create = AsyncMock()

        result = await service.create_task(
            owner_id=sample_user_id,
            title="New Task",
            description="Task description",
            priority=TaskPriority.MEDIUM,
            due_date=None,
            tags=[],
        )

        assert result.id == task_id
        assert result.owner_id == sample_user_id
        assert result.title == "New Task"
        mock_task_repository.create.assert_called_once()
        mock_audit_repository.create.assert_called_once()

    async def test_create_task_empty_title(
        self, sample_user_id, mock_task_repository, mock_audit_repository, mock_metrics_provider
    ):
        """Test creating task with empty title"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        with pytest.raises(ValueError, match="Title cannot be empty"):
            await service.create_task(
                owner_id=sample_user_id,
                title="",
                description="Description",
            )

    async def test_create_task_title_too_long(
        self, sample_user_id, mock_task_repository, mock_audit_repository, mock_metrics_provider
    ):
        """Test creating task with title exceeding max length"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        long_title = "A" * 501

        with pytest.raises(ValueError, match="Title cannot exceed"):
            await service.create_task(
                owner_id=sample_user_id,
                title=long_title,
                description="Description",
            )


@pytest.mark.asyncio
class TestTaskServiceGet:
    """Tests for TaskService.get_task_by_id()"""

    async def test_get_task_success(
        self, sample_task, mock_task_repository, mock_audit_repository, mock_metrics_provider
    ):
        """Test getting a task by ID"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        mock_task_repository.get_by_id.return_value = sample_task

        result = await service.get_task_by_id(task_id=sample_task.id, user_id=sample_task.owner_id)

        assert result.id == sample_task.id
        mock_task_repository.get_by_id.assert_called_once_with(sample_task.id)

    async def test_get_task_not_found(
        self,
        sample_user_id,
        sample_task,
        mock_task_repository,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test getting a non-existent task"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        mock_task_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Task not found"):
            await service.get_task_by_id(task_id=uuid4(), user_id=sample_user_id)

    async def test_get_task_unauthorized(
        self, sample_task, mock_task_repository, mock_audit_repository, mock_metrics_provider
    ):
        """Test getting a task without permission"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        mock_task_repository.get_by_id.return_value = sample_task
        other_user_id = uuid4()

        with pytest.raises(AuthorizationError, match="Not authorized"):
            await service.get_task_by_id(task_id=sample_task.id, user_id=other_user_id)


@pytest.mark.asyncio
class TestTaskServiceList:
    """Tests for TaskService.list_tasks()"""

    async def test_list_tasks_success(
        self,
        sample_user_id,
        sample_task,
        mock_task_repository,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test listing tasks"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        mock_task_repository.list.return_value = ([sample_task], 1)

        result, total = await service.list_tasks(owner_id=sample_user_id, page=1, page_size=20)

        assert len(result) == 1
        assert total == 1
        assert result[0].id == sample_task.id

    async def test_list_tasks_with_filters(
        self,
        sample_user_id,
        sample_task,
        mock_task_repository,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test listing tasks with filters"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        mock_task_repository.list.return_value = ([sample_task], 1)

        result, total = await service.list_tasks(
            owner_id=sample_user_id,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            tags=["work"],
            search="test",
            page=1,
            page_size=20,
        )

        assert len(result) == 1
        mock_task_repository.list.assert_called_once()

    async def test_list_tasks_empty(
        self, sample_user_id, mock_task_repository, mock_audit_repository, mock_metrics_provider
    ):
        """Test listing tasks with no results"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        mock_task_repository.list.return_value = ([], 0)

        result, total = await service.list_tasks(owner_id=sample_user_id, page=1, page_size=20)

        assert len(result) == 0
        assert total == 0


@pytest.mark.asyncio
class TestTaskServiceUpdate:
    """Tests for TaskService.update_task()"""

    async def test_update_task_success(
        self, sample_task, mock_task_repository, mock_audit_repository, mock_metrics_provider
    ):
        """Test successful task update"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        updated_task = Task(
            id=sample_task.id,
            owner_id=sample_task.owner_id,
            title="Updated Task",
            description="Updated description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            tags=["updated"],
        )

        mock_task_repository.get_by_id.return_value = sample_task
        mock_task_repository.update.return_value = updated_task
        mock_audit_repository.create = AsyncMock()

        task, changes = await service.update_task(
            task_id=sample_task.id,
            user_id=sample_task.owner_id,
            title="Updated Task",
            description="Updated description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
        )

        assert task.title == "Updated Task"
        assert len(changes) > 0
        mock_task_repository.update.assert_called_once()
        mock_audit_repository.create.assert_called_once()

    async def test_update_task_unauthorized(
        self, sample_task, mock_task_repository, mock_audit_repository, mock_metrics_provider
    ):
        """Test updating a task without permission"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        mock_task_repository.get_by_id.return_value = sample_task
        other_user_id = uuid4()

        with pytest.raises(AuthorizationError, match="Not authorized"):
            await service.update_task(
                task_id=sample_task.id, user_id=other_user_id, title="Updated"
            )


@pytest.mark.asyncio
class TestTaskServiceDelete:
    """Tests for TaskService.delete_task()"""

    async def test_delete_task_success(
        self, sample_task, mock_task_repository, mock_audit_repository, mock_metrics_provider
    ):
        """Test successful task deletion"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        mock_task_repository.get_by_id.return_value = sample_task
        mock_task_repository.delete = AsyncMock()
        mock_audit_repository.create = AsyncMock()

        await service.delete_task(task_id=sample_task.id, user_id=sample_task.owner_id)

        mock_task_repository.delete.assert_called_once_with(sample_task.id)
        mock_audit_repository.create.assert_called_once()

    async def test_delete_task_unauthorized(
        self, sample_task, mock_task_repository, mock_audit_repository, mock_metrics_provider
    ):
        """Test deleting a task without permission"""
        service = TaskService(
            task_repo=mock_task_repository,
            audit_repo=mock_audit_repository,
            tag_service=MagicMock(),
            metrics=mock_metrics_provider,
        )

        mock_task_repository.get_by_id.return_value = sample_task
        other_user_id = uuid4()

        with pytest.raises(AuthorizationError, match="Not authorized"):
            await service.delete_task(task_id=sample_task.id, user_id=other_user_id)
