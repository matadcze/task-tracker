import re
from dataclasses import dataclass
from typing import Optional, Protocol
from uuid import UUID

from src.domain.entities import Task
from src.domain.exceptions import ValidationError
from src.domain.services.task_service import TaskService


@dataclass
class ChatMessageResult:
    reply: str
    created_task: Optional[Task] = None


@dataclass
class TaskInterpretation:
    title: str
    description: Optional[str] = None


class TaskInterpreter(Protocol):
    async def interpret(self, message: str) -> Optional[TaskInterpretation]:
        ...


@dataclass
class SafetyCheckResult:
    flagged: bool
    reason: Optional[str] = None


class SafetyChecker(Protocol):
    async def check(self, message: str) -> SafetyCheckResult:
        ...


class ChatService:
    def __init__(
        self,
        task_service: TaskService,
        interpreter: Optional[TaskInterpreter] = None,
        safety_checker: Optional[SafetyChecker] = None,
    ):
        self.task_service = task_service
        self.interpreter = interpreter
        self.safety_checker = safety_checker

    async def _extract_task(self, message: str) -> TaskInterpretation:
        if not message or not message.strip():
            raise ValidationError("Message cannot be empty")

        normalized = " ".join(message.strip().split())

        if self.interpreter:
            try:
                interpreted = await self.interpreter.interpret(normalized)
                if interpreted and interpreted.title:
                    cleaned_title = self._clean_title(interpreted.title)
                    if cleaned_title:
                        description = interpreted.description or None
                        return TaskInterpretation(
                            title=cleaned_title,
                            description=description.strip() if description else None,
                        )
            except Exception:
                pass

        title = None
        patterns = [
            r"add\s+(?:a\s+)?task\s+(?:to\s+)?(?P<title>.+)",
            r"create\s+(?:a\s+)?task\s+(?:to\s+)?(?P<title>.+)",
            r"new\s+task[:\-]?\s+(?P<title>.+)",
            r"task[:\-]\s*(?P<title>.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if match:
                title = match.group("title")
                break

        if title is None:
            title = normalized

        title = self._clean_title(title)

        if not title:
            raise ValidationError("Could not determine a task title from the message")

        description = normalized if normalized != title else None

        return TaskInterpretation(title=title, description=description)

    @staticmethod
    def _clean_title(title: str) -> str:
        cleaned = title.strip().strip('"\'.').rstrip(".! ")
        if cleaned.lower().startswith("to "):
            cleaned = cleaned[3:].lstrip()
        return cleaned

    async def create_task_from_message(self, user_id: UUID, message: str) -> ChatMessageResult:
        if self.safety_checker:
            safety = await self.safety_checker.check(message)
            if safety.flagged:
                reason = safety.reason or "Message failed safety checks"
                raise ValidationError(reason)

        interpretation = await self._extract_task(message)
        task = await self.task_service.create_task(
            owner_id=user_id,
            title=interpretation.title,
            description=interpretation.description,
        )
        reply = f'Created a task titled "{task.title}" with default settings.'

        return ChatMessageResult(reply=reply, created_task=task)
