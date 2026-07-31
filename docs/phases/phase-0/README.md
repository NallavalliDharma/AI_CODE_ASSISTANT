# Phase 0 — Project Scaffolding & Infrastructure Foundation

## 1. Phase Objective

Establish the complete project foundation so all later phases can be built on a stable, production-ready base:

- Monorepo folder structure (backend, frontend, infra, docs)
- FastAPI application with health checks, CORS, structured logging, and global error handling
- PostgreSQL + Redis connectivity via SQLAlchemy and Celery
- Alembic migration framework (placeholder migration; tables begin in Phase 1)
- Vanilla JS frontend shell with Fetch API client and system status dashboard
- Docker Compose for local multi-service development
- GitHub Actions CI pipeline (lint + test + migrate)

**Phase 0 is complete when:** all services start via Docker, health endpoints respond, frontend shows live system status, and tests pass.

---

## 2. Folder Structure Changes

```
AI_CODE_Assistant/
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml
├── .github/workflows/ci.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/0001_initial.py
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── core/
│   │   │   ├── exceptions.py
│   │   │   └── logging.py
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   └── v1/health.py
│   │   ├── db/session.py
│   │   └── workers/
│   │       ├── celery_app.py
│   │       └── __init__.py  (ping task)
│   └── tests/
│       ├── conftest.py
│       └── test_health.py
├── frontend/
│   ├── index.html
│   ├── css/ (variables, layout, components)
│   └── js/ (api.js, router.js, main.js)
├── infra/nginx/nginx.conf
└── docs/phases/phase-0/README.md  (this file)
```

---

## 3. Files Created

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app factory, CORS, lifespan |
| `backend/app/config.py` | Pydantic settings from environment |
| `backend/app/core/exceptions.py` | Custom exceptions + global handlers |
| `backend/app/core/logging.py` | structlog configuration |
| `backend/app/db/session.py` | SQLAlchemy engine, session, DB health check |
| `backend/app/api/v1/health.py` | Liveness + readiness endpoints |
| `backend/app/workers/celery_app.py` | Celery configuration |
| `backend/app/workers/__init__.py` | Ping task for worker verification |
| `backend/alembic/*` | Migration framework |
| `frontend/index.html` | Landing page with system status |
| `frontend/js/api.js` | Fetch API wrapper |
| `docker-compose.yml` | postgres, redis, api, worker, frontend |
| `.github/workflows/ci.yml` | CI pipeline |

---

## 4. Code Summary

All code is production-ready and located in the repository. Key modules:

- **Application entry:** `backend/app/main.py` — factory pattern, OpenAPI at `/docs`
- **Configuration:** `backend/app/config.py` — all env vars centralized
- **Health checks:** `backend/app/api/v1/health.py` — liveness (no deps) + readiness (DB + Redis)
- **Error handling:** Standardized JSON error responses via `ErrorResponse` schema
- **Frontend:** Landing page polls `/api/v1/health` and `/api/v1/health/ready` on load

---

## 5. Database Changes

**Phase 0:** No application tables created.

- Alembic is configured and a placeholder migration `0001_initial` exists (empty upgrade/downgrade)
- PostgreSQL database `code_review_assistant` is created by Docker Compose
- Tables (users, teams, repositories, etc.) will be added in **Phase 1**

**Migration command:**
```bash
docker compose exec api alembic upgrade head
```

---

## 6. API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/` | Welcome message + doc links | No |
| GET | `/api/v1/health` | Liveness check | No |
| GET | `/api/v1/health/ready` | Readiness (DB + Redis) | No |
| GET | `/docs` | Swagger UI | No |
| GET | `/redoc` | ReDoc | No |
| GET | `/openapi.json` | OpenAPI schema | No |

---

## 7. Frontend Pages

| Page | Path | Description |
|------|------|-------------|
| Landing | `http://localhost:3000/` | Project intro, disabled Sign In (Phase 1), live system status panel |

The landing page displays real-time health for API, Database, Redis, and overall readiness.

---

## 8. Swagger Documentation

After starting the API, open:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Documented endpoints:
- `GET /api/v1/health` — Liveness check
- `GET /api/v1/health/ready` — Readiness check

---

## 9. Sample Requests and Responses

