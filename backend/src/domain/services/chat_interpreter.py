import re
from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class TaskInterpretation:
    title: str
    description: Optional[str] = None


class TaskInterpreter(Protocol):
    async def interpret(self, message: str) -> Optional[TaskInterpretation]: ...


class RegexTaskInterpreter(TaskInterpreter):

    def __init__(self):
        self.patterns = [
            r"add\s+(?:a\s+)?task\s+(?:to\s+)?(?P<title>.+)",
            r"create\s+(?:a\s+)?task\s+(?:to\s+)?(?P<title>.+)",
            r"new\s+task[:\-]?\s+(?P<title>.+)",
            r"task[:\-]\s*(?P<title>.+)",
        ]

    @staticmethod
    def _clean_title(title: str) -> str:
        cleaned = title.strip().strip("\"'.").rstrip(".! ")
        if cleaned.lower().startswith("to "):
            cleaned = cleaned[3:].lstrip()
        return cleaned

    async def interpret(self, message: str) -> Optional[TaskInterpretation]:
        normalized = " ".join(message.strip().split())
        title = None

        for pattern in self.patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if match:
                title = match.group("title")
                break

        if title is None:
            title = normalized

        cleaned_title = self._clean_title(title)
        if not cleaned_title:
            return None

        description = normalized if normalized != cleaned_title else None
        return TaskInterpretation(title=cleaned_title, description=description)
