# EstateAI Backend

FastAPI service for EstateAI. Dependencies are managed with [uv](https://docs.astral.sh/uv/).

## Setup

```powershell
cd backend
copy .env.example .env
uv sync
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
