from src.core.metrics import (
    attachment_operations_total,
    attachment_size_bytes,
    attachment_upload_duration,
    attachments_total,
    audit_events_total,
    auth_operation_duration,
    auth_operations_total,
    task_operation_duration,
    task_operations_total,
    tasks_total,
)
from src.domain.services.metrics_provider import MetricsProvider
from src.domain.value_objects import TaskStatus


class PrometheusMetricsProvider(MetricsProvider):

    def track_auth_operation(
        self, operation: str, status: str, duration: float | None = None
    ) -> None:

        auth_operations_total.labels(operation=operation, status=status).inc()
        if duration is not None:
            auth_operation_duration.labels(operation=operation).observe(duration)

    def track_task_operation(
        self, operation: str, status: str, duration: float | None = None
    ) -> None:

        task_operations_total.labels(operation=operation, status=status).inc()
        if duration is not None:
            task_operation_duration.labels(operation=operation).observe(duration)

    def increment_task_count(self, task_status: TaskStatus) -> None:

        tasks_total.labels(status=task_status.value).inc()

    def decrement_task_count(self, task_status: TaskStatus) -> None:

        tasks_total.labels(status=task_status.value).dec()

    def track_audit_event(self, event_type: str) -> None:

        audit_events_total.labels(event_type=event_type).inc()

    def track_attachment_operation(
        self, operation: str, status: str, duration: float | None = None
    ) -> None:

        attachment_operations_total.labels(operation=operation, status=status).inc()
        if operation == "upload" and duration is not None:
            attachment_upload_duration.observe(duration)

    def increment_attachment_count(self) -> None:

        attachments_total.inc()

    def decrement_attachment_count(self) -> None:

        attachments_total.dec()

    def track_attachment_size(self, size_bytes: int) -> None:

        attachment_size_bytes.observe(size_bytes)
