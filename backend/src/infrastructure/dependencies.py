from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domain.repositories import (
    AttachmentRepository,
    AuditEventRepository,
    TagRepository,
    TaskRepository,
    UserRepository,
)
from src.domain.services import AttachmentService, AuthService, TagService, TaskService
from src.domain.services.metrics_provider import MetricsProvider
from src.domain.services.storage_provider import StorageProvider
from src.infrastructure.database.session import get_db
from src.infrastructure.metrics import PrometheusMetricsProvider
from src.infrastructure.repositories import (
    AttachmentRepositoryImpl,
    AuditEventRepositoryImpl,
    TagRepositoryImpl,
    TaskRepositoryImpl,
    UserRepositoryImpl,
)
from src.infrastructure.storage import LocalFileStorage
from src.infrastructure.repositories.refresh_token_repository import (
    RefreshTokenRepositoryImpl,
)
from src.infrastructure.auth.jwt_provider import JWTProvider
from src.infrastructure.auth.password import PasswordUtils
from src.infrastructure.auth.rate_limiter import get_auth_rate_limiter, AuthRateLimiter


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:

    return UserRepositoryImpl(db)


def get_task_repository(db: AsyncSession = Depends(get_db)) -> TaskRepository:

    return TaskRepositoryImpl(db)


def get_attachment_repository(
    db: AsyncSession = Depends(get_db),
) -> AttachmentRepository:

    return AttachmentRepositoryImpl(db)


def get_audit_repository(db: AsyncSession = Depends(get_db)) -> AuditEventRepository:

    return AuditEventRepositoryImpl(db)


def get_tag_repository(db: AsyncSession = Depends(get_db)) -> TagRepository:

    return TagRepositoryImpl(db)


def get_refresh_token_repository(db: AsyncSession = Depends(get_db)):

    return RefreshTokenRepositoryImpl(db)


def get_metrics_provider() -> MetricsProvider:

    return PrometheusMetricsProvider()


def get_storage_provider() -> StorageProvider:

    return LocalFileStorage()


def get_rate_limiter() -> AuthRateLimiter:

    return get_auth_rate_limiter()


def get_tag_service(
    tag_repo: TagRepository = Depends(get_tag_repository),
) -> TagService:

    return TagService(tag_repo=tag_repo)


def get_task_service(
    task_repo: TaskRepository = Depends(get_task_repository),
    audit_repo: AuditEventRepository = Depends(get_audit_repository),
    tag_service: TagService = Depends(get_tag_service),
    metrics: MetricsProvider = Depends(get_metrics_provider),
) -> TaskService:

    return TaskService(
        task_repo=task_repo, audit_repo=audit_repo, tag_service=tag_service, metrics=metrics
    )


def get_attachment_service(
    attachment_repo: AttachmentRepository = Depends(get_attachment_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
    audit_repo: AuditEventRepository = Depends(get_audit_repository),
    storage: StorageProvider = Depends(get_storage_provider),
    metrics: MetricsProvider = Depends(get_metrics_provider),
) -> AttachmentService:

    return AttachmentService(
        attachment_repo=attachment_repo,
        task_repo=task_repo,
        audit_repo=audit_repo,
        storage=storage,
        metrics=metrics,
        max_file_size_mb=settings.max_upload_size_mb,
    )


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo=Depends(get_refresh_token_repository),
    metrics: MetricsProvider = Depends(get_metrics_provider),
    rate_limiter: AuthRateLimiter = Depends(get_rate_limiter),
) -> AuthService:

    return AuthService(
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
        metrics=metrics,
        jwt_provider=JWTProvider,
        password_utils=PasswordUtils,
        settings=settings,
        rate_limiter=rate_limiter,
    )
