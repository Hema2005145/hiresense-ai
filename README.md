# HireSense AI — Intelligent Resume Screening & Interview Assistant

> Status: Phase 2 (Project Scaffolding) complete. See `docs/` for full
> architecture. This README is expanded into the full documentation
> package in the final delivery phase.

## Running Locally (without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

cp .env.example .env              # then fill in GEMINI_API_KEY at minimum

uvicorn app.main:app --reload --port 8000
```

Then open:
- API health check: http://localhost:8000/api/v1/health
- Interactive API docs: http://localhost:8000/docs
- Frontend: http://localhost:8000/

## Running with Docker Compose

```bash
export GEMINI_API_KEY=your-key-here
docker compose up --build
```

This starts a Postgres database and the backend container together,
with the static frontend served from the backend and mounted for live
editing.

## Project Structure

See `docs/architecture.md` (added in the final documentation phase)
for the full breakdown. At a glance:

```
backend/app/api/         → FastAPI routers (HTTP layer only)
backend/app/schemas/     → Pydantic request/response models
backend/app/models/      → SQLAlchemy ORM models
backend/app/repositories/→ Database access, abstracted from services
backend/app/services/    → Business logic
backend/app/ai/          → LLM provider abstraction, embeddings, vector store
backend/app/ml/          → Training, evaluation, model registry
backend/app/core/        → Exceptions, logging
backend/app/db/          → Engine/session management
frontend/                → Static HTML/CSS/Bootstrap/JS
```

## Configuration

All configuration lives in environment variables, documented in
`backend/.env.example`. Copy it to `backend/.env` and fill in real
values — never commit `.env`.

The LLM provider is swappable via a single variable:

```
LLM_PROVIDER=gemini   # or: openai | claude
```

## Development Roadmap

This project is built incrementally, module by module. See the full
roadmap table in `docs/architecture.md` (Phase 1 deliverable).
