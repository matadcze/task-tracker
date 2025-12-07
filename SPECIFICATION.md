## 1. Product Overview

**Product:** Task Tracker
**Goal:** Let authenticated users manage personal tasks with attachments, reminders, and audit logs, built with Clean Architecture and modern Python + React stack.

**Key behaviors:**

* Users authenticate securely.
* Users can see all tasks, but **may only create/edit/delete their own tasks**.
* Users can upload attachments to their tasks.
* System sends (logs) “reminder sent” events for tasks due in next 24 hours.
* Every key action is audit-logged.
* API is observable (logs, metrics, health checks) and rate-limited.

---

## 2. Technology & High-Level Architecture

### 2.1 Tech Stack (proposed)

You can swap pieces if needed, but this spec assumes:

* **Backend API:** Python, FastAPI
* **Worker:** Python, same domain layer, scheduling via Celery/Redis or APScheduler
* **DB:** PostgreSQL
* **Cache / Queue:** Redis (rate limiting + Celery broker)
* **ORM:** SQLAlchemy + Alembic migrations
* **Auth:** JWT-based (access + refresh tokens) with OAuth2 password flow
* **Frontend:** React + TypeScript, Vite or Create React App
* **API Docs:** OpenAPI/Swagger (FastAPI auto-generated)
* **Containerization:** Docker + docker-compose
* **Metrics:** Prometheus-style metrics or simple in-memory counters exposed at `/metrics`
* **Logging:** JSON structured logs

### 2.2 Clean Architecture Layers

Logical layering:

* **Domain (Core)**

  * Entities: `User`, `Task`, `Attachment`, `AuditEvent`, `ReminderLog`, `Tag`
  * Value objects, enums: `TaskStatus`, `TaskPriority`
  * Repository interfaces (ports)
  * Domain services and business rules
* **Application (Use Cases)**

  * Use cases: `CreateTask`, `UpdateTask`, `DeleteTask`, `SearchTasks`, `UploadAttachment`, `SendReminders`, etc.
  * Orchestrates domain + infrastructure through interfaces.
* **Infrastructure**

  * DB implementations of repositories (SQLAlchemy)
  * JWT provider, password hasher
  * File storage adapter (local filesystem / S3-like)
  * Rate limiter adapter (Redis)
  * Message queue / scheduler adapter (Celery/Redis)
* **Interface (Delivery)**

  * HTTP API controllers (FastAPI routes)
  * Background worker entrypoints (Celery tasks)
  * Frontend React app (consuming HTTP API)

### 2.3 Service Topology

**docker-compose services:**

* `api`: FastAPI app
* `worker`: Celery worker (and beat/scheduler)
* `frontend`: React dev server / built static site behind Nginx
* `db`: PostgreSQL
* `redis`: Redis (rate limiting, Celery broker)
* Optionally: `prometheus`, `grafana` if you want real metrics dashboards

---

## 3. Data Model

### 3.1 Core Tables

**User**

* `id` (UUID, PK)
* `email` (string, unique)
* `password_hash` (string)
* `full_name` (string, nullable)
* `is_active` (boolean, default true)
* `created_at` (timestamp)
* `updated_at` (timestamp)

**Task**

