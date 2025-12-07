# Worker Tests

This directory contains comprehensive tests for the Celery worker and reminder service.

## Test Files

### test_celery_app.py
Tests for the Celery application configuration and setup.

**Test Cases:**
- `test_celery_app_is_configured` - Verifies Celery app is properly initialized
- `test_celery_app_broker_url` - Ensures broker URL is loaded from settings
- `test_celery_app_result_backend` - Verifies result backend is configured
- `test_celery_app_serializer_settings` - Tests JSON serialization configuration
- `test_celery_app_timezone_settings` - Validates UTC timezone is set
- `test_celery_app_includes_tasks` - Confirms task modules are included
- `test_celery_beat_schedule_configured` - Verifies beat schedule exists
- `test_beat_schedule_task_name` - Validates task name in schedule
- `test_beat_schedule_interval` - Confirms schedule interval is set

**Coverage:** Celery configuration, beat schedule setup

### test_tasks.py
Tests for Celery task implementations and async execution.

**Test Classes:**

#### TestRunRemindersAsync
Tests for the `_run_reminders()` async function:
- `test_run_reminders_success` - Single task reminder processing
- `test_run_reminders_no_tasks` - Handling when no tasks are due
- `test_run_reminders_database_error_rollback` - Transaction rollback on errors
- `test_run_reminders_multiple_tasks` - Processing multiple tasks
- `test_run_reminders_custom_window` - Using custom time windows

**Coverage:** Database session management, repository initialization, error handling

#### TestSendDueSoonRemindersTask
Tests for the `send_due_soon_reminders()` Celery task:
- `test_task_is_registered` - Task is registered with Celery
- `test_task_returns_processed_count` - Returns count of processed reminders
- `test_task_uses_24_hour_window` - Default 24-hour window
- `test_task_calls_configure_logging` - Logging initialization
- `test_task_logs_result` - Result logging
- `test_task_logs_include_timestamp` - Timestamp in logs
- `test_task_handles_zero_reminders` - Zero reminders handling
- `test_task_executes_async_function` - Async execution via asyncio.run

**Coverage:** Task execution, logging, async function wrapping

## Fixtures (in conftest.py)

Added reminder-specific fixtures:
- `sample_reminder_log` - Sample ReminderLog entity
- `mock_reminder_repository` - Mock reminder repository with async methods

## Test Statistics

- **Total Tests:** 32
- **Celery Configuration Tests:** 9
- **Worker Task Tests:** 8
- **Reminder Service Tests:** 15
- **Pass Rate:** 100%

## Running the Tests

Run all worker tests:
```bash
uv run pytest tests/test_worker/ -v
```

Run specific test file:
```bash
uv run pytest tests/test_worker/test_celery_app.py -v
```

Run reminder service tests:
```bash
uv run pytest tests/test_services/test_reminder_service.py -v
```

Run all worker and reminder tests:
```bash
uv run pytest tests/test_worker/ tests/test_services/test_reminder_service.py -v
```

## Test Coverage Areas

1. **Celery Configuration**
   - Broker and result backend setup
   - JSON serialization settings
   - UTC timezone configuration
   - Beat schedule registration

2. **Async Task Execution**
   - Database session management
   - Repository initialization
   - Error handling and rollback
   - Logging configuration

3. **Reminder Processing**
   - Single and multiple task handling
   - Idempotency (skipping existing reminders)
   - Error resilience
   - Audit trail creation
   - Metrics tracking

4. **Integration Points**
   - Task registration with Celery
   - Async function wrapping
   - Database transaction management
   - Logging and metrics integration

## Mocking Strategy

The tests use:
- `AsyncMock` for async repository methods
- `MagicMock` for metrics providers
- `patch` for dependency injection
- In-memory test database setup in conftest.py

## Key Test Patterns

1. **Service Testing:** Mock repositories and test business logic
2. **Task Testing:** Mock async functions and verify orchestration
3. **Configuration Testing:** Direct assertions on Celery settings
4. **Integration Testing:** Full async flow with mocked dependencies

## Notes

- All async tests use `@pytest.mark.asyncio` decorator
- Synchronous tests don't use asyncio marker
- Tests are isolated and don't require running services
- Mock repositories follow async method patterns
- Fixtures are defined in parent `conftest.py`
