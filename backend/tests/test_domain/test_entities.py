"""Tests for domain entities"""

from datetime import timedelta
from src.core.time import utc_now
from uuid import uuid4

from src.domain.entities import User, Task, Attachment
from src.domain.value_objects import TaskStatus, TaskPriority
from src.infrastructure.auth.password import PasswordUtils


class TestUserEntity:
    """Tests for User entity behavior"""

    def test_user_creation(self, sample_user):
        """Test creating a user"""
        assert sample_user.email == "test@example.com"
        assert sample_user.full_name == "Test User"
        assert sample_user.is_active is True

    def test_can_authenticate_active_user(self, sample_user):
        """Test that active user can authenticate"""
        assert sample_user.can_authenticate() is True

    def test_can_authenticate_inactive_user(self):
        """Test that inactive user cannot authenticate"""
        user = User(
            id=uuid4(),
            email="inactive@example.com",
            password_hash=PasswordUtils.hash_password("Password123"),
            full_name="Inactive User",
            is_active=False,
        )
        assert user.can_authenticate() is False

    def test_can_be_accessed_by_owner(self, sample_user):
        """Test user can be accessed by themselves"""
        assert sample_user.can_be_accessed_by(sample_user.id) is True

    def test_can_be_accessed_by_other_user(self, sample_user):
        """Test user cannot be accessed by other user"""
        other_user_id = uuid4()
        assert sample_user.can_be_accessed_by(other_user_id) is False


class TestTaskEntity:
    """Tests for Task entity behavior"""

    def test_task_creation(self, sample_task):
        """Test creating a task"""
        assert sample_task.title == "Test Task"
        assert sample_task.status == TaskStatus.TODO
        assert sample_task.priority == TaskPriority.MEDIUM
        assert len(sample_task.tags) == 2

    def test_is_overdue_with_future_due_date(self, sample_task):
        """Test that task with future due date is not overdue"""
        assert sample_task.is_overdue() is False

    def test_is_overdue_with_past_due_date(self, sample_task_overdue):
        """Test that task with past due date is overdue"""
        assert sample_task_overdue.is_overdue() is True

    def test_is_overdue_done_task_is_not_overdue(self):
        """Test that done task is never overdue, even with past due date"""
        task = Task(
            id=uuid4(),
            owner_id=uuid4(),
            title="Done Task",
            status=TaskStatus.DONE,
            due_date=utc_now() - timedelta(days=1),
        )
        assert task.is_overdue() is False

    def test_is_overdue_with_no_due_date(self):
        """Test that task without due date is never overdue"""
        task = Task(
            id=uuid4(),
            owner_id=uuid4(),
            title="No Due Date",
            status=TaskStatus.TODO,
            due_date=None,
        )
        assert task.is_overdue() is False

    def test_can_be_modified_by_owner(self, sample_task):
        """Test that task can be modified by owner"""
        assert sample_task.can_be_modified_by(sample_task.owner_id) is True

    def test_can_be_modified_by_non_owner(self, sample_task):
        """Test that task cannot be modified by non-owner"""
        other_user_id = uuid4()
        assert sample_task.can_be_modified_by(other_user_id) is False

    def test_can_be_viewed_by_owner(self, sample_task):
        """Test that task can be viewed by owner"""
        assert sample_task.can_be_viewed_by(sample_task.owner_id) is True

    def test_can_be_viewed_by_non_owner(self, sample_task):
        """Test that task cannot be viewed by non-owner"""
        other_user_id = uuid4()
        assert sample_task.can_be_viewed_by(other_user_id) is False

    def test_mark_as_done(self, sample_task):
        """Test marking task as done"""
        original_updated_at = sample_task.updated_at
        sample_task.mark_as_done()

        assert sample_task.status == TaskStatus.DONE
        assert sample_task.updated_at > original_updated_at

    def test_mark_as_in_progress(self, sample_task):
        """Test marking task as in progress"""
        original_updated_at = sample_task.updated_at
        sample_task.mark_as_in_progress()

        assert sample_task.status == TaskStatus.IN_PROGRESS
        assert sample_task.updated_at > original_updated_at

    def test_add_tag_new(self, sample_task):
        """Test adding a new tag to task"""
        initial_tag_count = len(sample_task.tags)
        result = sample_task.add_tag("new-tag")

        assert result is True
        assert len(sample_task.tags) == initial_tag_count + 1
        assert "new-tag" in sample_task.tags

    def test_add_tag_duplicate(self, sample_task):
        """Test adding a duplicate tag returns False"""
        result = sample_task.add_tag("work")

        assert result is False
        assert sample_task.tags.count("work") == 1

    def test_remove_tag_existing(self, sample_task):
        """Test removing an existing tag"""
        result = sample_task.remove_tag("work")

        assert result is True
        assert "work" not in sample_task.tags
        assert "important" in sample_task.tags

    def test_remove_tag_non_existing(self, sample_task):
        """Test removing a non-existing tag returns False"""
        result = sample_task.remove_tag("non-existing")

        assert result is False

    def test_has_tag_existing(self, sample_task):
        """Test checking if task has a specific tag"""
        assert sample_task.has_tag("work") is True

    def test_has_tag_non_existing(self, sample_task):
        """Test checking if task has non-existing tag"""
        assert sample_task.has_tag("non-existing") is False

    def test_add_tag_updates_timestamp(self, sample_task):
        """Test that adding tag updates the updated_at timestamp"""
        original_time = sample_task.updated_at
        sample_task.add_tag("test-tag")

        assert sample_task.updated_at > original_time


