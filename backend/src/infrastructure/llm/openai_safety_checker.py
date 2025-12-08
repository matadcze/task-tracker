import logging
from typing import Optional

from openai import AsyncOpenAI, OpenAIError

from src.domain.services.chat_service import SafetyCheckResult

logger = logging.getLogger(__name__)


class OpenAISafetyChecker:

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 8):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def check(self, message: str) -> SafetyCheckResult:
        try:
            result = await self.client.moderations.create(
                model=self.model,
                input=message,
                timeout=self.timeout_seconds,
            )
            flagged = False
            reason: Optional[str] = None

            if result and result.results:
                flagged = result.results[0].flagged
                if flagged:
                    reason = "Content violates moderation policy"

            return SafetyCheckResult(flagged=flagged, reason=reason)
        except OpenAIError as exc:
            logger.warning("OpenAI safety check failed, allowing message by default: %s", exc)
            return SafetyCheckResult(flagged=False)
        except Exception as exc:
            logger.warning("Unexpected safety check error, allowing message: %s", exc)
            return SafetyCheckResult(flagged=False)
