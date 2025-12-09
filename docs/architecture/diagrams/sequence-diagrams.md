# Sequence Diagrams

This document contains detailed sequence diagrams for key system interactions.

## 1. User Registration

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as API Layer
    participant AS as AuthService
    participant PH as PasswordHasher
    participant UR as UserRepository
    participant AR as AuditRepository
    participant DB as PostgreSQL

    C->>A: POST /api/v1/auth/register<br/>{email, password, full_name}

    A->>A: Validate RegisterRequest schema

    A->>AS: register(email, password, full_name)

    AS->>UR: get_by_email(email)
    UR->>DB: SELECT * FROM users WHERE email = ?
    DB-->>UR: null (not found)
    UR-->>AS: None

    AS->>PH: hash_password(password)
    PH-->>AS: bcrypt hash

    AS->>AS: Create User entity

    AS->>UR: create(user)
    UR->>DB: INSERT INTO users (...)
    DB-->>UR: user_id
    UR-->>AS: User entity

    AS->>AR: create(AuditEvent)
    AR->>DB: INSERT INTO audit_events (...)
    DB-->>AR: event_id

    AS-->>A: User entity

    A->>A: Convert to UserResponse

    A-->>C: 201 Created<br/>{id, email, full_name, ...}
```

## 2. User Login with Token Generation

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as API Layer
    participant AS as AuthService
    participant UR as UserRepository
    participant PH as PasswordHasher
    participant JWT as JWTProvider
    participant TR as RefreshTokenRepository
    participant AR as AuditRepository
    participant DB as PostgreSQL

    C->>A: POST /api/v1/auth/login<br/>{email, password}

    A->>AS: login(email, password)

    AS->>UR: get_by_email(email)
    UR->>DB: SELECT * FROM users WHERE email = ?
    DB-->>UR: UserModel
    UR-->>AS: User entity

    AS->>AS: Check user.can_authenticate()

    AS->>PH: verify_password(password, hash)
    PH-->>AS: true

    AS->>JWT: create_access_token(user_id)
    JWT-->>AS: access_token (15min expiry)

    AS->>JWT: create_refresh_token(user_id)
    JWT-->>AS: refresh_token (7day expiry)

    AS->>PH: hash_token(refresh_token)
    PH-->>AS: token_hash

    AS->>TR: create(RefreshToken)
    TR->>DB: INSERT INTO refresh_tokens (...)
    DB-->>TR: token_id

    AS->>AR: create(AuditEvent LOGIN)
    AR->>DB: INSERT INTO audit_events (...)

    AS-->>A: TokenResponse

    A-->>C: 200 OK<br/>{access_token, refresh_token, token_type, expires_in}

    Note over C: Store tokens in localStorage
```

## 3. Authenticated API Request

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant MW as Middleware
    participant RL as RateLimiter
    participant RD as Redis
    participant A as API Layer
    participant JWT as JWTProvider
    participant S as Service
    participant R as Repository
    participant DB as PostgreSQL

    C->>MW: GET /api/v1/tasks<br/>Authorization: Bearer <token>

    MW->>MW: Add correlation ID

    MW->>RL: check_rate_limit(client_ip)
    RL->>RD: INCR rate:ip:window
    RD-->>RL: count
    RL-->>MW: allowed (count < 100)

    MW->>A: Forward request

    A->>JWT: get_user_id_from_token(token)
    JWT->>JWT: Decode & verify signature
    JWT->>JWT: Check expiration
    JWT->>JWT: Validate type = "access"
    JWT-->>A: user_id (UUID)

    A->>S: list_tasks(owner_id=user_id, ...)

    S->>R: list(owner_id, filters...)
    R->>DB: SELECT * FROM tasks WHERE owner_id = ?
    DB-->>R: [TaskModel, ...]
    R->>R: Convert to entities
    R-->>S: ([Task, ...], total_count)

    S-->>A: (tasks, count)

    A->>A: Build TaskListResponse

    A-->>C: 200 OK<br/>{tasks: [...], total: N, page: 1}
```

## 4. Task Creation with Tags

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as API Layer
    participant TS as TaskService
    participant TagS as TagService
    participant TagR as TagRepository
    participant TR as TaskRepository
    participant AR as AuditRepository
    participant M as Metrics
    participant DB as PostgreSQL

    C->>A: POST /api/v1/tasks<br/>{title, description, tags: ["work", "urgent"]}

    A->>A: Validate TaskCreate schema

    A->>TS: create_task(owner_id, title, ..., tags)

    Note over TS: Start timer for metrics

    TS->>TS: Validate title not empty
    TS->>TS: Validate title length <= 500

    TS->>TagS: ensure_tags_exist(["work", "urgent"])

    loop For each tag
        TagS->>TagS: normalize(tag) → lowercase, strip
        TagS->>TagR: get_or_create(normalized_tag)
        TagR->>DB: SELECT * FROM tags WHERE name = ?
        alt Tag exists
            DB-->>TagR: TagModel
        else Tag not exists
            TagR->>DB: INSERT INTO tags (name)
            DB-->>TagR: TagModel
        end
        TagR-->>TagS: Tag entity
    end

    TagS-->>TS: [Tag entities]

    TS->>TS: Create Task entity with tag names

    TS->>TR: create(task)
    TR->>DB: INSERT INTO tasks (...)
    TR->>DB: INSERT INTO task_tags (task_id, tag_id)
    DB-->>TR: task_id
    TR-->>TS: Task entity

    TS->>AR: create(AuditEvent TASK_CREATED)
    AR->>DB: INSERT INTO audit_events (...)

    TS->>M: track_task_operation("create", "success", duration)
    TS->>M: increment_task_count(TODO)
    TS->>M: track_audit_event("TASK_CREATED")

    TS-->>A: Task entity

    A-->>C: 201 Created<br/>{id, title, tags: ["work", "urgent"], ...}
```

