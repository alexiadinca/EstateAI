# EstateAI Backend

FastAPI service for EstateAI. Dependencies are managed with [uv](https://docs.astral.sh/uv/).

## Setup

```powershell
cd backend
copy .env.example .env
uv sync
```

## Database

Set `DATABASE_URL` in `.env` to the Supabase Session pooler connection string, then:

```powershell
uv run python -m app.db.check_connection   # prints the PostgreSQL version, never the URL
uv run alembic upgrade head                # creates or updates the tables
uv run alembic check                       # confirms the models match the database
```

## Run the API

```powershell
uv run uvicorn app.main:app --reload
```

- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

## Run tests and lint

```powershell
uv run pytest
uv run ruff check .
```