### Liveness Check

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "Code Review Assistant",
  "environment": "development",
  "version": "0.1.0"
}
```

### Readiness Check (all healthy)

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/health/ready
```

**Response (200 OK):**
```json
{
  "status": "ready",
  "database": {
    "status": "ok",
    "message": "Database connection successful"
  },
  "redis": {
    "status": "ok",
    "message": "Redis connection successful"
  }
}
```

### Readiness Check (dependency down)

**Response (503 Service Unavailable):**
```json
{
  "status": "not_ready",
  "database": {
    "status": "error",
    "message": "Database connection failed: ..."
  },
  "redis": {
    "status": "ok",
    "message": "Redis connection successful"
  }
}
```

### Root Endpoint

**Request:**
```bash
curl -X GET http://localhost:8000/
```

**Response (200 OK):**
```json
{
  "message": "Welcome to Code Review Assistant",
  "docs": "/docs",
  "health": "/api/v1/health"
}
```

### Validation Error Example (Phase 1+ preview)

Phase 0 has no POST endpoints. Error format for future phases:

**Response (422):**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "errors": [...]
  }
}
```

---

## 10. Environment Variables

Copy `.env.example` to `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | Code Review Assistant | Display name |
| `APP_ENV` | No | development | `development` / `staging` / `production` |
| `APP_DEBUG` | No | true | Enable debug mode |
| `APP_SECRET_KEY` | **Yes** | — | App secret (min 32 chars) |
| `API_V1_PREFIX` | No | /api/v1 | API route prefix |
| `CORS_ORIGINS` | No | http://localhost:3000,... | Comma-separated origins |
| `DATABASE_URL` | **Yes** | — | PostgreSQL connection string |
| `REDIS_URL` | **Yes** | — | Redis connection string |
| `CELERY_BROKER_URL` | **Yes** | — | Celery broker |
| `CELERY_RESULT_BACKEND` | **Yes** | — | Celery result backend |
| `JWT_SECRET_KEY` | No | — | Used in Phase 1+ |
| `OPENAI_API_KEY` | No | — | Used in Phase 4+ |
| `LOG_LEVEL` | No | INFO | Logging level |
| `LOG_FORMAT` | No | json | `json` or `console` |

---

## 11. Installation Steps

### Option A — Docker (Recommended)

```bash
# Prerequisites: Docker Desktop 4.x+, Docker Compose v2

# 1. Navigate to project root
cd AI_CODE_Assistant

# 2. Create environment file
cp .env.example .env

# 3. Build and start services
docker compose up --build -d

# 4. Wait for health checks (30–60 seconds)
docker compose ps

# 5. Run migrations
docker compose exec api alembic upgrade head
```

### Option B — Local Python (No Docker)

```bash
# Prerequisites: Python 3.11+, PostgreSQL 15, Redis 7

# 1. Create virtual environment
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp ../.env.example ../.env
# Edit DATABASE_URL and REDIS_URL to point to localhost

# 4. Start PostgreSQL and Redis locally

# 5. Run migrations
alembic upgrade head

# 6. Start API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. Start Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# 8. Serve frontend (separate terminal)
cd ../frontend
# Use Docker for frontend+nginx, or:
python -m http.server 3000
# Note: API calls require nginx proxy or CORS; Docker is recommended.
```

---

## 12. Commands to Run

```bash
# Start all services
docker compose up --build -d

# View logs
docker compose logs -f api

# Stop services
docker compose down

# Stop and remove volumes (fresh DB)
docker compose down -v

# Run migrations
docker compose exec api alembic upgrade head

# Run tests inside container
docker compose exec api pytest tests/ -v

# Verify Celery worker
docker compose exec worker celery -A app.workers.celery_app inspect ping

# Run Celery ping task
docker compose exec worker celery -A app.workers.celery_app call app.workers.ping

# Lint
docker compose exec api ruff check app tests
```

---

## 13. Commands to Test

```bash
# 1. Liveness
curl http://localhost:8000/api/v1/health

# 2. Readiness
curl http://localhost:8000/api/v1/health/ready

# 3. Root
curl http://localhost:8000/

# 4. Frontend (open in browser)
start http://localhost:3000        # Windows
open http://localhost:3000         # macOS
xdg-open http://localhost:3000     # Linux

# 5. Swagger
start http://localhost:8000/docs

# 6. Pytest
cd backend && pytest tests/ -v

# 7. Pytest with coverage
cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

# 8. Ruff lint
cd backend && ruff check app tests
```

