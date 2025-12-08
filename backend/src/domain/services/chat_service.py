from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.domain.entities import Task
from src.domain.exceptions import ValidationError
from src.domain.services.chat_interpreter import (
    TaskInterpreter,
    TaskInterpretation,
    RegexTaskInterpreter,
)
from src.domain.services.task_service import TaskService


@dataclass
class ChatMessageResult:
    reply: str
    created_task: Optional[Task] = None


@dataclass
class SafetyCheckResult:
    flagged: bool
    reason: Optional[str] = None


class SafetyChecker:
    async def check(self, message: str) -> SafetyCheckResult:
        raise NotImplementedError


class ChatService:
    def __init__(
        self,
        task_service: TaskService,
        interpreter: Optional[TaskInterpreter] = None,
        safety_checker: Optional[SafetyChecker] = None,
        fallback_interpreter: Optional[TaskInterpreter] = None,
    ):
        self.task_service = task_service
        self.interpreter = interpreter
        self.safety_checker = safety_checker
        self.fallback_interpreter = fallback_interpreter or RegexTaskInterpreter()

    async def _run_safety(self, message: str) -> None:
        if not message or not message.strip():
            raise ValidationError("Message cannot be empty")

        if self.safety_checker:
            safety = await self.safety_checker.check(message)
            if safety.flagged:
                reason = safety.reason or "Message failed safety checks"
                raise ValidationError(reason)

    async def _interpret(self, message: str) -> TaskInterpretation:
        normalized = " ".join(message.strip().split())

        if self.interpreter:
            try:
                interpreted = await self.interpreter.interpret(normalized)
                if interpreted and interpreted.title:
                    return interpreted
            except Exception:
                pass

        fallback = await self.fallback_interpreter.interpret(normalized)
        if fallback and fallback.title:
            return fallback

        raise ValidationError("Could not determine a task title from the message")

    async def create_task_from_message(self, user_id: UUID, message: str) -> ChatMessageResult:
        await self._run_safety(message)
        interpretation = await self._interpret(message)

        task = await self.task_service.create_task(
            owner_id=user_id,
            title=interpretation.title,
            description=interpretation.description,
        )
        reply = f'Created a task titled "{task.title}" with default settings.'

        return ChatMessageResult(reply=reply, created_task=task)
