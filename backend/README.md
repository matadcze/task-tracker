# Task Tracker

## Architecture & Rationale

**Architecture diagram (high level)**

- Clients (Next.js frontend, API consumers)
- FastAPI backend (domain services, repositories, metrics, auth)
- PostgreSQL (primary data store)
- Redis (rate limiting + cache hooks)
- Local/Cloud object storage (attachments; local filesystem in dev)
- Prometheus + Grafana (metrics and dashboards)

Data flow is layered: API routes → domain services → repositories (SQLAlchemy async) → database. Cross-cutting concerns (auth, logging, metrics, rate limiting) live in middleware or dedicated providers. This separation keeps business logic testable and swaps infra pieces (e.g., storage) without touching the domain.

## Installation & Running

### Prerequisites
- Python 3.12
- Node 18+
- Docker & Docker Compose (for full stack: Postgres, Redis, Prometheus, Grafana)

### Backend (dev)
```
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn src.api.app:app --reload
```

Reminders are handled by Celery worker + beat (`reminder_check_interval_minutes`, default 10).
Environment is read from `.env` (see `src/core/config.py` for keys).

### Frontend (dev)
```
cd frontend
npm install
npm run dev
```
Set `NEXT_PUBLIC_API_URL` if the backend isn’t on the default `http://localhost:8000`.

### Full stack with Docker
```
docker compose up -d --build
```
Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Prometheus: http://localhost:9091 (proxied to container 9090)
- Grafana: http://localhost:3001 (admin/admin)

## Self‑Assessment

**Completed**
- Backend FastAPI with auth, tasks, attachments, audit, rate limiting, structured logging with correlation IDs.
- Metrics: HTTP request/error/latency, task/auth/attachments, reminders processed; Prometheus scrape + Grafana dashboard updated.
- Frontend Next.js UI with kanban, task CRUD, attachments manager, improved validation.
- Playwright smoke tests added (local run).

**Missing / Follow‑ups**
- Playwright dependencies not installed in this run (network-restricted); run `npm install && npx playwright install` locally.
- No CI wiring yet for e2e.
- Attachments use local storage by default; swap to cloud storage for production.

**Design choices & trade‑offs**
- Layered architecture (domain/services/repositories) for testability and swap-ability; slightly more boilerplate but clearer boundaries.
- Prometheus metrics via middleware + providers; minimal overhead but requires consistent label cardinality (paths currently raw).
- Rate limiting in middleware using Redis, keyed by user when authenticated; simple sliding window, not token bucket.
- Structured JSON logs with correlation IDs to tie requests and errors across services.

**Where AI assisted**
- I used Claude Code as my programming partner.