---

## 14. Expected Output

### `docker compose ps` (all healthy)

```
NAME           STATUS                   PORTS
cra-api        Up (healthy)             0.0.0.0:8000->8000/tcp
cra-frontend   Up                       0.0.0.0:3000->80/tcp
cra-postgres   Up (healthy)             0.0.0.0:5432->5432/tcp
cra-redis      Up (healthy)             0.0.0.0:6379->6379/tcp
cra-worker     Up
```

### `curl http://localhost:8000/api/v1/health`

```json
{"status":"ok","service":"Code Review Assistant","environment":"development","version":"0.1.0"}
```

### `pytest tests/ -v`

```
tests/test_health.py::test_root_endpoint PASSED
tests/test_health.py::test_liveness PASSED
tests/test_health.py::test_readiness_returns_structured_response PASSED
======================== 3 passed ========================
```

### Frontend (http://localhost:3000)

- Page title: **Code Review Assistant**
- System Status panel shows green dots for API, Database, Redis
- Overall status: **ready**

---

## 15. Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Connection refused` on port 8000 | API not started | Run `docker compose up -d` and wait for healthy status |
| Readiness returns 503 for database | Postgres not ready | Wait 30s; check `docker compose logs postgres` |
| Readiness returns 503 for redis | Redis not started | `docker compose up redis -d` |
| `env file .env not found` | Missing .env | `cp .env.example .env` |
| Port 5432 already in use | Local Postgres running | Stop local Postgres or change port in docker-compose.yml |
| Port 8000 already in use | Another process on 8000 | Change API port mapping in docker-compose.yml |
| Frontend shows "API Unreachable" | API down or nginx misconfigured | Verify `curl http://localhost:8000/api/v1/health` |
| CORS errors in browser | Wrong origin | Add your origin to `CORS_ORIGINS` in `.env` |
| Alembic `Can't locate revision` | Migration not run | `docker compose exec api alembic upgrade head` |
| Celery worker not connecting | Redis URL mismatch | Ensure `CELERY_BROKER_URL` matches Redis service |
| Module import errors in tests | Wrong working directory | Run pytest from `backend/` directory |

---

## 16. Verification Checklist

- [ ] `.env` file exists (copied from `.env.example`)
- [ ] `docker compose up --build -d` succeeds without errors
- [ ] All 5 containers are running (`docker compose ps`)
- [ ] `curl http://localhost:8000/api/v1/health` returns `"status": "ok"`
- [ ] `curl http://localhost:8000/api/v1/health/ready` returns `"status": "ready"` (HTTP 200)
- [ ] http://localhost:8000/docs loads Swagger UI with Health endpoints
- [ ] http://localhost:3000 loads landing page
- [ ] Frontend System Status shows API, Database, Redis as healthy
- [ ] `docker compose exec api alembic upgrade head` completes successfully
- [ ] `docker compose exec api pytest tests/ -v` — 3 tests pass
- [ ] `docker compose exec api ruff check app tests` — no lint errors
- [ ] Celery worker is running (`docker compose logs worker` shows "ready")
- [ ] Celery ping task returns `{"status": "pong"}`

---

## 17. Git Commit Message

```
feat(phase-0): scaffold project infrastructure and health-check foundation

- Add FastAPI app with CORS, structured logging, and global error handlers
- Configure PostgreSQL, Redis, Celery, and Alembic migration framework
- Add liveness and readiness health endpoints
- Create vanilla JS frontend shell with Fetch API client and status dashboard
- Add Docker Compose stack and GitHub Actions CI pipeline
```

---

## 18. Next Phase Preview

**Phase 1 — Auth & User Management** will add:
- User model and JWT authentication (login, register, refresh, logout)
- Password hashing with bcrypt
- RBAC middleware (Admin, Staff, Manager, User)
- User and team CRUD APIs
- Login page and auth flow in frontend
- Audit log middleware

---

**Phase 0 complete. Awaiting your approval before starting Phase 1.**
