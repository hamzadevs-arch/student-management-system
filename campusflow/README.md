# CampusFlow — Full-stack academic workspace

![Status: deployment preparation](https://img.shields.io/badge/status-deployment%20preparation-4c6ef5)

**Application:** React + Vite frontend, FastAPI backend, SQLite data storage, authentication, PDF reports, CSV/Excel import, calendar, academic assistant, and an ML demonstration.

## Start locally

From `campusflow/backend`:

```powershell
python -m pip install -r requirements.txt
python create_admin.py  # Only if no admin account exists
python -m uvicorn main:app --reload
```

From `campusflow/frontend` in another terminal:

```powershell
npm install
npm run dev
```

Then open http://127.0.0.1:5173.

### Existing database from Phase 13

Keep a backup of the existing `campusflow/students.db` and use it in this project's `campusflow` directory beside `backend/` and `frontend/`. Do not commit databases or create a new admin account. If `STUDENTS_DB` is set, back up that configured path instead.

### Run tests

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

### What is actually new in this production-preparation update?

- Multi-stage `Dockerfile` builds React and serves it via FastAPI, so production needs one service and one URL.
- `/api/health` checks that the database is reachable before responding OK.
- A GitHub Actions workflow verifies backend tests and attempts the frontend production build.
- `render.yaml` provides paid persistent disk storage for SQLite.
- Optional, explicit demo-only bootstrap seeds **fictional** students. Demo visitor account is read-only.
- Smoke-check script and manual QA checklist help validate public deployments.
- No local admin passwords or student records are bundled.

**No change** to core student/marks/attendance database tables is required. Existing Phase 13 functionality remains available.

## Main features

Students and profiles • marks and attendance • reports • Excel/CSV import • academic calendar • university PDF branding • role-based accounts • global search (`Ctrl+K`) • offline database-powered academic assistant • limited ML lab.

## What the AI does

The academic assistant uses predefined approved SQL operations to answer supported natural-language questions against current authorized records. It does **not** train a language model or connect to Ollama. New records become visible immediately via the next query.

## Deploy

Open [DEPLOYMENT.md](DEPLOYMENT.md) and follow it end-to-end. Render's persistent disks are paid. Do not deploy your local `students.db` to a public site. To let recruiters explore the demo, use the fictional-data bootstrap and give them only the read-only viewer credentials.

For the full history and Phase 9–13 notes, see [docs/PHASE_HISTORY.md](docs/PHASE_HISTORY.md).
