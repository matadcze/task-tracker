# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A production-ready task management application with FastAPI and Next.js. Features include user authentication, task CRUD operations, file attachments with drag & drop, search/filtering, and audit logging.

## Architecture

### Backend: Domain-Driven Design with Clean Architecture

Three-layer architecture enforcing separation of concerns:

```
API Layer → Domain Layer → Infrastructure Layer → Database
```

**Layer Responsibilities**:

1. **API Layer** (`src/api/`): HTTP handling, request/response validation
   - `app.py` - FastAPI app factory with exception handlers and middleware
   - `schemas.py` - Pydantic models for API contracts
   - `v1/` - Route handlers (auth, tasks, attachments, audit, health)
   - `middleware/` - Rate limiting (Redis-based sliding window)

2. **Domain Layer** (`src/domain/`): Pure business logic, framework-agnostic
   - `entities.py` - Domain entities with behavior methods (User, Task, Attachment, AuditEvent)
   - `value_objects.py` - Enums (TaskStatus, TaskPriority, EventType)
   - `repositories.py` - Repository interfaces (Abstract Base Classes)
   - `exceptions.py` - Domain exception hierarchy
   - `services/` - Service layer (TaskService, AuthService, AttachmentService) with dependency injection

3. **Infrastructure Layer** (`src/infrastructure/`): External concerns
   - `database/models.py` - SQLAlchemy ORM models
   - `repositories/` - Repository implementations (convert models ↔ entities)
   - `auth/` - JWT provider, password hashing, FastAPI dependencies
   - `storage/` - Local file storage for attachments

**Key Patterns**:
- Domain layer defines interfaces (repositories as ABCs), infrastructure implements them
- Domain entities are Pydantic models with behavior methods (not anemic data models), completely separate from SQLAlchemy models
- Repositories convert between SQLAlchemy models (DB) ↔ Pydantic entities (domain) via `_to_entity()` methods
- Service layer encapsulates business logic, receives dependencies via constructor injection
- All services use metrics and audit logging for observability

### Frontend: Type-Safe API Integration

Decoupled from backend specifics; communicates via typed API client.

**Key Files**:
- `frontend/src/lib/api/client.ts` - Centralized API service with error handling
- `frontend/src/lib/types/api.ts` - TypeScript interfaces (match backend schemas)
- `frontend/src/hooks/useApi.ts` - `useApi()` and `useApiPolling()` hooks for state management
- `frontend/src/config/constants.ts` - API endpoints and configuration

**Type Synchronization**: Changes to `backend/src/api/schemas.py` require updates to `frontend/src/lib/types/api.ts`.

## Development Commands

```bash
# Setup
make install              # Install backend + frontend dependencies
make backend-install      # Backend only (Python via uv)
make frontend-install     # Frontend only (Node via npm)

# Running
make dev                  # Start backend (8000) and frontend (3000) in parallel
make backend-dev          # Backend only
make frontend-dev         # Frontend only

# Testing & Linting
make test                 # Run all backend tests
cd backend && uv run pytest tests/test_api/test_health.py -v          # Specific test file
cd backend && uv run pytest tests/test_api/test_health.py::test_health_check -v  # Single test

make lint                 # Check code quality
make backend-format       # Auto-format Python code

# Docker
make docker-build         # Build images
make docker-up            # Start containers
make docker-down          # Stop containers

# Cleanup
make clean                # Remove __pycache__, node_modules, .pytest_cache, etc.
make help                 # Show all available commands
```

## Key Features

- **Authentication**: JWT (15min access + 7day refresh tokens), bcrypt password hashing, token revocation support
- **Task Management**: Full CRUD with search, filters, sorting, pagination, many-to-many tags
- **File Attachments**: Upload/download/delete with drag-drop UI (10MB limit, local storage)
- **Audit Logging**: Immutable audit trail with JSONB details, survives entity deletion via SET NULL FK
- **Type Safety**: Pydantic schemas (backend) ↔ TypeScript interfaces (frontend) - manual sync required
- **Monitoring**: Prometheus metrics + Grafana dashboards (auth, tasks, attachments, performance)
- **Rate Limiting**: Redis-based sliding window (100 req/min per IP), fails open if Redis unavailable
- **Database**: SQLAlchemy 2.0 async, PostgreSQL 16, Alembic migrations (auto-run on startup)

## Service Layer & Domain-Driven Design