class TestAttachmentEntity:
    """Tests for Attachment entity behavior"""

    def test_attachment_creation(self, sample_attachment):
        """Test creating an attachment"""
        assert sample_attachment.filename == "test.pdf"
        assert sample_attachment.content_type == "application/pdf"
        assert sample_attachment.size_bytes == 1024

    def test_is_for_task_matching(self, sample_attachment):
        """Test checking if attachment is for a specific task"""
        assert sample_attachment.is_for_task(sample_attachment.task_id) is True

    def test_is_for_task_non_matching(self, sample_attachment):
        """Test checking if attachment is for a different task"""
        other_task_id = uuid4()
        assert sample_attachment.is_for_task(other_task_id) is False

    def test_is_image_pdf(self, sample_attachment):
        """Test that PDF is not detected as image"""
        assert sample_attachment.is_image() is False

    def test_is_image_jpg(self):
        """Test that JPG is detected as image"""
        attachment = Attachment(
            id=uuid4(),
            task_id=uuid4(),
            filename="image.jpg",
            content_type="image/jpeg",
            size_bytes=5120,
            storage_path="/uploads/image.jpg",
        )
        assert attachment.is_image() is True

    def test_is_image_png(self):
        """Test that PNG is detected as image"""
        attachment = Attachment(
            id=uuid4(),
            task_id=uuid4(),
            filename="image.png",
            content_type="image/png",
            size_bytes=8192,
            storage_path="/uploads/image.png",
        )
        assert attachment.is_image() is True

    def test_is_document_pdf(self, sample_attachment):
        """Test that PDF is detected as document"""
        assert sample_attachment.is_document() is True

    def test_is_document_docx(self):
        """Test that DOCX is detected as document"""
        attachment = Attachment(
            id=uuid4(),
            task_id=uuid4(),
            filename="document.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=10240,
            storage_path="/uploads/document.docx",
        )
        assert attachment.is_document() is True

    def test_is_document_image(self):
        """Test that image is not detected as document"""
        attachment = Attachment(
            id=uuid4(),
            task_id=uuid4(),
            filename="image.jpg",
            content_type="image/jpeg",
            size_bytes=5120,
            storage_path="/uploads/image.jpg",
        )
        assert attachment.is_document() is False

    def test_size_in_mb(self, sample_attachment):
        """Test file size conversion to MB"""
        # 1024 bytes = 0.001 MB (rounded to 0.0 with 2 decimal places)
        # Using a larger attachment for testing
        large_attachment = Attachment(
            id=uuid4(),
            task_id=uuid4(),
            filename="large.pdf",
            content_type="application/pdf",
            size_bytes=1024 * 100,  # 100 KB
            storage_path="/uploads/large.pdf",
        )
        size_mb = large_attachment.size_in_mb()
        assert size_mb > 0

    def test_size_in_mb_large_file(self):
        """Test file size conversion for larger file"""
        # 1 MB = 1048576 bytes
        attachment = Attachment(
            id=uuid4(),
            task_id=uuid4(),
            filename="large.pdf",
            content_type="application/pdf",
            size_bytes=1048576,  # 1 MB
            storage_path="/uploads/large.pdf",
        )
        # Should be close to 1.0 MB
        assert 0.9 < attachment.size_in_mb() < 1.1