* `id` (UUID, PK)
* `owner_id` (UUID, FK → User.id)
* `title` (string, not null)
* `description` (text, nullable)
* `status` (enum: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`)
* `priority` (enum: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
* `due_date` (timestamp, nullable)
* `created_at` (timestamp)
* `updated_at` (timestamp)

**Tag**

* `id` (UUID, PK)
* `name` (string, unique)

**TaskTag (join table)**

* `task_id` (UUID, FK → Task.id)
* `tag_id` (UUID, FK → Tag.id)
* PK: `(task_id, tag_id)`

**Attachment**

* `id` (UUID, PK)
* `task_id` (UUID, FK → Task.id)
* `filename` (string)
* `content_type` (string)
* `size_bytes` (int)
* `storage_path` (string) – path or key to file in underlying storage
* `created_at` (timestamp)

**AuditEvent**

* `id` (UUID, PK)
* `user_id` (UUID, FK → User.id, nullable e.g. for system events)
* `event_type` (string enum: `TASK_CREATED`, `TASK_UPDATED`, `TASK_DELETED`, `ATTACHMENT_ADDED`, `ATTACHMENT_REMOVED`, `REMINDER_SENT`, `LOGIN`, `PASSWORD_CHANGED`)
* `task_id` (UUID, nullable)
* `attachment_id` (UUID, nullable)
* `details` (JSONB) – arbitrary metadata (diffs, old/new status, etc.)
* `created_at` (timestamp)

**ReminderLog**

* `id` (UUID, PK)
* `task_id` (UUID, FK → Task.id)
* `reminder_type` (string enum: `DUE_SOON`)
* `sent_at` (timestamp)
* Unique constraint: `(task_id, reminder_type)`

**RefreshToken (optional, if you want server-side revocation)**

* `id` (UUID, PK)
* `user_id` (UUID, FK → User.id)
* `token_hash` (string)
* `expires_at` (timestamp)
* `revoked` (bool)

---

## 4. Authentication & Authorization

### 4.1 Auth Flow (JWT-based)

* **Login (`POST /auth/login`)**

  * Inputs: `email`, `password`
  * Verify password; if valid, issue:

    * Access token (JWT, short-lived, e.g. 15 min)
    * Refresh token (JWT or opaque token, longer-lived)
  * Store refresh token hash in DB if you want revocation.

* **Refresh (`POST /auth/refresh`)**

  * Inputs: refresh token
  * Validate; if valid, return new access token (and optionally new refresh token).

* **Change Password (`POST /auth/change-password`)**

  * Inputs: current password, new password.
  * Require valid access token.
  * On success, invalidate existing refresh tokens (optional).

* **Me (`GET /auth/me`)**

  * Returns basic user profile info for current token.

### 4.2 Password & Security

* Passwords hashed with Argon2 or bcrypt.
* Use strong JWT signing key, HS256 or RS256.
* Include `sub` (user id), `exp`, maybe `scope` in JWT claims.

### 4.3 Authorization Rules

* **Read:**

  * Users can read tasks of all users (`GET /tasks`, `GET /tasks/{id}`).
* **Write:**

  * Only owner of a task can:

    * Update (`PUT/PATCH /tasks/{id}`)
    * Delete (`DELETE /tasks/{id}`)
    * Add/remove attachments (`POST/DELETE /tasks/{id}/attachments`)
* Worker actions:

  * Consider worker “system” user id for audit events, or `user_id = null` + `details.system = true`.

---

## 5. API Specification (HTTP)

### 5.1 Common

* Base URL: `/api/v1`
* Auth: `Authorization: Bearer <access_token>`
* Content-Type: `application/json` (except file uploads)
* Pagination: query params `page` (1-based), `page_size` (default 20, max 100)
* Sorting: `sort=field:direction`, e.g. `sort=due_date:asc` (can support multiple separated by commas)

### 5.2 Error Response Format

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task not found",
    "details": {},
    "correlation_id": "b123e456..."
  }
}
```

* `correlation_id` generated per request or taken from `X-Correlation-ID` header.

---

### 5.3 Auth Endpoints

1. **POST `/auth/register`** (optional for demo, or seed users)

   * Req: `{ "email": "string", "password": "string", "full_name": "string?" }`
   * Res: `{ "id": "...", "email": "...", "full_name": "..." }`

2. **POST `/auth/login`**

   * Req: `{ "email": "...", "password": "..." }`
   * Res:

     ```json
     {
       "access_token": "...",
       "refresh_token": "...",
       "token_type": "bearer",
       "expires_in": 900
     }
     ```

3. **POST `/auth/refresh`**

   * Req: `{ "refresh_token": "..." }`
   * Res: same as login access token fields.

4. **GET `/auth/me`**

   * Res: `{ "id": "...", "email": "...", "full_name": "...", "created_at": "..." }`

5. **POST `/auth/change-password`**

   * Req: `{ "current_password": "...", "new_password": "..." }`
   * Res: `204 No Content`

---

### 5.4 Task Endpoints

**Task JSON representation:**

```json
{
  "id": "...",
  "owner_id": "...",
  "title": "string",
  "description": "string",
  "status": "TODO",
  "priority": "MEDIUM",
  "due_date": "2025-12-31T10:00:00Z",
  "tags": ["backend", "urgent"],
  "created_at": "...",
  "updated_at": "..."
}
```

1. **POST `/tasks`**

   * Req:

     ```json
     {
       "title": "string",
       "description": "string?",
       "status": "TODO|IN_PROGRESS|DONE|BLOCKED?",
       "priority": "LOW|MEDIUM|HIGH|CRITICAL?",
       "due_date": "ISO8601?",
       "tags": ["string", ...]  // tag names
     }
     ```
   * Res: `201 Created` with Task JSON.
   * Audit: `TASK_CREATED`.

2. **GET `/tasks`** (list/search/filter)

   * Query params:

     * `search`: text search in title/description
     * `status`: single or multi (e.g. `status=TODO,IN_PROGRESS`)
     * `priority`: same pattern
     * `tags`: `tags=backend,urgent`
     * `due_from`: ISO date/time
     * `due_to`: ISO date/time
     * `sort`: e.g. `sort=due_date:asc,priority:desc`
     * `page`, `page_size`
   * Res:

     ```json
     {
       "items": [ /* Task JSON */ ],
       "page": 1,
       "page_size": 20,
       "total": 42
     }
     ```

3. **GET `/tasks/{task_id}`**

   * Res: Task JSON + attachments summaries:

     ```json
     {
       "task": { ... },
       "attachments": [
         {
           "id": "...",
           "filename": "...",
           "size_bytes": 1234,
           "created_at": "..."
         }
       ]
     }
     ```

4. **PUT `/tasks/{task_id}`** (full update)
   or **PATCH `/tasks/{task_id}`** (partial)

   * Req body similar to create.
   * Enforce: only owner can modify.
   * Res: updated Task JSON.
   * Audit: `TASK_UPDATED` (include changed fields in `details`).

5. **DELETE `/tasks/{task_id}`**

   * Enforce: only owner.
   * Res: `204 No Content`.
   * Audit: `TASK_DELETED`.

---

### 5.5 Attachments

1. **POST `/tasks/{task_id}/attachments`**

   * Content-Type: `multipart/form-data`
   * Fields:

     * `file`: binary file
   * Enforce: only owner.
   * Store file via storage adapter.
   * Res:

     ```json
     {
       "id": "...",
       "filename": "...",
       "content_type": "...",
       "size_bytes": 12345,
       "created_at": "..."
     }
     ```
   * Audit: `ATTACHMENT_ADDED`.

2. **GET `/tasks/{task_id}/attachments`**

   * Res: list of attachments (no file data).

3. **GET `/attachments/{attachment_id}/download`**

   * Returns file stream (Content-Disposition: attachment).
   * All users can download if they can view the task (as per requirement: can view all tasks).

4. **DELETE `/attachments/{attachment_id}`**

   * Resolve attachment → task → owner
   * Only owner can delete.
   * Deletes record + underlying file.
   * Audit: `ATTACHMENT_REMOVED`.

---

### 5.6 Audit & Monitoring (API)

1. **GET `/audit-events`** (admin/demo; optional)

   * Filter by `user_id`, `task_id`, `event_type`, date range.
   * Exposed read-only.

2. **GET `/health/live`**

   * Returns liveness status: `{ "status": "ok" }`.

3. **GET `/health/ready`**

   * Checks DB connection, Redis, etc.
   * Returns:

     ```json
     {
       "status": "ok",
       "components": {
         "db": "up",
         "redis": "up",
         "worker": "unknown|up"
       }
     }
     ```

4. **GET `/metrics`**

   * Text/plain Prometheus exposition or JSON:

     * `http_requests_total{path,method,status}`
     * `http_request_duration_seconds{path,method}`
     * `reminders_processed_total`
     * `errors_total{type}`

---

### 5.7 Rate Limiting

* Implement middleware using Redis.
* Keys:

  * If authenticated: `user:<user_id>:rate`
  * Else: `ip:<ip>:rate`
* Policy example:

  * 100 requests / 1 min per user/IP.
* On exceed:

  * HTTP 429 with standard error format + headers:

    * `Retry-After`
    * `X-RateLimit-Limit`
    * `X-RateLimit-Remaining`

---

## 6. Background Worker / Notifications

### 6.1 Reminder Behavior

* Runs every 5–10 minutes.
* Query tasks:

  * `status != DONE`
  * `due_date BETWEEN now AND now + 24h`
  * No existing `ReminderLog` with `(task_id, 'DUE_SOON')`.
* For each matching task:

  * Log reminder:

    * Create `ReminderLog` row (unique constraint ensures idempotence).
    * Create `AuditEvent` with type `REMINDER_SENT` and `details` containing due_date, etc.
  * (Optional) send email or real notification (for now, requirement says just log “reminder sent”).

### 6.2 Idempotence & Fault Tolerance

* Idempotence via **DB-level unique constraint** on `(task_id, reminder_type)`.
* If worker crashes mid-run:

  * Already-inserted `ReminderLog` prevents duplicates.
* Use Celery task retries for transient DB/Redis errors.
* Worker health:

  * Worker writes heartbeat to Redis or DB every N seconds.
  * API `/health/ready` can read that.

---

## 7. Logging & Observability

### 7.1 Structured Logging

* Use JSON logs:

  * Fields: `timestamp`, `level`, `message`, `logger`, `correlation_id`, `user_id`, `path`, `method`, `status`, `latency_ms`.
* Middleware:

  * Generate `correlation_id` if not present; propagate to:

    * Response header `X-Correlation-ID`
    * All logs per request
  * Worker:

    * Generate per job; propagate to logs and records.

### 7.2 Metrics

* HTTP middleware:

  * Increment `http_requests_total` by path template + method.
  * Measure duration.
  * Increment error counters when status >= 400.
* Worker:

  * Counter `reminders_processed_total`
  * Counter `reminders_failed_total`

---

## 8. Error Handling & Resilience

* Centralized exception handler mapping domain/infrastructure errors to HTTP status + error codes:

  * `ValidationError` → 400
  * `AuthenticationError` → 401
  * `AuthorizationError` → 403
  * `NotFoundError` → 404
  * `RateLimitExceeded` → 429
  * `InternalError` → 500
* Ensure all errors include `correlation_id`.
* Retry policies:

  * Celery automatic retry on transient DB/Redis failures with backoff.

---

## 9. Frontend Specification (React)

### 9.1 Pages / Routes

Using React Router:

* `/login`
* `/tasks`
* `/tasks/new`
* `/tasks/:taskId`
* `/tasks/:taskId/edit`
* `/change-password`

Optionally wrap with layout: header (user info + logout), main content, notifications.

### 9.2 State Management

* Use React Query (TanStack Query) for API calls.
* Store auth tokens in:

  * In-memory + localStorage for persistence.
* Axios/fetch wrapper with interceptor:

  * Automatically attach `Authorization` header.
  * On 401, try refresh flow; if refresh fails, redirect to `/login`.
  * Extract `X-Correlation-ID` from responses for debug (nice-to-have).

### 9.3 Screens

**Login Page**

* Form: email, password.
* Client validation:

  * Required fields, email format.
* On submit:

  * Call `/auth/login`; store tokens; redirect to `/tasks`.
* Show errors in toast/inline.

**Task List Page (`/tasks`)**

* Components:

  * Search bar: text input (title/description).
  * Filters: status multi-select, priority multi-select, tags multi-select, due date range.
  * Sort dropdown(s).
  * Table or cards of tasks:

    * Columns: title, owner email, status, priority, due date, tags.
  * Pagination controls.
* Clicking a row → `/tasks/:taskId`.

**Task Detail Page**

* Show:

  * Task fields (title, description, status, priority, due date, tags, owner).
  * Attachments list:

    * Filename, size, created date.
    * Download button.
    * Delete button if current user is owner.
* If current user is owner:

  * “Edit task” button (link to edit page).
  * Attachment upload area:

    * Drag & drop or file input.
    * Show upload progress and errors.

**Task Create/Edit Page**

* Form fields (with client validation):

  * Title (required, max length)
  * Description
  * Status
  * Priority
  * Due date (date/time picker)
  * Tags (multi-select or free-text chips)
* On submit:

  * Call POST `/tasks` or PATCH `/tasks/:id`.
  * Show success toast; redirect to detail.

**Change Password Page**

* Fields: current password, new password, confirm new password.
* Client validation: min length, confirm match.
* On success: show toast, optionally logout user.

### 9.4 Notifications / UX

* Toasts on:

  * Task created/updated/deleted.
  * Attachment uploaded/deleted.
  * Errors (400, 500, 429 with rate limit message).
* Loading indicators:

  * Spinners on network calls.
* Error states:

  * A 429 from API:

    * Show user-friendly message: “You’re making too many requests. Please wait a bit and try again.”

---

## 10. Tests Specification

### 10.1 Backend Unit Tests

* Domain entities:

  * Task status/priority rules, due date validations (if any).
* Use cases:

  * `CreateTaskUseCase` ensures tags are handled, audit event created.
  * `UpdateTaskUseCase` respects owner rules.
  * `SendRemindersUseCase` idempotence.

### 10.2 Integration Tests (API + DB)

* Spin up test DB (PostgreSQL) via docker.
* Tests:

  * Auth flow (register, login, refresh, change password).
  * Task CRUD:

    * User A creates a task; User B cannot edit/delete it but can view it.
  * Search & filter via query params.
  * Attachments:

    * Upload, list, delete.
  * Rate limit:

    * Hit endpoint > limit; expect 429.
  * Health endpoints return expected structure.

### 10.3 Worker / Queue Tests

* Use Celery test worker or synchronous mode.
* Verify:

  * Tasks due in 24h generate exactly one `ReminderLog`.
  * Running the reminder job twice does not create duplicates (unique constraint tested).
  * Failures retry properly.

### 10.4 Contract / API Documentation Tests

* Ensure OpenAPI schema is generated and valid (e.g., load `/openapi.json` and validate).
* Optionally test that responses conform to schema using Pydantic models.

### 10.5 Observability / Health Check Tests

* Test `/health/live` and `/health/ready` endpoints.
* Mock failures (DB down) to ensure readiness status changes.

### 10.6 UI Smoke Tests

* Using Playwright or Cypress:

  * Login flow works.
  * Task list loads.
  * Create task and see it in list.
  * Navigate to task detail.
  * Change password screen reachable and validates form.

---

## 11. Docker & Local Development

### 11.1 docker-compose Outline

```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: tasktracker
      POSTGRES_PASSWORD: tasktracker
      POSTGRES_DB: tasktracker
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  api:
    build: ./backend
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgres://tasktracker:tasktracker@db:5432/tasktracker
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: "dev-secret-change-me"
    ports:
      - "8000:8000"

  worker:
    build: ./backend
    depends_on:
      - api
      - redis
      - db
    command: ["celery", "-A", "app.worker", "worker", "-l", "info"]

  frontend:
    build: ./frontend
    depends_on:
      - api
    ports:
      - "3000:3000"
```

---

## 12. Documentation & Self-Assessment Stubs

### 12.1 Architecture & Rationale Document

Include:

* Diagram of layers and services (API ↔ DB/Redis, Worker ↔ DB/Redis, Frontend ↔ API).
* Short section per decision:

  * Why FastAPI + SQLAlchemy.
  * Why JWT auth.
  * Why Redis-based rate limiting.
  * Why reminder idempotence is DB-driven.

### 12.2 README

* How to set up:

  * `docker-compose up`
  * API available at `http://localhost:8000`
  * Swagger at `/docs`
  * Frontend at `http://localhost:3000`
* How to run tests.

### 12.3 Self-Assessment (to fill after implementation)

Sections:

* What is complete vs. missing.
* What trade-offs were made (e.g., no real email notifications, simple local file storage).
* Where AI helped you:

  * Examples of prompts for:
    * Generating initial FastAPI structure
    * Writing a React form with validation
    * Designing SQLAlchemy models