### Service Layer Architecture
Business logic is encapsulated in service classes located in `src/domain/services/`:
- **TaskService** - Task CRUD, status transitions, filtering, pagination
- **AuthService** - Registration, login, token refresh, password changes
- **AttachmentService** - File upload/download, validation, cleanup

Services are injected into route handlers via `infrastructure/dependencies.py` and instantiated by FastAPI's `Depends()`. Services receive repository and utility dependencies via constructor injection.

**Service Method Pattern**:
```python
async def operation(self, user_id: UUID, ...) -> ResultType:
    start_time = time.time()
    try:
        # Validation and business logic
        result = await self.repo.operation(...)

        # Audit trail
        await self.audit_repo.create(AuditEvent(...))

        # Metrics tracking
        duration = time.time() - start_time
        self.metrics.track_operation("name", "success", duration)

        return result
    except DomainException:
        # ... metrics tracking for errors ...
        raise
```

### Entity Behavior Methods
Domain entities (User, Task, Attachment) have behavior methods encapsulating business rules. Never access fields directly in services - use entity methods:

**Task Entity**:
- `can_be_modified_by(user_id)` - Authorization check
- `can_be_viewed_by(user_id)` - Access control
- `is_overdue()` - Check overdue status
- `mark_as_done()` / `mark_as_in_progress()` - Status transitions
- `add_tag(tag)` / `remove_tag(tag)` / `has_tag(tag)` - Tag management

**User Entity**:
- `can_authenticate()` - Check if user is active
- `can_be_accessed_by(user_id)` - Privacy enforcement

**Attachment Entity**:
- `is_for_task(task_id)` - Validate task relationship
- `is_image()` / `is_document()` - File type checking
- `size_in_mb()` - Size formatting for display

## Common Modifications

### Add an API Endpoint

1. **Define domain business logic**: Add method to appropriate service (TaskService, AuthService, AttachmentService) in `src/domain/services/`
2. **Add Pydantic models**: Define request/response schemas in `backend/src/api/schemas.py`
3. **Create route handler**: In `backend/src/api/v1/{resource}.py`
   - Inject service via `Depends(get_*_service)`
   - Handler delegates to service, catches domain exceptions
   - Maps domain entities to response models
4. **Add metrics**: Service method calls `self.metrics.track_*_operation()` with success/error status and duration
5. **Add TypeScript types**: Match Pydantic schema in `frontend/src/lib/types/api.ts`
6. **Add API client method**: In `frontend/src/lib/api/client.ts`, return typed Promise
7. **Use in component**: `const {data, loading, error} = useApi(() => apiClient.resource.method())`

**Example route handler** (delegates to service):
```python
@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        task = await task_service.create_task(
            owner_id=current_user_id,
            title=task_data.title,
            ...
        )
        return TaskResponse.model_validate(task)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Update Configuration

Add setting to `backend/src/core/config.py`:
```python
my_setting: str = "default_value"
```

Access in any module: `from src.core.config import settings; settings.my_setting`

### Add Database Migration

```bash
cd backend
uv run alembic revision --autogenerate -m "description"
# Review generated migration in alembic/versions/
uv run alembic upgrade head  # Apply migration
```

Migrations auto-run on container startup via `entrypoint.sh`.

### Add Prometheus Metrics

1. Define metric in `backend/src/core/metrics.py` using `_get_or_create_*` helpers (handles hot-reload)
   ```python
   my_operation_total = _get_or_create_counter(
       "my_operation",  # Don't add _total suffix
       "Description of the operation",
       ["operation", "status"],
   )
   ```
2. Add abstract method to `src/domain/services/metrics_provider.py` (the interface)
3. Implement in `src/infrastructure/metrics/prometheus_provider.py` (the implementation)
4. Track in service methods: `self.metrics.track_*_operation(operation, status, duration)`
5. View at `http://localhost:8000/metrics` or Grafana dashboard `http://localhost:3001`

**Metrics naming convention**:
- Counters: `operation_total` (Prometheus adds `_total` automatically)
- Histograms: `operation_duration_seconds`
- Gauges: `operation_count` (no suffix)

## Testing

**Test Files**:
- `backend/tests/test_api/` - Endpoint tests using `TestClient(create_app())`
- `backend/tests/test_state/` - State structure tests
- `backend/tests/test_utils/` - Configuration tests