## 5. Chat Message Processing

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as API Layer
    participant CS as ChatService
    participant SC as SafetyChecker
    participant OAM as OpenAI Moderation
    participant PI as Primary Interpreter
    participant OAC as OpenAI Chat
    participant FI as Fallback Interpreter
    participant TS as TaskService
    participant DB as PostgreSQL

    C->>A: POST /api/v1/chat/messages<br/>{message: "Remind me to buy groceries"}

    A->>CS: create_task_from_message(user_id, message)

    %% Safety Check
    CS->>SC: check(message)
    SC->>OAM: POST /v1/moderations<br/>{input: message}

    alt OpenAI available
        OAM-->>SC: {flagged: false}
        SC-->>CS: SafetyCheckResult(flagged=false)
    else OpenAI unavailable
        OAM--xSC: Timeout/Error
        Note over SC: Fail open - skip moderation
        SC-->>CS: Continue without check
    end

    %% Interpretation
    CS->>PI: interpret(message)
    PI->>OAC: POST /v1/chat/completions<br/>{messages: [...]}

    alt OpenAI available
        OAC-->>PI: {title: "Buy groceries", description: null}
        PI-->>CS: TaskInterpretation
    else OpenAI unavailable
        OAC--xPI: Timeout/Error
        CS->>FI: interpret(message)
        FI->>FI: Regex match "remind me to (.*)"
        FI-->>CS: TaskInterpretation(title="buy groceries")
    end

    %% Task Creation
    CS->>TS: create_task(user_id, title, description)
    TS->>DB: INSERT INTO tasks (...)
    DB-->>TS: Task entity
    TS-->>CS: Task

    CS->>CS: Build reply message

    CS-->>A: ChatMessageResult

    A-->>C: 200 OK<br/>{reply: "Created task...", created_task: {...}}
```

## 6. File Upload

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as API Layer
    participant TS as TaskService
    participant TR as TaskRepository
    participant AS as AttachmentService
    participant LS as LocalStorage
    participant AttR as AttachmentRepository
    participant AR as AuditRepository
    participant DB as PostgreSQL
    participant FS as File System

    C->>A: POST /api/v1/tasks/{task_id}/attachments<br/>Content-Type: multipart/form-data

    A->>TS: get_task_by_id(task_id, user_id)
    TS->>TR: get_by_id(task_id)
    TR->>DB: SELECT * FROM tasks WHERE id = ?
    DB-->>TR: TaskModel
    TR-->>TS: Task entity

    TS->>TS: Check task.can_be_modified_by(user_id)
    TS-->>A: Task (authorized)

    A->>AS: upload_attachment(task_id, file, user_id)

    AS->>AS: Validate file size <= 10MB
    AS->>AS: Generate storage path

    AS->>LS: save(file_content, path)
    LS->>FS: Write file to disk
    FS-->>LS: Success
    LS-->>AS: storage_path

    AS->>AS: Create Attachment entity

    AS->>AttR: create(attachment)
    AttR->>DB: INSERT INTO attachments (...)
    DB-->>AttR: attachment_id
    AttR-->>AS: Attachment entity

    AS->>AR: create(AuditEvent ATTACHMENT_UPLOADED)
    AR->>DB: INSERT INTO audit_events (...)

    AS-->>A: Attachment entity

    A-->>C: 201 Created<br/>{id, filename, size_bytes, ...}
```

