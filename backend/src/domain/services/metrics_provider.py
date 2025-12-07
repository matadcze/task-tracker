from abc import ABC, abstractmethod

from ..value_objects import TaskStatus


class MetricsProvider(ABC):

    @abstractmethod
    def track_auth_operation(
        self, operation: str, status: str, duration: float | None = None
    ) -> None:

        pass

    @abstractmethod
    def track_task_operation(
        self, operation: str, status: str, duration: float | None = None
    ) -> None:

        pass

    @abstractmethod
    def increment_task_count(self, task_status: TaskStatus) -> None:

        pass

    @abstractmethod
    def decrement_task_count(self, task_status: TaskStatus) -> None:

        pass

    @abstractmethod
    def track_audit_event(self, event_type: str) -> None:

        pass

    @abstractmethod
    def track_attachment_operation(
        self, operation: str, status: str, duration: float | None = None
    ) -> None:

        pass

    @abstractmethod
    def increment_attachment_count(self) -> None:

        pass

    @abstractmethod
    def decrement_attachment_count(self) -> None:

        pass

    @abstractmethod
    def track_attachment_size(self, size_bytes: int) -> None:

        pass
