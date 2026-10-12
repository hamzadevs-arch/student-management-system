# CampusFlow — Phase 9: Advanced Academic Reports & Analytics

**Full-stack Student Management System:** React 19 + Vite + Tailwind CSS + Recharts + FastAPI + SQLite + ReportLab

This is a working upgrade to **CampusFlow Phase 8**, not a separate demo app. Admin and teacher login, team access, CRUD, attendance, and marks are preserved.

## What's new in Phase 9

- A polished **Academic reporting** screen accessible from **Reports** in the existing sidebar
- Program and semester filters, plus an optional **attendance date range**
- Statistics: enrolled students, recorded assessments, academic average, attendance rate
- Interactive Recharts for semester comparisons, subject performance, and monthly attendance
- Grade distribution and program performance table
- **Admin-only** downloadable academic summary **PDF**, program summary **CSV**, and individual student **PDF**
- The **full student directory CSV** from Phase 8 remains available to admins
- New optional `semester` fields for marks and attendance records
- **Non-destructive SQLite migration**: older Phase 8 marks and attendance are tagged **Unassigned**
- Six automated backend tests covering the Phase 8 and Phase 9 features, including permissions

### A data-model limitation to understand

The Phase 8 `marks` table stores subjects and scores, but **does not store an assessment date**. Therefore, report **date** filters apply to *attendance only*, not marks. The *semester* filter applies to both records after Phase 9.

Older marks and attendance are not assigned to a semester automatically. They appear under **Unassigned** until new entries are recorded with a semester. This avoids inventing academic data.

### Permissions

| Feature | Admin | Teacher |
|---|:---:|:---:|
| View reports and charts | Yes | Yes |
| Filter semesters, programs and dates | Yes | Yes |
| Download academic summary PDF and program CSV | Yes | No |
| Download an individual student PDF | Yes | No |
| Download full student directory CSV | Yes | No |
| Record marks and attendance with semester | Yes | Yes |
| Manage students and teacher accounts | Yes | No |

The API checks permission on the backend; hiding an export button is not considered sufficient protection.

## Install Phase 9 without losing your data (Windows + VS Code)

**First: Keep a backup of your existing `students.db` database.**

1. In File Explorer, open your **Phase 8** folder and locate `campusflow/students.db`. (The DB is beside `backend` and `frontend`.)
2. Copy `students.db` to a safe backup location. Do **not** delete your Phase 8 folder yet.
3. Extract `CampusFlow_Phase9_Advanced_Reports.zip` into a separate folder.
4. Open the extracted `campusflow` folder in VS Code (`File → Open Folder`).
5. Copy your **original** Phase 8 `students.db` into this new **Phase 9 `campusflow`** folder. Do not copy `students.db` into `backend` or `frontend`.
6. Confirm you now see `campusflow/backend`, `campusflow/frontend`, and `campusflow/students.db`.

Phase 9 creates two missing `semester` columns when you start the backend. It does **not** remove students, saved marks, attendance, admins, teachers, or authentication data.

### Terminal 1 — backend

From the new `campusflow` folder:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Keep this terminal open. Expected: `Uvicorn running on http://127.0.0.1:8000`.

**Do not rerun `create_admin.py` if you copied your existing Phase 8 database.** Log in with your existing admin username/password.

### Terminal 2 — frontend

Open a **new** VS Code terminal and run from the new `campusflow` folder:

```powershell
cd frontend
npm install
npm run dev
```

Open **http://127.0.0.1:5173/** and sign in.

If you are creating an entirely new project without an existing `students.db`, run `python create_admin.py` from `backend` once before signing in; use your own strong unique password.

## Test Phase 9

1. Sign in as **admin**.
2. Add a student if your database has none.
3. Open **Grades & marks** → **Add marks** → select **Semester 1** → save a subject score.
4. Open **Attendance** → **Record attendance** → select **Semester 1** → save present or absent status.
5. Open **Reports** → select the semester → inspect the statistics and charts.
6. Click **Download PDF**, **Program CSV**, or select a student and click **Student PDF**.
7. Optional: sign in as a teacher and verify charts are visible but exports are restricted.

The Reports dropdown also has **Unassigned** for historical records; leaving it at **All semesters** includes all records.

## Automated tests (optional)

From `campusflow/backend`:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
```

The test suite uses temporary database files, not your own `students.db`.

## Folder structure

```text
campusflow/
├── backend/
│   ├── main.py                # Existing CRUD/auth + new API endpoints
│   ├── reports.py             # Reporting aggregates, CSV/PDF generation
│   ├── security.py            # Phase 8 authentication and roles
│   ├── create_admin.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── tests/
│       ├── test_phase8.py
│       └── test_phase9.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Workspace, navigation, marks/attendance forms
│   │   ├── ReportsPage.jsx    # New Phase 9 reports UI
│   │   ├── AccountsPage.jsx
│   │   ├── AuthScreen.jsx
│   │   ├── api.js
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
├── README.md
├── PHASE9_CHANGELOG.md
└── .gitignore
```

## Add Phase 9 to your existing GitHub project

To keep the existing history in `hamzadevs-arch/student-management-system`, copy the new **`campusflow/` source files** into the `campusflow/` folder of your **cloned original GitHub repository**, replacing the older Phase 8 source files. Do not copy local `students.db`, `.env` files, or `node_modules`. From your clone:

```powershell
git add campusflow
git status
# Confirm no databases, credentials or node_modules are staged.
git commit -m "Phase 9: Add academic reports, semester analytics and PDF exports"
git push origin main
```

Never force-push or initialize a new Git history inside an extracted ZIP.

## Local development and data safety

- `students.db` is excluded by `.gitignore`. Keep backups and never upload it to GitHub.
- Avoid putting real student information into a publicly hosted demo or screenshot.
- For local learning/development only; this is not yet an audited production student-information system.
- PDF exports include private academic information. Keep them in a secure folder and share only with authorized people.
- Endpoints are documented at http://127.0.0.1:8000/docs while backend is running.

## Next phase

**Phase 10 — AI Academic Assistant**: permission-aware natural-language questions over read-only academic data.
