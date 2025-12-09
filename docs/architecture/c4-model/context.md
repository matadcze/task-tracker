# C4 Model - Level 1: System Context Diagram

The System Context diagram shows Task Tracker and its relationships with users and external systems.

## System Context Diagram

```mermaid
C4Context
    title System Context Diagram - Task Tracker

    Person(user, "User", "A person who manages their tasks and uses the AI assistant")

    System(tasktracker, "Task Tracker", "Allows users to manage tasks, attach files, and create tasks via natural language chat")

    System_Ext(openai, "OpenAI API", "Provides LLM capabilities for natural language task interpretation and content moderation")
    System_Ext(email, "Email Service", "Future: Sends reminder notifications")
    System_Ext(browser, "Web Browser", "User's web browser for accessing the application")

    Rel(user, browser, "Uses")
    Rel(browser, tasktracker, "Accesses via HTTPS")
    Rel(tasktracker, openai, "Interprets natural language, moderates content", "HTTPS/REST")
    Rel(tasktracker, email, "Sends notifications", "SMTP (Future)")
```

## Alternative Rendering (Standard Mermaid)

```mermaid
flowchart TB
    subgraph External
        User[("User<br/><small>Person managing tasks</small>")]
        OpenAI[("OpenAI API<br/><small>LLM & Moderation</small>")]
        Browser[("Web Browser")]
    end

    subgraph TaskTrackerSystem["Task Tracker System"]
        TT["Task Tracker<br/><small>Task management with<br/>AI-powered chat assistant</small>"]
    end

    User -->|"Uses"| Browser
    Browser -->|"HTTPS"| TT
    TT -->|"REST API<br/>Chat completion<br/>Content moderation"| OpenAI

    style TT fill:#1168bd,stroke:#0b4884,color:#fff
    style User fill:#08427b,stroke:#052e56,color:#fff
    style OpenAI fill:#999999,stroke:#666666,color:#fff
    style Browser fill:#999999,stroke:#666666,color:#fff
```

## Context Description

### Primary Users

| Actor | Description | Interaction |
|-------|-------------|-------------|
| **User** | End user managing personal tasks | Accesses via web browser, creates tasks manually or via chat |

### External Systems

| System | Purpose | Protocol | Notes |
|--------|---------|----------|-------|
| **OpenAI API** | Natural language interpretation, content moderation | HTTPS/REST | Fail-open design - system works without it |
| **Web Browser** | User interface delivery | HTTPS | Modern browsers (Chrome, Firefox, Safari, Edge) |
| **Email Service** | Reminder notifications | SMTP | Future capability |

### System Capabilities

Task Tracker provides:

1. **Task Management** - CRUD operations with search, filtering, sorting, pagination
2. **File Attachments** - Upload, download, and manage files attached to tasks
3. **AI Chat Assistant** - Natural language task creation ("Remind me to...")
4. **Audit Logging** - Immutable record of all user actions
5. **Authentication** - JWT-based with refresh tokens
6. **Scheduled Reminders** - Background job processing for due-soon tasks

## Key Quality Attributes

| Attribute | Requirement |
|-----------|-------------|
| **Availability** | System remains functional if OpenAI is unavailable (fallback to regex) |
| **Security** | JWT authentication, bcrypt passwords, content moderation |
| **Performance** | Rate limiting (100 req/min), async everywhere |
| **Observability** | Prometheus metrics, audit logging, request correlation IDs |

## Data Flow Summary

```
User Request → Frontend → Backend API → Domain Services → Database
                                    ↓
                              [If chat] → OpenAI API (optional)
                                    ↓
                              Response ← Domain Entity ← Repository
```

## Next Level

See [Container Diagram](container.md) for the high-level technology architecture.
