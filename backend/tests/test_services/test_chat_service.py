import pytest
from unittest.mock import AsyncMock

from src.domain.entities import Task
from src.domain.exceptions import ValidationError
from src.domain.services.chat_service import ChatService, TaskInterpreter, TaskInterpretation


class StubInterpreter(TaskInterpreter):
    def __init__(
        self,
        title: str | None = None,
        description: str | None = None,
        should_raise: bool = False,
    ):
        self.title = title
        self.description = description
        self.should_raise = should_raise
        self.calls = 0

    async def interpret(self, message: str) -> TaskInterpretation | None:
        self.calls += 1
        if self.should_raise:
            raise RuntimeError("llm failure")
        if self.title is None:
            return None
        return TaskInterpretation(title=self.title, description=self.description)


@pytest.mark.asyncio
async def test_creates_task_from_instruction(sample_user_id):
    task_service = AsyncMock()
    created_task = Task(owner_id=sample_user_id, title="call John")
    task_service.create_task.return_value = created_task

    service = ChatService(task_service=task_service)

    result = await service.create_task_from_message(sample_user_id, "Add a task to call John")

    task_service.create_task.assert_awaited_once_with(
        owner_id=sample_user_id, title="call John", description="Add a task to call John"
    )
    assert result.created_task == created_task
    assert "call John" in result.reply


@pytest.mark.asyncio
async def test_uses_message_when_no_pattern(sample_user_id):
    task_service = AsyncMock()
    created_task = Task(owner_id=sample_user_id, title="Follow up with design team")
    task_service.create_task.return_value = created_task

    service = ChatService(task_service=task_service)

    result = await service.create_task_from_message(sample_user_id, "Follow up with design team")

    task_service.create_task.assert_awaited_once_with(
        owner_id=sample_user_id, title="Follow up with design team", description=None
    )
    assert result.created_task.title == "Follow up with design team"
    assert "Follow up with design team" in result.reply


@pytest.mark.asyncio
async def test_rejects_empty_message(sample_user_id):
    task_service = AsyncMock()
    service = ChatService(task_service=task_service)

    with pytest.raises(ValidationError):
        await service.create_task_from_message(sample_user_id, "   ")


@pytest.mark.asyncio
async def test_prefers_interpreter_when_available(sample_user_id):
    task_service = AsyncMock()
    created_task = Task(owner_id=sample_user_id, title="LLM generated title")
    task_service.create_task.return_value = created_task
    interpreter = StubInterpreter(
        title="LLM generated title", description="LLM generated description"
    )

    service = ChatService(task_service=task_service, interpreter=interpreter)

    await service.create_task_from_message(sample_user_id, "Add a task to call John")

    assert interpreter.calls == 1
    task_service.create_task.assert_awaited_once_with(
        owner_id=sample_user_id,
        title="LLM generated title",
        description="LLM generated description",
    )


@pytest.mark.asyncio
async def test_falls_back_when_interpreter_errors(sample_user_id):
    task_service = AsyncMock()
    created_task = Task(owner_id=sample_user_id, title="call John")
    task_service.create_task.return_value = created_task
    interpreter = StubInterpreter(should_raise=True)

    service = ChatService(task_service=task_service, interpreter=interpreter)

    await service.create_task_from_message(sample_user_id, "Add a task to call John")

    assert interpreter.calls == 1
    task_service.create_task.assert_awaited_once_with(
        owner_id=sample_user_id, title="call John", description="Add a task to call John"
    )