**Test Pattern**:
```python
from fastapi.testclient import TestClient
from src.api.app import create_app

def test_endpoint():
    client = TestClient(create_app())
    response = client.get("/api/v1/health")
    assert response.status_code == 200
```

Run with `-v` for verbose output. Settings ignores extra `.env` variables, so tests work without perfect env setup.

## Configuration

**Backend** (`backend/src/core/config.py`):
- Loads from `backend/.env` via Pydantic Settings
- Settings class uses `extra="ignore"` - test-friendly, won't fail on extra env vars
- Singleton pattern: `from src.core.config import settings`
- **Important vars**:
  - `DATABASE_URL` - PostgreSQL connection string (async driver: `postgresql+asyncpg://`)
  - `REDIS_URL` - Redis connection for rate limiting/caching
  - `JWT_SECRET_KEY` - HMAC signing key for tokens
  - `ACCESS_TOKEN_EXPIRE_MINUTES` - Default 15
  - `REFRESH_TOKEN_EXPIRE_DAYS` - Default 7
  - `MAX_UPLOAD_SIZE_MB` - File upload limit, default 10

**Frontend** (`frontend/src/config/constants.ts`):
- `NEXT_PUBLIC_API_URL` - Backend base URL, defaults to `http://localhost:8000`
- All other config is in TypeScript constants (API endpoints, timeouts)

**Docker Services**:
- Backend: `http://localhost:8000` (health: `/health`, metrics: `/metrics`)
- Frontend: `http://localhost:3000`
- Prometheus: `http://localhost:9091` (from host), `http://prometheus:9090` (internal)
- Grafana: `http://localhost:3001` (admin/admin)

## Important Patterns & Gotchas

### Repository Pattern & Liskov Substitution Principle
- Domain layer (`domain/repositories.py`) defines **interfaces** (ABCs)
- Infrastructure layer implements them (`infrastructure/repositories/`)
- Route handlers inject repository implementations via FastAPI dependencies
- Repositories convert between SQLAlchemy models (DB) ↔ Pydantic entities (domain)
- **IMPORTANT**: Interface method signatures must match implementations exactly (Liskov Substitution Principle)
  - All parameters in implementation must exist in interface
  - Default values must match between interface and implementation
  - Return types must be identical
  - Example: If implementation has `list(self, owner_id: UUID = None, ...)`, interface must also include `owner_id` parameter

### Async Everywhere
- All route handlers are `async def`
- Database: Use `AsyncSession` from `get_db()` dependency
- Redis: Use `redis.asyncio` client
- File I/O: Even local storage uses `async` methods (aiofiles)

### Type Synchronization
**Critical**: `backend/src/api/schemas.py` and `frontend/src/lib/types/api.ts` must stay in sync manually.

Example workflow:
1. Add field to Pydantic schema: `user_count: int`
2. Update TypeScript interface: `user_count: number`
3. Backend tests will catch missing fields in responses
4. Frontend TypeScript will catch missing properties in usage

### Metrics Hot-Reload Safety
Prometheus metrics in `src/core/metrics.py` use `_get_or_create_*()` helpers to handle duplicate registration during uvicorn hot-reload. Always use these helpers, never create metrics directly with `Counter()`, `Gauge()`, or `Histogram()`.

### Database Migrations
Alembic migrations in `backend/alembic/versions/` auto-run on container startup via entrypoint script. For local dev, run manually: `uv run alembic upgrade head`

## Troubleshooting

**"Duplicated timeseries in CollectorRegistry"**:
- Metrics defined directly (not using helpers) get re-registered on hot reload
- Use `_get_or_create_counter/gauge/histogram()` from `core/metrics.py`

**Type errors between frontend/backend**:
- Pydantic schema changed but TypeScript interface didn't
- Update `frontend/src/lib/types/api.ts` to match `backend/src/api/schemas.py`

**Rate limit errors**:
- Redis unavailable or connection failed
- Rate limiting fails open (allows requests) if Redis down
- Check Redis container: `docker logs tasktracker-redis`

**Database migration conflicts**:
- Multiple branches created migrations
- Use `uv run alembic merge heads` to create merge migration
- Or manually edit migration file to resolve conflicts

**Grafana dashboard not loading**:
- Check Prometheus datasource URL is `http://prometheus:9090` (internal Docker network)
- NOT `http://localhost:9091` (host network)
- Dashboard JSON must be flat (no `"dashboard": {}` wrapper)
