# Production preparation (after Phase 13)

## Implemented

- Docker multi-stage build: React production bundle is served with FastAPI on a single origin.
- Existing `STUDENTS_DB` SQLite path remains configurable; cloud blueprint mounts persistent `/data`.
- Health check now queries SQLite to detect basic storage failure.
- Optional, **first-run-only** fictional demo bootstrap with separated private admin and public read-only viewer accounts; no hard-coded secrets.
- Viewer blocked from changing marks and attendance at the API layer; frontend hides relevant edit buttons.
- Automated CI: Python pytest and frontend `npm run build` workflows.
- Smoke checks for health, version, unauthorized access, static login shell and unknown endpoints.
- New professional repository README, deployment guide, manual QA checklist and screenshot instructions.
- Root and app `.gitignore`, Docker build exclusions to protect data and credentials.

## Tested here

- 30 backend tests passed.
- Bootstrap on scratch SQLite created 24 fictional students, 96 marks, 288 attendance records, and two roles. Running it a second time did not add more rows.
- Python module compilation completed.

## Not yet verified

- `npm run build` couldn't run here because installing npm dependencies timed out.
- Docker image build was not run (Docker CLI unavailable in the environment).
- Render deployment requires an authenticated account, explicit approval of paid resources, and real deployment verification.
- Browser-based click-through and screenshots still require a working local/hosted React build.

**Do not mistake this update for a verified live deployment or a completed security audit.**
