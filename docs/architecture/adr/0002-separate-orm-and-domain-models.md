# ADR-0002: Separate ORM and Domain Models

## Status

Accepted

## Date

2024-01-15

## Context

Following our adoption of DDD (ADR-0001), we need to decide how to model our domain entities in relation to our database models.

Two main approaches exist:
1. **Shared models**: Use SQLAlchemy models as domain entities (with added behavior methods)
2. **Separate models**: Pydantic entities in domain layer, SQLAlchemy models in infrastructure

The domain layer should be framework-agnostic and focused on business logic, not persistence concerns.

## Decision

We will maintain **separate models**:

- **Domain Entities** (`src/domain/entities.py`): Pydantic BaseModel classes with behavior methods
- **ORM Models** (`src/infrastructure/database/models.py`): SQLAlchemy models for persistence
- **Conversion**: Repositories convert between models via `_to_entity()` methods

**Example:**

```python
# Domain Entity (Pydantic)
class Task(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    status: TaskStatus

    def can_be_modified_by(self, user_id: UUID) -> bool:
        return self.owner_id == user_id

    def mark_as_done(self) -> None:
        self.status = TaskStatus.DONE

# ORM Model (SQLAlchemy)
class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(UUID, primary_key=True)
    owner_id = Column(UUID, ForeignKey("users.id"))
    title = Column(String(500))
    status = Column(Enum(TaskStatus))

# Repository converts between them
class SQLAlchemyTaskRepository:
    def _to_entity(self, model: TaskModel) -> Task:
        return Task.model_validate(model)
```

## Consequences

### Positive

- **Framework independence**: Domain layer has no SQLAlchemy dependency
- **Clean separation**: Database schema changes don't affect domain logic
- **Testability**: Domain entities can be instantiated without database
- **Validation**: Pydantic provides runtime validation for domain entities
- **Serialization**: Pydantic entities easily convert to JSON for API responses
- **Rich models**: Behavior methods live naturally on Pydantic models

### Negative

- **Duplication**: Two representations of the same concept
- **Mapping overhead**: Conversion code in repositories
- **Sync discipline**: Changes must be made in both places
- **Memory**: Two objects created per database record

### Neutral

- Repository becomes the boundary where conversion happens
- API schemas (`src/api/schemas.py`) are a third representation for request/response

## Alternatives Considered

### Alternative 1: SQLAlchemy Models as Domain Entities

**Description:** Add behavior methods directly to SQLAlchemy models, use them throughout the application.

**Pros:**
- Single source of truth
- No conversion code
- Familiar pattern (Active Record)

**Cons:**
- Domain layer depends on SQLAlchemy
- Testing requires database session
- Mixing persistence and business concerns

**Why not chosen:** Violates clean architecture principles. Testing becomes integration testing.

### Alternative 2: SQLModel (Pydantic + SQLAlchemy hybrid)

**Description:** Use SQLModel which combines Pydantic validation with SQLAlchemy ORM.

**Pros:**
- Single model definition
- Pydantic validation built-in
- Less boilerplate

**Cons:**
- Tightly couples domain to database
- Less mature than SQLAlchemy
- Async support still evolving

**Why not chosen:** Still couples domain to ORM. Separate models give more flexibility.

### Alternative 3: Data Transfer Objects (DTOs) Only

**Description:** Domain layer uses plain dictionaries or dataclasses, no rich models.

**Pros:**
- Minimal dependencies
- Very lightweight

**Cons:**
- No validation
- No behavior on entities
- Anemic domain model

**Why not chosen:** We want rich domain models with behavior, not just data bags.

## Implementation Notes

**Repository conversion pattern:**

```python
class SQLAlchemyTaskRepository(TaskRepository):
    async def get_by_id(self, task_id: UUID) -> Optional[Task]:
        result = await self.session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    def _to_entity(self, model: TaskModel) -> Task:
        return Task(
            id=model.id,
            owner_id=model.owner_id,
            title=model.title,
            status=model.status,
            # ... map all fields
        )
```

## References

- [ADR-0001: Use Domain-Driven Design](0001-use-domain-driven-design.md)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
