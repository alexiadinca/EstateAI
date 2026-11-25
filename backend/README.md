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

## Authentication

Protected endpoints expect a Supabase access token in the `Authorization: Bearer <token>`
header. The backend verifies it with the project's public signing keys, so only
`SUPABASE_URL` is required. To test without the frontend, sign in a confirmed test user and
call `/me` while the API is running:

```powershell
$supabaseUrl = "https://<project-ref>.supabase.co"
$publishableKey = "<sb_publishable_... key from the Supabase Connect dialog>"
$body = @{ email = "<test user email>"; password = "<test user password>" } | ConvertTo-Json
$session = Invoke-RestMethod -Method Post -Uri "$supabaseUrl/auth/v1/token?grant_type=password" `
    -Headers @{ apikey = $publishableKey } -ContentType "application/json" -Body $body
Invoke-RestMethod -Uri "http://127.0.0.1:8000/me" -Headers @{ Authorization = "Bearer $($session.access_token)" }
```

The first call to `/me` creates the user's row in `user_profile`.

## Run tests and lint

```powershell
uv run pytest
uv run ruff check .
```
