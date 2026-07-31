# Code Review Assistant

AI-enabled full-stack platform for automated code review, bug detection, and human-approved review workflows.

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| **0** | Project scaffolding & infrastructure | ✅ Complete |
| 1 | Auth & user management | Pending |
| 2 | Repository intake (GitHub OAuth) | Pending |
| 3 | Static analysis | Pending |
| 4 | AI review core (OpenAI) | Pending |
| 5 | Context retrieval / RAG | Pending |
| 6 | Review workflow | Pending |
| 7 | Rules engine | Pending |
| 8 | Dashboard & analytics | Pending |
| 9 | DevOps & AWS deployment | Pending |
| 10 | Documentation & deliverables | Pending |

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Alembic, Celery
- **Frontend:** HTML, CSS, Vanilla JavaScript (Fetch API)
- **Database:** PostgreSQL 15
- **Cache/Queue:** Redis 7
- **AI:** OpenAI (modular provider layer — Phase 4+)
- **Auth:** JWT + RBAC (Phase 1+)

## Quick Start (Docker)

```bash
# 1. Clone and enter project
cd AI_CODE_Assistant

# 2. Create environment file
cp .env.example .env

# 3. Start all services
docker compose up --build -d

# 4. Run database migrations
docker compose exec api alembic upgrade head

# 5. Verify
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/ready
```

Open in browser:
- **Frontend:** http://localhost:3000
- **API Docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Local Development (Without Docker)

See [docs/phases/phase-0/README.md](docs/phases/phase-0/README.md) for detailed setup.

## Documentation

- [Phase 0 — Scaffolding](docs/phases/phase-0/README.md)
- Architecture plan: see project chat / SRS (Phase 10)

## License

Private — academic / portfolio project.
