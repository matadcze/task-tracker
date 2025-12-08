# Task Tracker

A production-grade task management platform with an AI-powered chat assistant that understands natural language commands.

## What It Does

Talk to the assistant like you would to a colleague:
- *"Remind me to review the quarterly report"*
- *"Create a task to fix the login bug"*

The AI interprets your intent, extracts structured data, and creates tasks automatically.

## Technical Highlights

- **Agentic AI Architecture** — LLM-based task interpretation with graceful fallback to rule-based parsing
- **Content Safety** — Real-time moderation via OpenAI's moderation API
- **Domain-Driven Design** — Clean separation between business logic and infrastructure
- **Production-Ready** — JWT auth, rate limiting, audit logging, Prometheus metrics, async everywhere

## Stack

**Backend:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis, Celery
**Frontend:** Next.js, TypeScript
**AI:** OpenAI API (chat completion + moderation)
**Ops:** Docker Compose, Prometheus, Grafana