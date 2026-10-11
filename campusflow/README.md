# CampusFlow · Phase 8 — Accounts & Permissions

**React + Tailwind CSS + Recharts + Lucide React + Python FastAPI + SQLite**

This release extends the Phase 7 CampusFlow dashboard with real user authentication and role-based access, while keeping the dashboard design and existing SQLite student records.

## New in Phase 8

- Polished **sign-in screen** with no hard-coded demo credentials
- **Admin / Teacher** roles, enforced inside FastAPI
- Admin-only **Team access** screen to create, enable, or disable teachers
- Passwords hashed using Python's PBKDF2-HMAC-SHA256 with random per-user salts
- Random, expiring (8-hour) login tokens; the SQLite DB contains only their SHA-256 digests
- Temporary account lockout after 5 consecutive wrong passwords
- Frontend hides actions unavailable to teachers, **and** backend rejects forbidden requests
- Existing `students`, `marks`, and `attendance` tables remain intact

### Permission matrix

| Action | Admin | Teacher |
|---|:---:|:---:|
| View dashboard, students, marks and attendance | ✓ | ✓ |
| Add / update / delete student records | ✓ | — |
| Record marks | ✓ | ✓ |
| Record attendance | ✓ | ✓ |
| Export student CSV (including email addresses) | ✓ | — |
| Create or disable teacher accounts | ✓ | — |

This is a local development project, not a production-hardened school system. Do not expose it on the public internet or upload real student data to GitHub. Production deployment requires HTTPS, stronger secure session handling, audit logs, recovery flows, and security review.

## Before you start

Install:
- **Python 3.10+** (`python --version`)
- **Node.js 20.19+ or 22.12+** (`node --version`)
- VS Code

Extract the ZIP. You should see:

```text
campusflow/
├── backend/
│   ├── main.py
│   ├── security.py
│   ├── create_admin.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── seed_demo.py
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── AuthScreen.jsx
│   │   ├── AccountsPage.jsx
│   │   ├── api.js
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
├── README.md
└── .gitignore
```

### Keep your old database

**Back up `students.db` before you replace any files.**

If you're upgrading from Phase 7, keep the existing `students.db` in the **root `campusflow/` folder** (next to `backend/` and `frontend/`). Don't delete it. Phase 8 creates only the missing `users` and `sessions` tables.

If you don't have a database, CampusFlow creates a new empty `students.db` automatically.

## Run the project in VS Code — Windows

**Open the `campusflow` folder in VS Code**, then select **Terminal → New Terminal**.

### Terminal 1: backend (Python)

Run these **one at a time**:

```powershell
cd backend
python -m pip install -r requirements.txt
```

**First time only**: create your own administrator account:

```powershell
python create_admin.py
```

Choose an administrator username and a **unique password of at least 12 characters**. The terminal will not show your password while typing it. No password is provided or embedded in the repository.

Start the API:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Leave this terminal running. You should see `Uvicorn running on http://127.0.0.1:8000`.

> If you already ran the server before creating the administrator, you can open a *third* terminal to run `python create_admin.py` from `backend/`. You only need to run it once.

### Terminal 2: frontend (React)

Click the **+** button at the top-right of VS Code's terminal panel to create a second terminal. It should start in the project's root folder. Run:

```powershell
cd frontend
npm install
npm run dev
```

Leave this terminal running. Open **http://127.0.0.1:5173** in Chrome or Edge.

You'll see the new CampusFlow login screen. Sign in using the **username/password you chose in Terminal 1**.

**After signing in as admin**, choose **Team access** in the sidebar to add a teacher. Teachers use the same login screen; teacher permissions are enforced by FastAPI.

If Terminal 2 says the `frontend` folder doesn't exist, you may be inside `backend/`. Run `cd ..` before `cd frontend`.

## macOS / Linux

Run the same commands in two terminals. Depending on your machine, `python3` may be required instead of `python`.

## API docs

When the backend is running: http://127.0.0.1:8000/docs

Most endpoints require an `Authorization: Bearer <token>` header. Login at `POST /api/auth/login` to obtain a token.

## Run automated backend tests (optional)

From the `backend` directory:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q tests/test_phase8.py
```

The tests use temporary SQLite databases and **do not touch your own `students.db`**.

## Security notes

- There are **no default passwords or auto-created administrators**.
- Only run `create_admin.py` on a computer you control.
- Never commit `students.db` or account tokens to GitHub. `.gitignore` excludes the database.
- Login tokens are kept in browser `sessionStorage` for this learning project: closing the tab usually ends access on that tab, but any outstanding token expires after up to 8 hours or when revoked. `sessionStorage` can be accessed by JavaScript, so don't consider this production session security.
- Don't store real student records here unless you have permission and appropriate safeguards.
- For real deployment, move to audited authentication/session infrastructure, secure HTTP-only cookies with CSRF protection, TLS, monitoring, backup/restore, account recovery, and security testing.

## Next milestone

**Phase 9:** Advanced academic reports, filters and export improvements. **Phase 10:** Restricted AI assistant for authorized academic data.
