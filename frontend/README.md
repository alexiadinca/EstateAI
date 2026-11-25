# EstateAI Frontend

Angular 22 application for EstateAI. Requires Node.js 22.22+, 24.15+ or 26+.

## Setup

```powershell
cd frontend
npm install
```

Configuration is in `src/environments/environment.ts`: the FastAPI address, the Supabase
project URL and the Supabase publishable key. These values are public by design. Never put the
Supabase secret key or the database password in the frontend.

## Run

Start the backend first (see `backend/README.md`), then:

```powershell
npm start
```

Open http://localhost:4200. The backend must allow this address in `CORS_ALLOWED_ORIGINS`.

## Build and test

```powershell
npm run build
npm test -- --watch=false
```

## Structure

| Folder | Contents |
| --- | --- |
| `src/styles/` | Design tokens and shared form, card and button styles |
| `src/app/core/auth/` | Supabase session, sign-in, registration, route guards, token interceptor |
| `src/app/core/api/` | Typed services for the FastAPI endpoints |
| `src/app/features/` | Pages: sign-in, registration, account |
| `src/app/shared/` | Reusable form validators |
