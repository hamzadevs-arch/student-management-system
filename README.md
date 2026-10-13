# CampusFlow — Academic Management Dashboard

A full-stack academic administration portfolio project built with **React, Vite, FastAPI, and SQLite**.

> **Status:** Phase 13 features complete; production-preparation pack includes GitHub Actions and a Render/Docker deployment blueprint. This repository is not automatically deployed. The assistant is **offline and database-powered**, not a trained LLM. Predictions based on fictional training data are identified as a demonstration.

## Features

| Area | Capabilities |
| --- | --- |
| Student management | Search, create, update, delete, student profile drawer |
| Academic records | Record and review grades/marks and attendance |
| Reporting | Analytics, CSV exports, branded PDF summaries |
| Smart campus | Excel/CSV student import, academic calendar, university branding |
| Assistant | Approved, read-only questions against live SQLite records |
| ML lab | Synthetic-data demonstration and optional historical-data training |
| Access control | Administrator and teacher roles; optional read-only public demo |
| User experience | Responsive layout, global search (`Ctrl+K`), display preferences |

The original introductory CLI student-management exercises may also exist elsewhere in this repository. The current full-stack application is in [`campusflow/`](campusflow/).

## Tech stack

- React 19, Vite 7, Tailwind CSS, Recharts, Lucide icons
- FastAPI, Pydantic, Python 3.11+, SQLite, ReportLab, scikit-learn
- Pytest for backend tests, GitHub Actions for continuous integration
- Docker multi-stage build for a single-origin production service

## Quick start (Windows PowerShell)

```powershell
cd campusflow\backend
python -m pip install -r requirements.txt
python create_admin.py  # First installation ONLY; do not run against an existing account
python -m uvicorn main:app --reload
```

Open a **second** terminal, from the Git repository root:

```powershell
cd campusflow\frontend
npm install
npm run dev
```

Go to **http://localhost:5173**. The API is available at **http://127.0.0.1:8000/api/health**.

If you have an existing `campusflow/students.db`, **back it up and retain it**. Never run `create_admin.py` to replace an existing admin account. The database is excluded from Git.

## Automated checks

```powershell
cd campusflow\backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Frontend:

```powershell
cd campusflow\frontend
npm install
npm run build
```

The GitHub Actions workflow in [`.github/workflows/campusflow-ci.yml`](.github/workflows/campusflow-ci.yml) performs both checks on new pushes and pull requests.

## Deployment and demo

See [**Deployment guide**](campusflow/DEPLOYMENT.md). The prepared `render.yaml` uses a paid Render service with a **persistent disk**; it does not silently use volatile storage. It can bootstrap a separate database populated exclusively with **fictional demo student data** and an optional read-only visitor account.

> **Privacy:** Never push `students.db`, real student details, account passwords, `.env` files, or student exports into a public repository. Do not upload your own 200-student local database as part of the public demo. Public viewers must never receive the administrator password.

## Screenshots

Screenshots are not pre-generated in this package. Capture actual images from the app after it runs, using only fictional demo records. Suggested frames and locations: [`campusflow/docs/screenshots/README.md`](campusflow/docs/screenshots/README.md).

## Documentation

- [CampusFlow application and development instructions](campusflow/README.md)
- [Deployment / Docker / Render](campusflow/DEPLOYMENT.md)
- [Manual QA checklist](campusflow/docs/QA_CHECKLIST.md)
- [Phase history](campusflow/docs/PHASE_HISTORY.md)

## Limitations

- SQLite + a single persistent disk is appropriate for a small portfolio demonstration, **not** a multi-instance production university service.
- The academic assistant supports a defined set of live-data queries; it is not a general-purpose conversational AI.
- Predicted grades are exploratory estimates. No grades are generated for real students from fictional training data.
- Frontend production build and cloud deployment must be verified in GitHub Actions/on the cloud host.

---

**Portfolio project:** CampusFlow — React + FastAPI full-stack academic workspace.