## 7. Token Refresh

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as API Layer
    participant JWT as JWTProvider
    participant PH as PasswordHasher
    participant TR as RefreshTokenRepository
    participant DB as PostgreSQL

    C->>A: POST /api/v1/auth/refresh<br/>{refresh_token: "..."}

    A->>JWT: verify_token(refresh_token, type="refresh")
    JWT->>JWT: Decode token
    JWT->>JWT: Verify signature
    JWT->>JWT: Check expiration
    JWT->>JWT: Validate type = "refresh"
    JWT-->>A: payload {sub: user_id}

    A->>PH: hash_token(refresh_token)
    PH-->>A: token_hash

    A->>TR: get_by_token_hash(token_hash)
    TR->>DB: SELECT * FROM refresh_tokens WHERE token_hash = ?
    DB-->>TR: RefreshTokenModel

    A->>A: Check not revoked

    A->>TR: revoke_by_token_hash(token_hash)
    TR->>DB: UPDATE refresh_tokens SET revoked = true

    A->>JWT: create_access_token(user_id)
    JWT-->>A: new_access_token

    A->>JWT: create_refresh_token(user_id)
    JWT-->>A: new_refresh_token

    A->>PH: hash_token(new_refresh_token)
    PH-->>A: new_token_hash

    A->>TR: create(new RefreshToken)
    TR->>DB: INSERT INTO refresh_tokens (...)

    A-->>C: 200 OK<br/>{access_token, refresh_token, ...}
```

## 8. Background Reminder Processing

```mermaid
sequenceDiagram
    autonumber
    participant Beat as Celery Beat
    participant Redis as Redis Queue
    participant Worker as Celery Worker
    participant RS as ReminderService
    participant TR as TaskRepository
    participant RR as ReminderLogRepository
    participant DB as PostgreSQL

    Note over Beat: Every 10 minutes (configurable)

    Beat->>Redis: Enqueue "reminders.send_due_soon"

    Worker->>Redis: Dequeue task

    Worker->>RS: send_due_soon_reminders(window_hours=24)

    RS->>RS: Calculate time window<br/>now to now + 24 hours

    RS->>TR: list_due_between(due_after, due_before)
    TR->>DB: SELECT * FROM tasks<br/>WHERE due_date BETWEEN ? AND ?<br/>AND status != 'done'
    DB-->>TR: [TaskModel, ...]
    TR-->>RS: [Task entities]

    loop For each due task
        RS->>RR: get_by_task_and_type(task_id, DUE_SOON)
        RR->>DB: SELECT * FROM reminder_logs<br/>WHERE task_id = ? AND reminder_type = ?
        DB-->>RR: ReminderLogModel or null

        alt Reminder not sent yet
            RS->>RS: Create ReminderLog entity
            RS->>RR: create(reminder_log)
            RR->>DB: INSERT INTO reminder_logs (...)
            Note over RS: Log reminder sent (future: send email)
            RS->>RS: processed_count++
        else Already reminded
            Note over RS: Skip (idempotent)
        end
    end

    RS-->>Worker: processed_count

    Worker->>Redis: Store result

    Note over Worker: Task complete
```

## 9. Account Deletion

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as API Layer
    participant AS as AuthService
    participant TS as TaskService
    participant AttS as AttachmentService
    participant TR as TaskRepository
    participant UR as UserRepository
    participant RTR as RefreshTokenRepository
    participant AR as AuditRepository
    participant DB as PostgreSQL

    C->>A: DELETE /api/v1/auth/me<br/>Authorization: Bearer <token>

    A->>AS: delete_account(user_id)

    %% Revoke all tokens
    AS->>RTR: revoke_by_user_id(user_id)
    RTR->>DB: UPDATE refresh_tokens SET revoked = true<br/>WHERE user_id = ?

    %% Delete user's tasks (cascades to attachments)
    AS->>TS: delete_tasks_for_owner(user_id)
    TS->>TR: delete_by_owner(user_id)
    TR->>DB: DELETE FROM tasks WHERE owner_id = ?
    Note over DB: CASCADE deletes attachments,<br/>reminder_logs, task_tags

    %% Audit before deletion
    AS->>AR: create(AuditEvent USER_DELETED)
    AR->>DB: INSERT INTO audit_events (user_id=NULL, ...)
    Note over AR: user_id SET NULL on delete

    %% Delete user
    AS->>UR: delete(user_id)
    UR->>DB: DELETE FROM users WHERE id = ?

    AS-->>A: Success

    A-->>C: 204 No Content

    Note over C: Clear localStorage tokens
```

## Error Handling Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API Layer
    participant S as Service
    participant EH as Exception Handler

    C->>A: Request with invalid data

    A->>S: Service call

    alt Validation Error
        S-->>A: raise ValidationError("message")
        A->>EH: Handle DomainException
        EH-->>C: 400 Bad Request<br/>{error: {code: "ValidationError", message: "..."}}
    else Not Found
        S-->>A: raise NotFoundError("Task not found")
        A->>EH: Handle DomainException
        EH-->>C: 404 Not Found<br/>{error: {code: "NotFoundError", ...}}
    else Authorization Error
        S-->>A: raise AuthorizationError("Not authorized")
        A->>EH: Handle DomainException
        EH-->>C: 403 Forbidden<br/>{error: {code: "AuthorizationError", ...}}
    else Unexpected Error
        S-->>A: raise Exception("...")
        A->>EH: Handle generic Exception
        EH-->>C: 500 Internal Server Error<br/>{error: {code: "InternalServerError", ...}}
    end

    Note over EH,C: All responses include correlation_id
```
