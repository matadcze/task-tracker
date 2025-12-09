# C4 Model - Level 3: Component Diagram

The Component diagram shows how the Backend container is made up of components, their responsibilities, and interactions.

## Backend Component Diagram

![Backend Component Diagram](./backend-component-diagram.png)

## Layer Responsibilities

### API Layer (`src/api/`)

| Component | File | Responsibility |
|-----------|------|----------------|
| **FastAPI App** | `app.py` | App factory, exception handlers, router registration |
| **Auth Routes** | `v1/auth.py` | Register, login, refresh, profile endpoints |
| **Task Routes** | `v1/tasks.py` | CRUD operations for tasks |
| **Chat Routes** | `v1/chat.py` | Natural language task creation |
| **Attachment Routes** | `v1/attachments.py` | File upload/download |
| **Audit Routes** | `v1/audit.py` | Audit log queries |
| **Schemas** | `schemas.py` | Request/response Pydantic models |
| **Middleware** | `middleware/` | Rate limiting, metrics, request logging |

### Domain Layer (`src/domain/`)

| Component | File | Responsibility |
|-----------|------|----------------|
| **Entities** | `entities.py` | Rich domain models with behavior methods |
| **Value Objects** | `value_objects.py` | Enums (TaskStatus, Priority, EventType) |
| **Exceptions** | `exceptions.py` | Domain exception hierarchy |
| **Repository Interfaces** | `repositories.py` | Abstract base classes for data access |
| **TaskService** | `services/task_service.py` | Task business logic, validation |
| **AuthService** | `services/auth_service.py` | Authentication workflows |
| **ChatService** | `services/chat_service.py` | LLM orchestration with fallback |
| **AttachmentService** | `services/attachment_service.py` | File handling logic |
| **ReminderService** | `services/reminder_service.py` | Due-soon reminder processing |

### Infrastructure Layer (`src/infrastructure/`)

| Component | File | Responsibility |
|-----------|------|----------------|
| **User Repository** | `repositories/user_repository.py` | User persistence |
| **Task Repository** | `repositories/task_repository.py` | Task persistence with filtering |
| **SQLAlchemy Models** | `database/models.py` | ORM model definitions |
| **JWTProvider** | `auth/jwt_provider.py` | Token creation/verification |
| **PasswordHasher** | `auth/password.py` | bcrypt hashing |
| **RateLimiter** | `auth/rate_limiter.py` | Redis sliding window |
| **OpenAI Interpreter** | `llm/openai_task_interpreter.py` | Chat completion for task extraction |
| **OpenAI Safety** | `llm/openai_safety_checker.py` | Content moderation |
| **Local Storage** | `storage/local_storage.py` | File system operations |

## Dependency Flow

```
API Layer
    ↓ depends on
Domain Layer (Services, Entities, Interfaces)
    ↓ implemented by
Infrastructure Layer (Repositories, Providers)
    ↓ uses
External Systems (Database, Redis, OpenAI)
```

The domain layer defines interfaces; infrastructure implements them. This allows:
- Testing with mock implementations
- Swapping implementations without changing business logic
- Clear separation of concerns

## Service Dependency Injection

```python
# Route handler receives injected service
@router.post("/tasks")
async def create_task(
    task_data: TaskCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.create_task(...)

# Service receives injected dependencies
class TaskService:
    def __init__(
        self,
        task_repo: TaskRepository,      # Interface
        audit_repo: AuditEventRepository,
        tag_service: TagService,
        metrics: MetricsProvider,       # Interface
    ):
        ...
```

## Key Design Patterns

### Repository Pattern
```
┌─────────────────────┐     ┌──────────────────────┐
│ TaskRepository (ABC)│ ←── │ SQLAlchemyTaskRepo   │
│   + create()        │     │   + create()         │
│   + get_by_id()     │     │   + get_by_id()      │
│   + list()          │     │   + list()           │
│   + update()        │     │   + _to_entity()     │
│   + delete()        │     │                      │
└─────────────────────┘     └──────────────────────┘
```

### Entity Conversion
```
SQLAlchemy Model (DB) ──_to_entity()──→ Pydantic Entity (Domain)
     TaskModel                              Task
```

### Interpreter Pattern (Chat)
```
┌───────────────────┐     ┌─────────────────────────┐
│ TaskInterpreter   │ ←── │ OpenAITaskInterpreter   │
│   + interpret()   │     │   + interpret()         │
└───────────────────┘     └─────────────────────────┘
         ↑
         └──────────────── │ RegexTaskInterpreter   │
                          │   + interpret()         │
                          └─────────────────────────┘
```

## Next Steps

- See [Arc42 Documentation](../arc42/arc42-documentation.md) for comprehensive architecture documentation
- See [ADRs](../adr/) for decision rationale
- See [Sequence Diagrams](../diagrams/sequence-diagrams.md) for interaction flows
