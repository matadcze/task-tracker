import secrets
import time
import unicodedata
import inspect
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from ..entities import Attachment, AuditEvent
from ..exceptions import AuthorizationError, NotFoundError, ValidationError
from ..repositories import AttachmentRepository, AuditEventRepository, TaskRepository
from ..value_objects import EventType
from .metrics_provider import MetricsProvider
from .storage_provider import StorageProvider


class AttachmentService:
    ALLOWED_CONTENT_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/csv",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        "application/zip",
        "application/x-7z-compressed",
        "application/x-tar",
        "application/gzip",
        "application/json",
        "application/xml",
        "application/octet-stream",
    }

    FORBIDDEN_EXTENSIONS = {
        ".exe",
        ".dll",
        ".bat",
        ".cmd",
        ".sh",
        ".ps1",
        ".scr",
        ".com",
        ".pif",
        ".vbs",
        ".js",
        ".jar",
    }

    # Allowed file extensions (whitelist approach)
    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".csv",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".zip",
        ".7z",
        ".tar",
        ".gz",
        ".json",
        ".xml",
    }

    def __init__(
        self,
        attachment_repo: AttachmentRepository,
        task_repo: TaskRepository,
        audit_repo: AuditEventRepository,
        storage: StorageProvider,
        metrics: MetricsProvider,
        max_file_size_mb: Optional[int] = None,
        settings: Optional[object] = None,
    ):
        self.attachment_repo = attachment_repo
        self.task_repo = task_repo
        self.audit_repo = audit_repo
        self.storage = storage
        self.metrics = metrics
        resolved_max_mb = (
            max_file_size_mb
            if max_file_size_mb is not None
            else getattr(settings, "max_upload_size_mb", 10)
        )
        self.max_file_size_bytes = resolved_max_mb * 1024 * 1024

    async def upload_attachment(
        self,
        task_id: UUID,
        user_id: UUID,
        filename: str,
        file_content: bytes,
        mime_type: str,
    ) -> Attachment:
        start_time = time.time()

        try:
            task = await self.task_repo.get_by_id(task_id)
            if not task:
                raise NotFoundError("Task not found")

            if not task.can_be_modified_by(user_id):
                raise AuthorizationError("Not authorized")

            # Sanitize filename
            original_filename = self._sanitize_filename(filename)

            if not original_filename:
                raise ValidationError("Filename cannot be empty")

            file_extension = Path(original_filename).suffix.lower()

            # Check forbidden extensions
            if file_extension in self.FORBIDDEN_EXTENSIONS:
                raise ValidationError(
                    f"File type '{file_extension}' is not allowed for security reasons"
                )

            # Check allowed extensions (whitelist)
            if file_extension and file_extension not in self.ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f"File type '{file_extension}' is not permitted. "
                    f"Allowed types: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
                )

            if len(original_filename) > 255:
                raise ValidationError("Filename cannot exceed 255 characters")

            normalized_content_type = mime_type or "application/octet-stream"

            # Validate content-type against whitelist
            if normalized_content_type not in self.ALLOWED_CONTENT_TYPES:
                raise ValidationError(f"Content type '{normalized_content_type}' is not allowed")

            file_size = len(file_content or b"")

            if file_size == 0:
                raise ValidationError("File cannot be empty")

            if file_size > self.max_file_size_bytes:
                max_size_mb = self.max_file_size_bytes / (1024 * 1024)
                raise ValidationError(
                    f"File size ({file_size / (1024 * 1024):.2f}MB) exceeds maximum allowed size of {max_size_mb}MB"
                )

            existing_attachments = await self.attachment_repo.list_by_task(task_id)
            if len(existing_attachments) >= 50:
                raise ValidationError("Maximum number of attachments (50) reached for this task")

            # Generate safe storage filename to prevent directory traversal
            safe_filename = self._generate_safe_filename(original_filename)
            storage_path = await self.storage.save_file(BytesIO(file_content), safe_filename)

            attachment = Attachment(
                task_id=task_id,
                filename=original_filename,  # Store original for display
                storage_path=storage_path,
                content_type=normalized_content_type,
                size_bytes=file_size,
            )

            created_attachment = await self.attachment_repo.create(attachment)

            await self.audit_repo.create(
                AuditEvent(
                    user_id=user_id,
                    event_type=EventType.ATTACHMENT_ADDED,
                    task_id=task_id,
                    attachment_id=created_attachment.id,
                    details={
                        "filename": filename,
                        "size_bytes": file_size,
                        "content_type": normalized_content_type,
                    },
                )
            )

            duration = time.time() - start_time
            self.metrics.track_attachment_operation("upload", "success", duration)
            self.metrics.increment_attachment_count()
            self.metrics.track_attachment_size(file_size)
            self.metrics.track_audit_event(EventType.ATTACHMENT_ADDED.value)

            return created_attachment

        except (ValidationError, NotFoundError, AuthorizationError):
            duration = time.time() - start_time
            self.metrics.track_attachment_operation("upload", "error", duration)
            raise
        except Exception:
            duration = time.time() - start_time
            self.metrics.track_attachment_operation("upload", "error", duration)
            raise

    async def list_attachments(self, task_id: UUID, user_id: UUID) -> List[Attachment]:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found")

        allowed = task.can_be_viewed_by(user_id)
        if inspect.isawaitable(allowed):
            allowed = await allowed
        if not allowed:
            raise AuthorizationError("Not authorized")

        attachments = await self.attachment_repo.list_by_task(task_id)
        return attachments

    async def get_attachment(self, task_id: UUID, attachment_id: UUID, user_id: UUID) -> Attachment:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found")

        allowed = task.can_be_viewed_by(user_id)
        if inspect.isawaitable(allowed):
            allowed = await allowed
        if not allowed:
            raise AuthorizationError("Not authorized")

        attachment = await self.attachment_repo.get_by_id(attachment_id)
        if not attachment or not attachment.is_for_task(task_id):
            raise NotFoundError("Attachment not found")

        return attachment

    async def get_attachment_file_path(
        self, task_id: UUID, attachment_id: UUID, user_id: UUID
    ) -> tuple[Path, Attachment]:
        attachment = await self.get_attachment(task_id, attachment_id, user_id)

        if not await self.storage.file_exists(attachment.storage_path):
            raise NotFoundError("File not found in storage. It may have been deleted or corrupted.")

        file_path = await self.storage.get_file_path(attachment.storage_path)

        return file_path, attachment

    async def delete_attachment(self, task_id: UUID, attachment_id: UUID, user_id: UUID) -> None:
        start_time = time.time()

        try:
            attachment = await self.get_attachment(task_id, attachment_id, user_id)

            await self.audit_repo.create(
                AuditEvent(
                    user_id=user_id,
                    event_type=EventType.ATTACHMENT_REMOVED,
                    task_id=task_id,
                    attachment_id=attachment_id,
                    details={
                        "filename": attachment.filename,
                        "size_bytes": attachment.size_bytes,
                        "content_type": attachment.content_type,
                    },
                )
            )

            try:
                await self.storage.delete_file(attachment.storage_path)
            except Exception:
                pass

            await self.attachment_repo.delete(attachment_id)

            duration = time.time() - start_time
            self.metrics.track_attachment_operation("delete", "success", duration)
            self.metrics.decrement_attachment_count()
            self.metrics.track_audit_event(EventType.ATTACHMENT_REMOVED.value)

        except (NotFoundError, AuthorizationError):
            duration = time.time() - start_time
            self.metrics.track_attachment_operation("delete", "error", duration)
            raise
        except Exception:
            duration = time.time() - start_time
            self.metrics.track_attachment_operation("delete", "error", duration)
            raise

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and other attacks.

        Args:
            filename: Original filename from client

        Returns:
            Sanitized filename with path components removed
        """
        if not filename:
            return ""

        # Strip whitespace
        filename = filename.strip()

        # Extract basename only (removes any path components)
        filename = Path(filename).name

        # Normalize unicode to prevent lookalike attacks
        filename = unicodedata.normalize("NFKC", filename)

        # Remove any null bytes
        filename = filename.replace("\x00", "")

        return filename

    @staticmethod
    def _generate_safe_filename(original_filename: str) -> str:
        """
        Generate a safe storage filename using UUID to prevent collisions and attacks.

        Args:
            original_filename: Original sanitized filename

        Returns:
            Safe filename for storage (UUID-based with original extension)
        """
        file_ext = Path(original_filename).suffix.lower()
        # Use cryptographically secure random hex string
        safe_filename = f"{secrets.token_hex(16)}{file_ext}"
        return safe_filename
