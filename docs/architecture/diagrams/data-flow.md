# Data Flow Diagrams

This document describes how data flows through the Task Tracker system.

## 1. Overall Data Flow

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Browser[Web Browser]
        LocalStorage[(localStorage)]
    end

    subgraph API["API Layer"]
        Routes[Route Handlers]
        Middleware[Middleware Stack]
        Schemas[Pydantic Validation]
    end

    subgraph Domain["Domain Layer"]
        Services[Domain Services]
        Entities[Domain Entities]
    end

    subgraph Infrastructure["Infrastructure Layer"]
        Repos[Repositories]
        Auth[Auth Providers]
        LLM[LLM Integration]
        Storage[File Storage]
    end

    subgraph Data["Data Stores"]
        Postgres[(PostgreSQL)]
        Redis[(Redis)]
        FileSystem[(File System)]
    end

    subgraph External["External"]
        OpenAI[OpenAI API]
    end

    Browser -->|"HTTP Request"| Middleware
    Browser <-->|"Tokens"| LocalStorage
    Middleware -->|"Rate Check"| Redis
    Middleware -->|"Validated Request"| Routes
    Routes -->|"Pydantic Models"| Schemas
    Schemas -->|"Service Call"| Services
    Services -->|"Domain Entities"| Entities
    Services -->|"Repository Call"| Repos
    Repos -->|"SQL Queries"| Postgres
    Services -->|"Token Ops"| Auth
    Auth -->|"Token Verify"| Redis
    Services -->|"Chat Request"| LLM
    LLM -->|"API Call"| OpenAI
    Services -->|"File Ops"| Storage
    Storage -->|"Read/Write"| FileSystem
```

## 2. Request Processing Flow

```mermaid
flowchart LR
    subgraph Request["Incoming Request"]
        HTTP[HTTP Request]
    end

    subgraph Middleware["Middleware Pipeline"]
        direction TB
        M1[Request Logging]
        M2[Correlation ID]
        M3[Rate Limiting]
        M4[Metrics]
        M1 --> M2 --> M3 --> M4
    end

    subgraph Handler["Route Handler"]
        Auth[JWT Validation]
        Validate[Schema Validation]
        Service[Service Call]
    end

    subgraph Response["Response"]
        JSON[JSON Response]
    end

    HTTP --> M1
    M4 --> Auth
    Auth --> Validate
    Validate --> Service
    Service --> JSON
```

## 3. Task Data Flow

### 3.1 Task Creation

```mermaid
flowchart TB
    Client[Client] -->|"POST /tasks<br/>{title, description, ...}"| API[API Route]
    API -->|"TaskCreate schema"| Validate[Pydantic Validation]
    Validate -->|"Valid data"| Service[TaskService.create_task]

    Service -->|"Normalize tags"| TagService[TagService]
    TagService -->|"Get or create"| TagRepo[TagRepository]
    TagRepo -->|"INSERT/SELECT"| DB[(PostgreSQL)]

    Service -->|"Create Task entity"| Entity[Task Entity]
    Service -->|"Save task"| TaskRepo[TaskRepository]
    TaskRepo -->|"INSERT"| DB

    Service -->|"Create audit event"| AuditRepo[AuditRepository]
    AuditRepo -->|"INSERT"| DB

    Service -->|"Track metrics"| Metrics[Prometheus]

    Service -->|"Return Task"| API
    API -->|"TaskResponse"| Client
```

### 3.2 Task Query Flow

```mermaid
flowchart TB
    Client[Client] -->|"GET /tasks?status=todo&page=1"| API[API Route]
    API -->|"Query params"| Validate[Pydantic Validation]
    Validate -->|"Valid filters"| Service[TaskService.list_tasks]

    Service -->|"Build query"| TaskRepo[TaskRepository]
    TaskRepo -->|"SELECT with filters"| DB[(PostgreSQL)]

    DB -->|"TaskModel rows"| TaskRepo
    TaskRepo -->|"Convert to entities"| Convert[_to_entity]
    Convert -->|"Task entities"| Service
    Service -->|"Return list + count"| API
    API -->|"TaskListResponse"| Client

    subgraph Query["SQL Query Components"]
        Where[WHERE clauses]
        Join[JOIN tags]
        Order[ORDER BY]
        Limit[LIMIT/OFFSET]
    end

    TaskRepo --> Where
    TaskRepo --> Join
    TaskRepo --> Order
    TaskRepo --> Limit
