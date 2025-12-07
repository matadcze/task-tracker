"""Tests for AttachmentService"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.domain.services.attachment_service import AttachmentService
from src.domain.entities import Attachment
from src.domain.exceptions import NotFoundError, AuthorizationError, ValidationError


@pytest.mark.asyncio
class TestAttachmentServiceUpload:
    """Tests for AttachmentService.upload_attachment()"""

    async def test_upload_valid_file(
        self,
        sample_user_id,
        sample_task,
        mock_attachment_repository,
        mock_task_repository,
        mock_storage_provider,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test uploading a valid file"""
        service = AttachmentService(
            attachment_repo=mock_attachment_repository,
            task_repo=mock_task_repository,
            storage=mock_storage_provider,
            audit_repo=mock_audit_repository,
            metrics=mock_metrics_provider,
            settings=MagicMock(max_upload_size_mb=10),
        )

        attachment_id = uuid4()
        created_attachment = Attachment(
            id=attachment_id,
            task_id=sample_task.id,
            filename="document.pdf",
            file_path="/uploads/document_123.pdf",
            file_size_bytes=1024,
            mime_type="application/pdf",
            uploaded_by=sample_user_id,
        )

        mock_task_repository.get_by_id.return_value = sample_task
        mock_storage_provider.save_file = AsyncMock(return_value="/uploads/document_123.pdf")
        mock_attachment_repository.create.return_value = created_attachment
        mock_audit_repository.create = AsyncMock()

        file_content = b"PDF content"
        result = await service.upload_attachment(
            task_id=sample_task.id,
            user_id=sample_user_id,
            filename="document.pdf",
            file_content=file_content,
            mime_type="application/pdf",
        )

        assert result.id == attachment_id
        assert result.filename == "document.pdf"
        mock_task_repository.get_by_id.assert_called_once()
        mock_storage_provider.save_file.assert_called_once()
        mock_attachment_repository.create.assert_called_once()

    async def test_upload_unauthorized_user(
        self,
        sample_user_id,
        sample_task,
        sample_user2,
        mock_attachment_repository,
        mock_task_repository,
        mock_storage_provider,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test uploading file to task not owned by user"""
        service = AttachmentService(
            attachment_repo=mock_attachment_repository,
            task_repo=mock_task_repository,
            storage=mock_storage_provider,
            audit_repo=mock_audit_repository,
            metrics=mock_metrics_provider,
            settings=MagicMock(max_upload_size_mb=10),
        )

        mock_task_repository.get_by_id.return_value = sample_task

        with pytest.raises(AuthorizationError, match="Not authorized"):
            await service.upload_attachment(
                task_id=sample_task.id,
                user_id=sample_user2.id,  # Different user
                filename="document.pdf",
                file_content=b"content",
                mime_type="application/pdf",
            )

    async def test_upload_forbidden_extension(
        self,
        sample_user_id,
        sample_task,
        mock_attachment_repository,
        mock_task_repository,
        mock_storage_provider,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test uploading file with forbidden extension"""
        service = AttachmentService(
            attachment_repo=mock_attachment_repository,
            task_repo=mock_task_repository,
            storage=mock_storage_provider,
            audit_repo=mock_audit_repository,
            metrics=mock_metrics_provider,
            settings=MagicMock(max_upload_size_mb=10),
        )

        mock_task_repository.get_by_id.return_value = sample_task

        with pytest.raises(ValidationError, match="not allowed"):
            await service.upload_attachment(
                task_id=sample_task.id,
                user_id=sample_user_id,
                filename="malware.exe",
                file_content=b"executable",
                mime_type="application/x-msdownload",
            )

    async def test_upload_file_too_large(
        self,
        sample_user_id,
        sample_task,
        mock_attachment_repository,
        mock_task_repository,
        mock_storage_provider,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test uploading file exceeding size limit"""
        service = AttachmentService(
            attachment_repo=mock_attachment_repository,
            task_repo=mock_task_repository,
            storage=mock_storage_provider,
            audit_repo=mock_audit_repository,
            metrics=mock_metrics_provider,
            settings=MagicMock(max_upload_size_mb=10),
        )

        mock_task_repository.get_by_id.return_value = sample_task

        # 11 MB file
        large_content = b"x" * (11 * 1024 * 1024)

        with pytest.raises(ValidationError, match="exceeds maximum"):
            await service.upload_attachment(
                task_id=sample_task.id,
                user_id=sample_user_id,
                filename="large.pdf",
                file_content=large_content,
                mime_type="application/pdf",
            )


@pytest.mark.asyncio
class TestAttachmentServiceGet:
    """Tests for AttachmentService.get_attachment()"""

    async def test_get_attachment_success(
        self,
        sample_task,
        sample_attachment,
        mock_attachment_repository,
        mock_task_repository,
        mock_storage_provider,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test getting an attachment"""
        service = AttachmentService(
            attachment_repo=mock_attachment_repository,
            task_repo=mock_task_repository,
            storage=mock_storage_provider,
            audit_repo=mock_audit_repository,
            metrics=mock_metrics_provider,
            settings=MagicMock(),
        )

        # Update sample_attachment to match sample_task
        sample_attachment.task_id = sample_task.id

        mock_attachment_repository.get_by_id.return_value = sample_attachment
        mock_task_repository.get_by_id.return_value = sample_task

        result = await service.get_attachment(
            attachment_id=sample_attachment.id, task_id=sample_task.id, user_id=sample_task.owner_id
        )

        assert result.id == sample_attachment.id
        mock_attachment_repository.get_by_id.assert_called_once()

    async def test_get_attachment_not_found(
        self,
        sample_task,
        mock_attachment_repository,
        mock_task_repository,
        mock_storage_provider,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test getting a non-existent attachment"""
        service = AttachmentService(
            attachment_repo=mock_attachment_repository,
            task_repo=mock_task_repository,
            storage=mock_storage_provider,
            audit_repo=mock_audit_repository,
            metrics=mock_metrics_provider,
            settings=MagicMock(),
        )

        mock_attachment_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Attachment not found"):
            await service.get_attachment(
                attachment_id=uuid4(), task_id=sample_task.id, user_id=sample_task.owner_id
            )

    async def test_get_attachment_unauthorized(
        self,
        sample_task,
        sample_attachment,
        sample_user2,
        mock_attachment_repository,
        mock_task_repository,
        mock_storage_provider,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test getting attachment without permission"""
        service = AttachmentService(
            attachment_repo=mock_attachment_repository,
            task_repo=mock_task_repository,
            storage=mock_storage_provider,
            audit_repo=mock_audit_repository,
            metrics=mock_metrics_provider,
            settings=MagicMock(),
        )

        sample_attachment.task_id = sample_task.id
        mock_attachment_repository.get_by_id.return_value = sample_attachment
        mock_task_repository.get_by_id.return_value = sample_task

        with pytest.raises(AuthorizationError, match="Not authorized"):
            await service.get_attachment(
                attachment_id=sample_attachment.id,
                task_id=sample_task.id,
                user_id=sample_user2.id,  # Different user
            )


@pytest.mark.asyncio
class TestAttachmentServiceList:
    """Tests for AttachmentService.list_attachments()"""

    async def test_list_attachments_success(
        self,
        sample_task,
        sample_attachment,
        mock_attachment_repository,
        mock_task_repository,
        mock_storage_provider,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test listing attachments for a task"""
        service = AttachmentService(
            attachment_repo=mock_attachment_repository,
            task_repo=mock_task_repository,
            storage=mock_storage_provider,
            audit_repo=mock_audit_repository,
            metrics=mock_metrics_provider,
            settings=MagicMock(),
        )

        sample_attachment.task_id = sample_task.id
        mock_attachment_repository.list_by_task.return_value = [sample_attachment]
        mock_task_repository.get_by_id.return_value = sample_task

        result = await service.list_attachments(
            task_id=sample_task.id, user_id=sample_task.owner_id
        )

        assert len(result) == 1
        assert result[0].id == sample_attachment.id

    async def test_list_attachments_empty(
        self,
        sample_task,
        mock_attachment_repository,
        mock_task_repository,
        mock_storage_provider,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test listing attachments when none exist"""
        service = AttachmentService(
            attachment_repo=mock_attachment_repository,
            task_repo=mock_task_repository,
            storage=mock_storage_provider,
            audit_repo=mock_audit_repository,
            metrics=mock_metrics_provider,
            settings=MagicMock(),
        )

        mock_attachment_repository.list_by_task.return_value = []
        mock_task_repository.get_by_id.return_value = sample_task

        result = await service.list_attachments(
            task_id=sample_task.id, user_id=sample_task.owner_id
        )

        assert len(result) == 0


@pytest.mark.asyncio
class TestAttachmentServiceDelete:
    """Tests for AttachmentService.delete_attachment()"""

    async def test_delete_attachment_success(
        self,
        sample_task,
        sample_attachment,
        mock_attachment_repository,
        mock_task_repository,
        mock_storage_provider,
        mock_audit_repository,
        mock_metrics_provider,
    ):
        """Test successful attachment deletion"""
        service = AttachmentService(
            attachment_repo=mock_attachment_repository,
            task_repo=mock_task_repository,
            storage=mock_storage_provider,
            audit_repo=mock_audit_repository,
            metrics=mock_metrics_provider,
            settings=MagicMock(),
        )

        sample_attachment.task_id = sample_task.id
        mock_attachment_repository.get_by_id.return_value = sample_attachment
        mock_task_repository.get_by_id.return_value = sample_task
        mock_attachment_repository.delete = AsyncMock()
        mock_storage_provider.delete_file = AsyncMock()
        mock_audit_repository.create = AsyncMock()

        await service.delete_attachment(
            attachment_id=sample_attachment.id, task_id=sample_task.id, user_id=sample_task.owner_id
        )

        mock_attachment_repository.delete.assert_called_once()
        mock_storage_provider.delete_file.assert_called_once()
        mock_audit_repository.create.assert_called_once()
