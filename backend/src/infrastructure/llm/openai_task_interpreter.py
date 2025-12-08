import json
import logging
from typing import Optional

from openai import AsyncOpenAI, BadRequestError, OpenAIError

from src.domain.services.chat_interpreter import TaskInterpretation

logger = logging.getLogger(__name__)


class OpenAIChatTaskInterpreter:
    def __init__(self, api_key: str, model: str, timeout_seconds: int = 8):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.timeout_seconds = timeout_seconds

    def _prompt(self) -> str:
        return """
You are a task extraction helper. When given a user's short message, analyze it carefully to determine the main action or objective. Provide your answer as a JSON object with two fields: a concise task "title" and a longer "description" that explains the objective in a clear sentence or two.

Please ensure:
- The "title" must be as short and specific as possible, omitting extra context.
- The "description" should briefly and clearly explain the task, providing the necessary context or clarification beyond the title, but remaining succinct.
- Output ONLY a JSON object with "title" and "description". Do NOT add due dates, priorities, or any extra context.
- If uncertain about the user's intent, use your best judgment to summarize both fields appropriately.
- All reasoning and analysis should happen internally; never include it in your output.

# Output Specifications

- Output only JSON in the form: {"title": "[task title]", "description": "[task description]"}
- Do not add extra keys, explanations, introductory text, or alternate formatting.
- NEVER include due dates, priorities, or information unrelated to the user's core request.
- If user intent is ambiguous, make a best-guess concise title and description.

# Workflow

- Internally: analyze the message → identify main objective → choose concise, clear title → write a brief, clear description explaining the task.
- Only OUTPUT the JSON object, containing both the title and description as described.

# Examples

Example 1
- Input: "Remind me to feed the cat"
- Output: {"title": "feed the cat", "description": "Remind me to give food to the cat."}

Example 2
- Input: "Check status of last week's report."
- Output: {"title": "check status of last week's report", "description": "Look into and provide the current status or progress of the report from last week."}

Example 3  
- Input: "Email Sarah about budget updates"
- Output: {"title": "email Sarah about budget updates", "description": "Send an email to Sarah to inform her of any updates regarding the budget."}

Example 4  
- Input: "I’m not sure if I need to call Bob or Alice, but something about the contract"
- Output: {"title": "contact Bob or Alice about the contract", "description": "Reach out to either Bob or Alice to discuss or clarify matters related to the contract."}

(Real-world examples may be longer or more ambiguous; always keep the task title brief and the description clear and to the point. Use your best judgment for unclear cases.)

IMPORTANT REMINDER:  
You must ONLY output the JSON object with "title" and "description" as specified above—nothing more.
"""

    async def _complete(self, message: str, use_response_format: bool = True):
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._prompt()},
                {"role": "user", "content": message},
            ],
            "max_completion_tokens": 80,
            "temperature": 1,
            "timeout": self.timeout_seconds,
        }
        if use_response_format:
            kwargs["response_format"] = {"type": "json_object"}

        return await self.client.chat.completions.create(**kwargs)

    async def interpret(self, message: str) -> Optional[TaskInterpretation]:
        completion = None
        try:
            completion = await self._complete(message, use_response_format=True)
        except BadRequestError as exc:
            logger.debug("OpenAI bad request, retrying without response_format: %s", exc)
            try:
                completion = await self._complete(message, use_response_format=False)
            except OpenAIError as inner_exc:
                logger.warning("OpenAI interpreter failed after retry: %s", inner_exc)
                return None
        except OpenAIError as exc:
            logger.warning("OpenAI interpreter failed: %s", exc)
            return None
        except Exception as exc:
            logger.warning("Unexpected OpenAI interpreter error: %s", exc)
            return None

        if not completion or not completion.choices:
            return None

        content = completion.choices[0].message.content
        if not content:
            return None

        try:
            parsed = json.loads(content)
            title = parsed.get("title") or parsed.get("task_title")
            description = parsed.get("description") or parsed.get("task_description")
        except json.JSONDecodeError:
            title = content
            description = None

        if not isinstance(title, str):
            return None

        return TaskInterpretation(
            title=title,
            description=description if isinstance(description, str) else None,
        )
