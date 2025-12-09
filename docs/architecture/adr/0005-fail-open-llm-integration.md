# ADR-0005: Fail-Open LLM Integration

## Status

Accepted

## Date

2024-02-01

## Context

The application integrates with OpenAI API for two features:

1. **Task Interpretation**: Extract structured task data from natural language
2. **Content Moderation**: Check messages for inappropriate content

These external API calls can fail due to:
- Network issues
- API rate limits
- Service outages
- Timeout (configured at 8 seconds)

We need to decide how the system should behave when OpenAI is unavailable.

## Decision

We will implement a **fail-open** design where external AI features degrade gracefully:

### Strategy

| Component | Primary | Fallback | On Failure |
|-----------|---------|----------|------------|
| **Task Interpreter** | OpenAI Chat Completion | Regex-based parsing | Use regex result |
| **Safety Checker** | OpenAI Moderation API | None | Skip moderation |

### Implementation

```python
class ChatService:
    async def _interpret(self, message: str) -> TaskInterpretation:
        # Try OpenAI first
        if self.interpreter:
            try:
                result = await self.interpreter.interpret(message)
                if result and result.title:
                    return result
            except Exception:
                pass  # Fall through to fallback

        # Fallback to regex
        return await self.fallback_interpreter.interpret(message)

    async def _run_safety(self, message: str) -> None:
        if self.safety_checker:
            try:
                result = await self.safety_checker.check(message)
                if result.flagged:
                    raise ValidationError(result.reason)
            except ValidationError:
                raise  # Re-raise validation errors
            except Exception:
                pass  # Skip moderation on other errors
```

### Fallback Interpreter

The `RegexTaskInterpreter` extracts task titles using patterns like:
- "remind me to **[task]**"
- "create a task to **[task]**"
- "add **[task]** to my tasks"

## Consequences

### Positive

- **High availability**: Core functionality works without OpenAI
- **Cost efficiency**: Regex fallback is free
- **Predictable**: Users can always create tasks via chat
- **Graceful degradation**: Reduced functionality beats total failure

### Negative

- **Reduced accuracy**: Regex less intelligent than LLM
- **No moderation**: Inappropriate content may pass through when OpenAI down
- **Silent failures**: Users may not know they're using fallback
- **Security risk**: Fail-open moderation could allow harmful content

### Neutral

- Logging captures when fallback is used
- Metrics track interpreter success/failure rates

## Alternatives Considered

### Alternative 1: Fail-Closed

**Description:** Return error if OpenAI unavailable, require AI for all chat features.

**Pros:**
- Consistent AI quality
- Content always moderated
- Clear error messaging

**Cons:**
- Feature unavailable during OpenAI outages
- Bad user experience
- Dependency on external service

**Why not chosen:** Core task creation shouldn't depend on external service.

### Alternative 2: Queue and Retry

**Description:** Queue failed requests, retry when OpenAI available.

**Pros:**
- Eventually consistent
- No degradation

**Cons:**
- Delayed task creation
- Complex implementation
- User waits for result

**Why not chosen:** Users expect immediate task creation.

### Alternative 3: Multiple LLM Providers

**Description:** Fall back to alternative LLM (Anthropic, local model).

**Pros:**
- Maintains AI quality
- Redundancy

**Cons:**
- Multiple API integrations
- Cost of multiple providers
- Different model behaviors

**Why not chosen:** Over-engineered for current needs. Could be future enhancement.

### Alternative 4: Local LLM

**Description:** Run small LLM locally as fallback (e.g., Ollama).

**Pros:**
- No external dependency
- Privacy benefits
- Offline capable

**Cons:**
- Resource intensive
- Lower quality than GPT
- Deployment complexity

**Why not chosen:** Adds significant infrastructure complexity.

## Risk Mitigation

### Content Moderation Risk

When moderation fails open, harmful content could enter the system:

**Mitigations:**
1. Input length limits
2. Database-level constraints
3. Manual review capability (audit logs)
4. Rate limiting reduces abuse potential

### Monitoring

Track these metrics to detect degraded operation:
- `chat_interpreter_fallback_total`: Count of regex fallback uses
- `chat_safety_skip_total`: Count of skipped safety checks
- `openai_request_duration_seconds`: API latency
- `openai_request_errors_total`: API failures

## Configuration

```python
# Settings
OPENAI_API_KEY: Optional[str] = None      # Feature disabled if not set
OPENAI_MODEL: str = "gpt-5.1-chat-latest"
OPENAI_MODERATION_MODEL: str = "omni-moderation-latest"
OPENAI_TIMEOUT_SECONDS: int = 8
```

If `OPENAI_API_KEY` is not set, the system uses regex-only interpretation with no moderation - a fully functional but AI-free mode.

## References

- [OpenAI Moderation API](https://platform.openai.com/docs/guides/moderation)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Graceful Degradation](https://www.nngroup.com/articles/graceful-degradation-progressive-enhancement/)
