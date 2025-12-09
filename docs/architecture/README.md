# Task Tracker Architecture Documentation

Comprehensive architecture documentation for the Task Tracker application - a production-ready task management platform with AI-powered chat assistant.

## Documentation Structure

```
docs/architecture/
├── README.md                    # This file - documentation index
├── c4-model/                    # C4 Model diagrams
│   ├── context.md              # System Context (Level 1)
│   ├── container.md            # Container diagram (Level 2)
│   └── component.md            # Component diagram (Level 3)
├── arc42/                       # Arc42 architecture template
│   └── arc42-documentation.md  # Complete Arc42 documentation
├── adr/                         # Architecture Decision Records
│   ├── 0001-use-domain-driven-design.md
│   ├── 0002-separate-orm-and-domain-models.md
│   ├── 0003-jwt-authentication-strategy.md
│   ├── 0004-celery-for-background-jobs.md
│   ├── 0005-fail-open-llm-integration.md
│   └── template.md             # ADR template
└── diagrams/                    # Additional diagrams
    ├── data-flow.md            # Data flow diagrams
    ├── sequence-diagrams.md    # Key sequence diagrams
    └── security-architecture.md # Security documentation
```

## Quick Links

### C4 Model (Recommended Starting Point)
- [System Context](c4-model/context.md) - Bird's eye view of the system
- [Container Diagram](c4-model/container.md) - High-level technology choices
- [Component Diagram](c4-model/component.md) - Internal structure

### Arc42 Documentation
- [Complete Arc42 Documentation](arc42/arc42-documentation.md) - Comprehensive architecture documentation

### Architecture Decision Records (ADRs)
- [ADR-0001: Domain-Driven Design](adr/0001-use-domain-driven-design.md)
- [ADR-0002: Separate ORM and Domain Models](adr/0002-separate-orm-and-domain-models.md)
- [ADR-0003: JWT Authentication Strategy](adr/0003-jwt-authentication-strategy.md)
- [ADR-0004: Celery for Background Jobs](adr/0004-celery-for-background-jobs.md)
- [ADR-0005: Fail-Open LLM Integration](adr/0005-fail-open-llm-integration.md)

### Diagrams
- [Data Flow Diagrams](diagrams/data-flow.md)
- [Sequence Diagrams](diagrams/sequence-diagrams.md)
- [Security Architecture](diagrams/security-architecture.md)

## Architecture Overview

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS |
| **Backend API** | FastAPI, Python 3.11+, Pydantic |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 (async) |
| **Cache/Broker** | Redis 7 |
| **Background Jobs** | Celery + Celery Beat |
| **AI Integration** | OpenAI API (GPT + Moderation) |
| **Monitoring** | Prometheus, Grafana |
| **Containerization** | Docker, Docker Compose |

### Key Architectural Patterns

1. **Domain-Driven Design (DDD)** - Clear separation between domain logic and infrastructure
2. **Clean Architecture** - Three-layer architecture (API → Domain → Infrastructure)
3. **Repository Pattern** - Abstraction over data access
4. **Dependency Injection** - Constructor injection via FastAPI's `Depends()`
5. **Rich Domain Models** - Entities with behavior, not just data containers

### System Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                        Task Tracker System                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Frontend  │  │   Backend   │  │   Background Workers    │  │
│  │   (Next.js) │  │   (FastAPI) │  │   (Celery)              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│          │               │                    │                  │
│          └───────────────┼────────────────────┘                  │
│                          │                                       │
│                    ┌─────┴─────┐                                │
│                    │ PostgreSQL │                                │
│                    │   Redis    │                                │
│                    └───────────┘                                 │
└─────────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────┴─────┐ ┌────┴────┐ ┌────┴────┐
        │  OpenAI   │ │ Browser │ │  Users  │
        │    API    │ │         │ │         │
        └───────────┘ └─────────┘ └─────────┘
```

## Rendering Diagrams

All diagrams in this documentation use **Mermaid** syntax and can be rendered:

1. **GitHub/GitLab**: Automatically rendered in markdown preview
2. **VS Code**: Install "Mermaid Preview" extension
3. **CLI**: Use `mmdc` (Mermaid CLI) to generate images
4. **Online**: Paste code at [mermaid.live](https://mermaid.live)

## Documentation Maintenance

- **ADRs**: Create new ADR for any significant architectural decision
- **Diagrams**: Update when adding new services or significant changes
- **Arc42**: Review quarterly or after major releases

## Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Developer guide and codebase instructions
- [README.md](../../README.md) - Project overview and quick start
- [QUESTIONS.md](../../QUESTIONS.md) - Interview preparation questions
