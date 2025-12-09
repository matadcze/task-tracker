# ADR-0001: Use Domain-Driven Design

## Status

Accepted

## Date

2024-01-15

## Context

We are building a task management application that needs to:
- Handle complex business rules (task status transitions, ownership validation)
- Support multiple features (tasks, attachments, audit, chat)
- Maintain a clear separation between business logic and technical concerns
- Be easily testable and maintainable as the codebase grows

We needed to choose an architectural approach that would support these requirements.

## Decision

We will use **Domain-Driven Design (DDD)** with a **three-layer Clean Architecture**:

```
API Layer → Domain Layer → Infrastructure Layer
```

**Layer responsibilities:**

1. **API Layer** (`src/api/`): HTTP handling, request/response validation, routing
2. **Domain Layer** (`src/domain/`): Pure business logic, entities with behavior, service classes
3. **Infrastructure Layer** (`src/infrastructure/`): Database access, external APIs, file storage

**Key DDD tactical patterns used:**
- **Entities**: Objects with identity and behavior (User, Task, Attachment)
- **Value Objects**: Immutable types (TaskStatus, TaskPriority enums)
- **Repository Pattern**: Abstract data access behind interfaces
- **Domain Services**: Business logic that spans multiple entities

## Consequences

### Positive

- **Testability**: Domain layer can be unit tested without database or HTTP concerns
- **Maintainability**: Changes to database schema don't affect business logic
- **Clarity**: Each layer has a clear responsibility
- **Flexibility**: Can swap implementations (e.g., different database) without changing domain
- **Onboarding**: New developers understand where code belongs

### Negative

- **Initial complexity**: More files and abstractions than simple CRUD
- **Boilerplate**: Repository interfaces require implementations
- **Learning curve**: Team must understand DDD concepts
- **Over-engineering risk**: Simple features may feel heavyweight

### Neutral

- Requires discipline to maintain layer boundaries
- May need to create ADRs for boundary decisions

## Alternatives Considered

### Alternative 1: Simple MVC / Active Record

**Description:** Routes directly manipulate ORM models, business logic in routes or model methods.

**Pros:**
- Faster initial development
- Less boilerplate
- Familiar to most developers

**Cons:**
- Business logic scattered across routes and models
- Hard to test without database
- Coupling between HTTP and database concerns

**Why not chosen:** Would become unmaintainable as features grow. Testing would require full integration tests.

### Alternative 2: Hexagonal Architecture (Ports and Adapters)

**Description:** Strict separation with explicit port/adapter interfaces for all external concerns.

**Pros:**
- Even cleaner separation than DDD
- Very testable

**Cons:**
- More abstractions than needed for this project size
- Higher learning curve

**Why not chosen:** Over-engineered for current requirements. DDD provides sufficient separation.

### Alternative 3: Microservices

**Description:** Separate services for tasks, auth, attachments, etc.

**Pros:**
- Independent scaling
- Technology flexibility per service

**Cons:**
- Operational complexity (K8s, service mesh)
- Network latency
- Distributed transactions

**Why not chosen:** Premature for a single-team, single-deployment application.

## References

- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Clean Architecture by Robert Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [ADR-0002: Separate ORM and Domain Models](0002-separate-orm-and-domain-models.md)
