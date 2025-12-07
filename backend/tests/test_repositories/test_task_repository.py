"""Tests for TaskRepository"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from src.domain.entities import Task
from src.domain.value_objects import TaskStatus, TaskPriority
from src.infrastructure.repositories.task_repository import TaskRepositoryImpl


@pytest.mark.asyncio
class TestTaskRepositoryCreate:
    """Tests for TaskRepository.create()"""

    async def test_create_task(self, db_session: AsyncSession, sample_user_id, sample_task):
        """Test creating a new task"""
        repo = TaskRepositoryImpl(db_session)

        result = await repo.create(sample_task)

        assert result.id == sample_task.id
        assert result.owner_id == sample_task.owner_id
        assert result.title == sample_task.title
        assert result.status == TaskStatus.TODO


@pytest.mark.asyncio
class TestTaskRepositoryGet:
    """Tests for TaskRepository.get_by_id()"""

    async def test_get_task_by_id(self, db_session: AsyncSession, sample_task):
        """Test retrieving task by ID"""
        repo = TaskRepositoryImpl(db_session)

        # Create task
        created = await repo.create(sample_task)

        # Retrieve
        result = await repo.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.title == created.title

    async def test_get_task_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent task"""
        repo = TaskRepositoryImpl(db_session)

        result = await repo.get_by_id(uuid4())

        assert result is None


@pytest.mark.asyncio
class TestTaskRepositoryList:
    """Tests for TaskRepository.list()"""

    async def test_list_tasks_by_owner(self, db_session: AsyncSession, sample_user_id):
        """Test listing tasks for a specific owner"""
        repo = TaskRepositoryImpl(db_session)

        # Create multiple tasks
        task1 = Task(
            owner_id=sample_user_id,
            title="Task 1",
            status=TaskStatus.TODO,
        )
        task2 = Task(
            owner_id=sample_user_id,
            title="Task 2",
            status=TaskStatus.IN_PROGRESS,
        )

        await repo.create(task1)
        await repo.create(task2)

        # List
        result, total = await repo.list(owner_id=sample_user_id)

        assert total >= 2
        assert len(result) >= 2

    async def test_list_tasks_filter_by_status(self, db_session: AsyncSession, sample_user_id):
        """Test listing tasks filtered by status"""
        repo = TaskRepositoryImpl(db_session)

        # Create tasks with different statuses
        task_todo = Task(
            owner_id=sample_user_id,
            title="Todo Task",
            status=TaskStatus.TODO,
        )
        task_done = Task(
            owner_id=sample_user_id,
            title="Done Task",
            status=TaskStatus.DONE,
        )

        await repo.create(task_todo)
        await repo.create(task_done)

        # List only TODO tasks
        result, total = await repo.list(owner_id=sample_user_id, status=TaskStatus.TODO)

        todo_tasks = [t for t in result if t.status == TaskStatus.TODO]
        assert len(todo_tasks) >= 1

    async def test_list_tasks_filter_by_priority(self, db_session: AsyncSession, sample_user_id):
        """Test listing tasks filtered by priority"""
        repo = TaskRepositoryImpl(db_session)

        # Create tasks with different priorities
        task_high = Task(
            owner_id=sample_user_id,
            title="High Priority",
            priority=TaskPriority.HIGH,
        )
        task_low = Task(
            owner_id=sample_user_id,
            title="Low Priority",
            priority=TaskPriority.LOW,
        )

        await repo.create(task_high)
        await repo.create(task_low)

        # List only HIGH priority
        result, total = await repo.list(owner_id=sample_user_id, priority=TaskPriority.HIGH)

        high_tasks = [t for t in result if t.priority == TaskPriority.HIGH]
        assert len(high_tasks) >= 1

    async def test_list_tasks_pagination(self, db_session: AsyncSession, sample_user_id):
        """Test pagination in task list"""
        repo = TaskRepositoryImpl(db_session)

        # Create multiple tasks
        for i in range(5):
            task = Task(
                owner_id=sample_user_id,
                title=f"Task {i}",
            )
            await repo.create(task)

        # Get first page
        result1, total1 = await repo.list(owner_id=sample_user_id, page=1, page_size=2)

        # Get second page
        result2, total2 = await repo.list(owner_id=sample_user_id, page=2, page_size=2)

        assert total1 == total2  # Total should be same
        # Results should be different unless we have exact same amount


@pytest.mark.asyncio
class TestTaskRepositoryUpdate:
    """Tests for TaskRepository.update()"""

    async def test_update_task_title(self, db_session: AsyncSession, sample_task):
        """Test updating task title"""
        repo = TaskRepositoryImpl(db_session)

        # Create
        created = await repo.create(sample_task)

        # Update
        created.title = "Updated Title"
        result = await repo.update(created)

        assert result.title == "Updated Title"

    async def test_update_task_status(self, db_session: AsyncSession, sample_task):
        """Test updating task status"""
        repo = TaskRepositoryImpl(db_session)

        # Create
        created = await repo.create(sample_task)

        # Update status
        created.status = TaskStatus.DONE
        result = await repo.update(created)

        assert result.status == TaskStatus.DONE


@pytest.mark.asyncio
class TestTaskRepositoryDelete:
    """Tests for TaskRepository.delete()"""

    async def test_delete_task(self, db_session: AsyncSession, sample_task):
        """Test deleting a task"""
        repo = TaskRepositoryImpl(db_session)

        # Create
        created = await repo.create(sample_task)

        # Delete
        await repo.delete(created.id)

        # Verify deleted
        result = await repo.get_by_id(created.id)
        assert result is None
