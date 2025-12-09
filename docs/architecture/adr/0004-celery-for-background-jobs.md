# ADR-0004: Celery for Background Jobs

## Status

Accepted

## Date

2024-01-25

## Context

The application needs to perform background tasks that should not block HTTP request handling:

1. **Scheduled reminders**: Check for tasks due soon and log reminders
2. **Future: Email notifications**: Send reminder emails asynchronously
3. **Future: File processing**: Thumbnail generation, virus scanning

Requirements:
- Reliable task execution (tasks shouldn't be lost)
- Scheduled/periodic task support
- Horizontal scalability (multiple workers)
- Monitoring and visibility into task status

## Decision

We will use **Celery** with **Celery Beat** for background job processing:

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Celery Beat │────▶│    Redis    │◀────│   Worker    │
│ (Scheduler) │     │  (Broker)   │     │ (Processor) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  PostgreSQL │
                    │  (Results)  │
                    └─────────────┘
```

### Components

| Component | Purpose | Container |
|-----------|---------|-----------|
| **Celery Worker** | Executes tasks from queue | `celery-worker` |
| **Celery Beat** | Schedules periodic tasks | `celery-beat` |
| **Redis** | Message broker | `redis` |

### Task Definition Pattern

```python
@celery_app.task(name="reminders.send_due_soon")
def send_due_soon_reminders() -> int:
    """Celery task wrapper around domain service."""
    async def _run():
        async with AsyncSessionLocal() as session:
            service = ReminderService(...)
            return await service.send_due_soon_reminders()

    return asyncio.run(_run())
```

### Schedule Configuration

```python
celery_app.conf.beat_schedule = {
    "due-soon-reminders": {
        "task": "reminders.send_due_soon",
        "schedule": timedelta(minutes=settings.reminder_check_interval_minutes),
    },
}
```

## Consequences

### Positive

- **Reliability**: Redis-backed queue persists tasks
- **Scalability**: Add more workers for throughput
- **Scheduling**: Celery Beat handles cron-like schedules
- **Monitoring**: Flower dashboard available (not currently deployed)
- **Mature ecosystem**: Well-documented, battle-tested

### Negative

- **Operational overhead**: Two additional containers (worker + beat)
- **Complexity**: Async Python requires `asyncio.run()` wrapper
- **Redis dependency**: Single point of failure for job queue
- **Memory**: Workers consume memory even when idle

### Neutral

- Tasks define their own retry logic
- Results stored in Redis (can be PostgreSQL if needed)

## Alternatives Considered

### Alternative 1: FastAPI BackgroundTasks

**Description:** Use FastAPI's built-in `BackgroundTasks` for async execution.

**Pros:**
- No additional dependencies
- Simple implementation
- In-process execution

**Cons:**
- Tasks lost on server restart
- No scheduling support
- No distributed processing
- No visibility/monitoring

**Why not chosen:** Not reliable for critical tasks. No scheduling capability.

### Alternative 2: RQ (Redis Queue)

**Description:** Simpler Redis-based task queue.

**Pros:**
- Simpler than Celery
- Lightweight
- Redis-native

**Cons:**
- Less feature-rich than Celery
- Scheduling requires separate scheduler (rq-scheduler)
- Smaller ecosystem

**Why not chosen:** Celery's scheduling and maturity preferred.

### Alternative 3: APScheduler

**Description:** Python scheduling library, runs in-process.

**Pros:**
- No external broker needed
- Simple setup
- Good for single-instance

**Cons:**
- Not distributed
- Jobs lost on restart (without job store)
- In-process resource competition

**Why not chosen:** Doesn't support distributed workers.

### Alternative 4: AWS SQS + Lambda / Cloud Tasks

**Description:** Cloud-native serverless task processing.

**Pros:**
- Managed infrastructure
- Auto-scaling
- Pay-per-use

**Cons:**
- Cloud vendor lock-in
- More complex local development
- Cost for high-frequency tasks

**Why not chosen:** Prefer self-hosted solution without cloud dependencies.

## Implementation Notes

### Running Locally

```bash
# Terminal 1: Worker
cd backend && uv run celery -A src.worker.celery_app worker --loglevel=info

# Terminal 2: Beat (scheduler)
cd backend && uv run celery -A src.worker.celery_app beat --loglevel=info
```

### Docker Compose

```yaml
celery-worker:
  command: uv run celery -A src.worker.celery_app worker --loglevel=info
  depends_on:
    - redis
    - postgres

celery-beat:
  command: uv run celery -A src.worker.celery_app beat --loglevel=info
  depends_on:
    - redis
```

### Idempotency

Reminder tasks are idempotent:
- Check if reminder already sent for task + type
- Skip if already exists (unique constraint)

```python
existing = await self.reminder_repo.get_by_task_and_type(
    task_id, ReminderType.DUE_SOON
)
if existing:
    continue  # Skip, already reminded
```

## References

- [Celery Documentation](https://docs.celeryq.dev/)
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/tasks.html#tips-and-best-practices)
- [Redis as Message Broker](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html)