```

## 4. Authentication Data Flow

### 4.1 Login Flow

```mermaid
flowchart TB
    Client[Client] -->|"POST /auth/login<br/>{email, password}"| API[Auth Route]
    API -->|"Validate"| Service[AuthService.login]

    Service -->|"Get user by email"| UserRepo[UserRepository]
    UserRepo -->|"SELECT"| DB[(PostgreSQL)]
    DB -->|"User model"| UserRepo
    UserRepo -->|"User entity"| Service

    Service -->|"Verify password"| Hasher[PasswordHasher]
    Hasher -->|"bcrypt.verify"| Service

    Service -->|"Create tokens"| JWT[JWTProvider]
    JWT -->|"Access token (15min)"| Service
    JWT -->|"Refresh token (7d)"| Service

    Service -->|"Store refresh hash"| TokenRepo[RefreshTokenRepository]
    TokenRepo -->|"INSERT"| DB

    Service -->|"Tokens"| API
    API -->|"TokenResponse"| Client
    Client -->|"Store tokens"| LocalStorage[(localStorage)]
```

### 4.2 Token Refresh Flow

```mermaid
flowchart TB
    Client[Client] -->|"POST /auth/refresh<br/>{refresh_token}"| API[Auth Route]

    API -->|"Validate token"| JWT[JWTProvider]
    JWT -->|"Decode & verify"| API

    API -->|"Check revocation"| TokenRepo[RefreshTokenRepository]
    TokenRepo -->|"SELECT by hash"| DB[(PostgreSQL)]

    API -->|"Revoke old token"| TokenRepo
    TokenRepo -->|"UPDATE revoked=true"| DB

    API -->|"Create new tokens"| JWT
    API -->|"Store new refresh"| TokenRepo
    TokenRepo -->|"INSERT"| DB

    API -->|"New tokens"| Client
```

## 5. Chat/LLM Data Flow

```mermaid
flowchart TB
    Client[Client] -->|"POST /chat/messages<br/>{message: 'Remind me to...'}"| API[Chat Route]
    API -->|"ChatMessageRequest"| Service[ChatService]

    subgraph Safety["Safety Check (Optional)"]
        SafetyCheck[SafetyChecker]
        OpenAIMod[OpenAI Moderation API]
        SafetyCheck -->|"POST /moderations"| OpenAIMod
        OpenAIMod -->|"{flagged: bool}"| SafetyCheck
    end

    Service -->|"Check content"| SafetyCheck

    subgraph Interpretation["Task Interpretation"]
        Primary[OpenAI Interpreter]
        Fallback[Regex Interpreter]
        OpenAIChat[OpenAI Chat API]

        Primary -->|"POST /chat/completions"| OpenAIChat
        OpenAIChat -->|"{title, description}"| Primary
    end

    Service -->|"Try primary"| Primary
    Primary -->|"On failure"| Fallback
    Fallback -->|"Regex extract"| Service

    Service -->|"Create task"| TaskService[TaskService]
    TaskService -->|"Save"| DB[(PostgreSQL)]

    Service -->|"ChatMessageResult"| API
    API -->|"{reply, created_task}"| Client
