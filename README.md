# EstateAI

Intelligent real estate analysis and investment decision support platform.

| Folder | Contents |
| --- | --- |
| `frontend/` | Angular application |
| `backend/` | FastAPI service, database models and migrations ([backend/README.md](backend/README.md)) |

## Setting up a new computer

On Windows 10 or 11, one command installs the tools and every dependency, then checks that the
application works:

```powershell
git clone <repository-url>
cd EstateAI
powershell -ExecutionPolicy Bypass -File setup.ps1
```

The script:

1. installs **Git**, **Node.js LTS** and **uv** with winget when they are missing or too old
   (Windows may ask for permission);
2. installs the frontend packages from `frontend/package-lock.json` (`npm ci`) and the backend
   packages from `backend/uv.lock` (`uv sync`), with the exact versions used in development;
   uv downloads Python 3.14 for the backend if the computer does not have it;
3. creates `backend/.env` from `backend/.env.example` if it does not exist;
4. checks the database connection, runs the backend and frontend tests and builds the frontend,
   then prints a summary.

It can be run again at any time; it only adds what is missing. Use `-SkipChecks` to install
without running the checks.

### Configuration that is not in Git

`backend/.env` contains the database password and is deliberately excluded from Git. Copy your
own `backend/.env` to the new computer (for example from a USB drive or a password manager), or
fill in `DATABASE_URL` and `SUPABASE_URL` in the file the script creates. The script reports
when the file still contains placeholders.

### Python packages without uv

`backend/requirements.txt` lists the same backend packages for `pip`, with hashes:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

It is generated from `uv.lock`. After changing backend dependencies, regenerate it:

```powershell
cd backend
uv export --format requirements-txt --no-dev --no-emit-project --locked --output-file requirements.txt
```

## Running the application

In two terminals:

```powershell
cd backend
uv run uvicorn app.main:app --reload
```

```powershell
cd frontend
npm.cmd start
```

Then open http://localhost:4200. `npm.cmd` works even when PowerShell blocks the `npm` script
wrapper; on other computers `npm start` is equivalent.

## Presentation day checklist

- Run `setup.ps1` on the presentation laptop the day before, and check that the summary shows no
  FAILED items.
- Make sure the laptop is connected to the internet: the database and sign-in run on Supabase.
- Start the backend and the frontend before the presentation and sign in once.