```

## 6. File Attachment Data Flow

### 6.1 Upload Flow

```mermaid
flowchart TB
    Client[Client] -->|"POST /tasks/{id}/attachments<br/>multipart/form-data"| API[Attachment Route]

    API -->|"Validate task access"| TaskService[TaskService]
    TaskService -->|"Check ownership"| TaskRepo[TaskRepository]
    TaskRepo -->|"SELECT"| DB[(PostgreSQL)]

    API -->|"Upload file"| AttachService[AttachmentService]

    AttachService -->|"Validate size/type"| Validate[Validation]
    AttachService -->|"Save to disk"| Storage[LocalStorage]
    Storage -->|"Write file"| FileSystem[(File System)]

    AttachService -->|"Create entity"| AttachRepo[AttachmentRepository]
    AttachRepo -->|"INSERT"| DB

    AttachService -->|"Audit log"| AuditRepo[AuditRepository]
    AuditRepo -->|"INSERT"| DB

    AttachService -->|"Attachment"| API
    API -->|"AttachmentResponse"| Client
```

### 6.2 Download Flow

```mermaid
flowchart TB
    Client[Client] -->|"GET /tasks/{id}/attachments/{aid}"| API[Attachment Route]

    API -->|"Validate access"| TaskService[TaskService]
    API -->|"Get attachment"| AttachRepo[AttachmentRepository]
    AttachRepo -->|"SELECT"| DB[(PostgreSQL)]

    API -->|"Read file"| Storage[LocalStorage]
    Storage -->|"Read from disk"| FileSystem[(File System)]

    Storage -->|"File bytes"| API
    API -->|"StreamingResponse"| Client
```

## 7. Background Job Data Flow

```mermaid
flowchart TB
    subgraph Scheduler["Celery Beat"]
        Beat[Beat Scheduler]
        Schedule[(Schedule Config)]
        Beat -->|"Check schedule"| Schedule
    end

    subgraph Broker["Redis"]
        Queue[(Task Queue)]
    end

    subgraph Worker["Celery Worker"]
        Consumer[Task Consumer]
        ReminderTask[send_due_soon_reminders]
    end

    subgraph Domain["Domain Layer"]
        ReminderService[ReminderService]
        TaskRepo[TaskRepository]
        ReminderRepo[ReminderLogRepository]
    end

    Beat -->|"Enqueue task"| Queue
    Consumer -->|"Dequeue task"| Queue
    Consumer -->|"Execute"| ReminderTask

    ReminderTask -->|"Call service"| ReminderService
    ReminderService -->|"Find due tasks"| TaskRepo
    TaskRepo -->|"SELECT due_date BETWEEN"| DB[(PostgreSQL)]

    ReminderService -->|"Check existing"| ReminderRepo
    ReminderRepo -->|"SELECT"| DB

    ReminderService -->|"Log reminder"| ReminderRepo
    ReminderRepo -->|"INSERT"| DB

    ReminderService -->|"Count processed"| ReminderTask
    ReminderTask -->|"Result"| Queue
```

## 8. Metrics Data Flow

```mermaid
flowchart LR
    subgraph Application["Application"]
        Service[Services]
        Middleware[Middleware]
        Metrics[Prometheus Metrics]

        Service -->|"track_*_operation"| Metrics
        Middleware -->|"request metrics"| Metrics
    end

    subgraph Endpoint["Metrics Endpoint"]
        Export["/metrics"]
        Metrics -->|"Expose"| Export
    end

    subgraph Monitoring["Monitoring Stack"]
        Prometheus[(Prometheus)]
        Grafana[Grafana]

        Export -->|"Scrape (15s)"| Prometheus
        Prometheus -->|"Query"| Grafana
    end

    subgraph Display["Dashboards"]
        Dashboard[Grafana Dashboard]
        Grafana -->|"Visualize"| Dashboard
    end
```

## Data Transformations Summary

| Layer | Input Format | Output Format | Transformation |
|-------|--------------|---------------|----------------|
| API → Domain | Pydantic Schema | Domain Entity | Schema validation |
| Domain → Infra | Domain Entity | ORM Model | Entity to model |
| Infra → Database | ORM Model | SQL | SQLAlchemy serialization |
| Database → Infra | SQL Result | ORM Model | SQLAlchemy deserialization |
| Infra → Domain | ORM Model | Domain Entity | `_to_entity()` |
| Domain → API | Domain Entity | Response Schema | `model_validate()` |
