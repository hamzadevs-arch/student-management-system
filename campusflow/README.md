# CampusFlow — Phase 10: AI-Enhanced Academic Assistant + Phase 9 Reports

**Full-stack Student Management System:** React 19 + Vite + Tailwind CSS + Recharts + FastAPI + SQLite + ReportLab

**Phase 10 added:** A secure, read-only academic chat assistant in the existing CampusFlow sidebar. The assistant uses locally computed academic facts and works without an API key. Optional OpenAI-based wording is available for aggregate summaries only.

This is a working upgrade to **CampusFlow Phase 9**, not a separate demo app. Admin and teacher login, team access, CRUD, attendance, marks, PDF/CSV reports, and analytics are preserved. The Phase 10 chat does not change your database tables.

## What's new in Phase 10

- **AI Assistant** sidebar page with a polished chat, suggested questions, and answer cards
- Ask about student counts, subject averages, attendance, program performance, and semesters
- **Administrator-only** student-specific answers, top-five student averages, and low-attendance lists
- Permission checks enforced by FastAPI, not just by hidden buttons
- Safe, parameterized, predefined `SELECT` queries: user input never runs as SQL
- No API key necessary: the default mode uses **local intent matching and deterministic data insights**, not a general-purpose LLM
- **Optional** language-model wording for aggregate verified answers via the OpenAI API (explicit opt-in). Individual student details are never sent to the API.
- Chat history exists only while the React page is open, not in your database

### Phase 10 example questions

```text
How many students are enrolled?
How many students in BS Computer Science?
What is the overall average score?
Which subject has the highest average marks?
What is the attendance rate?
Show Semester 4 performance
Compare performance by program
Show Ali Ahmed's marks                        (admin only)
Who are the top 5 students by average marks?    (admin only)
Which students have attendance below 75%?       (admin only)
```

**Important:** The assistant does not answer every possible sentence. It supports the patterns listed above and will explain when a question is outside its scope. For true LLM-assisted *wording* of verified aggregates, see the optional section below; the model cannot generate SQL or modify records.

### Phase 10 optional OpenAI wording (not required)

The local assistant works without any API key. For an optional language-model rephrasing of **aggregate** academic facts:

1. With permission to use an API account and only with data suitable for external processing, open the **backend** terminal.
2. Run `python -m pip install -r requirements-llm.txt`.
3. Set the key **only in the backend terminal's environment**, never inside `frontend/src` or committed files:

```powershell
$env:OPENAI_API_KEY = "your-personal-api-key"
$env:OPENAI_MODEL = "gpt-4.1-mini"
python -m uvicorn main:app --reload
```

The backend sends **verified aggregate summaries**, such as subject/program labels and statistical values, to the model. **Individual student names, email addresses, student IDs, and raw rows are never sent**, and the original question is not sent. API calls may have a cost. If unavailable, the app returns the verified local answer. For school/real-student deployments, keep this optional feature off until organizational privacy approvals are obtained.

### Test Phase 10 in CampusFlow

1. Sign in as your existing admin or teacher.
2. Open **AI Assistant** in the sidebar.
3. Click **How many students are enrolled?**; it should reflect your live `students.db`.
4. Ask **What is the attendance rate?**. If none is entered, the answer should say no records are available.
5. As an **admin**, ask **Show Ali Ahmed's marks** (replace with a name in your database).
6. Sign in as a **teacher** and try the same name-specific question: it should be denied in the assistant.

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
- Twelve automated backend tests across Phases 8–10, including assistant permissions

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

## Install Phase 10 without losing your data (Windows + VS Code)

**First: Keep a backup of your existing `students.db` database.**

1. In File Explorer, open your **Phase 9** folder and locate `campusflow/students.db`. (The DB is beside `backend` and `frontend`.)
2. Copy `students.db` to a safe backup location. Do **not** delete your Phase 9 folder yet.
3. Extract `CampusFlow_Phase10_Academic_AI_Assistant.zip` into a separate folder.
4. Open the extracted `campusflow` folder in VS Code (`File → Open Folder`).
5. Copy your **original** Phase 9 `students.db` into this new **Phase 10 `campusflow`** folder. Do not copy `students.db` into `backend` or `frontend`.
6. Confirm you now see `campusflow/backend`, `campusflow/frontend`, and `campusflow/students.db`.

Phase 10 does **not** introduce database migrations or remove students, saved marks, attendance, admins, teachers, or authentication data.

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

## Test Phase 9 reports (still included)

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
│   ├── academic_assistant.py   # NEW: read-only academic QA
│   ├── main.py                # Existing CRUD/auth + new API endpoints
│   ├── reports.py             # Reporting aggregates, CSV/PDF generation
│   ├── security.py            # Phase 8 authentication and roles
│   ├── create_admin.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── requirements-llm.txt   # Optional external model dependency
│   └── tests/
│       ├── test_phase8.py
│       ├── test_phase9.py
│       └── test_phase10.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Workspace, navigation, marks/attendance forms
│   │   ├── ReportsPage.jsx    # Phase 9 reports UI
│   │   ├── AssistantPage.jsx  # NEW: Phase 10 chat UI
│   │   ├── AccountsPage.jsx
│   │   ├── AuthScreen.jsx
│   │   ├── api.js
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
├── README.md
├── PHASE9_CHANGELOG.md
├── PHASE10_CHANGELOG.md
└── .gitignore
```

## Add Phase 10 to your existing GitHub project

To keep the existing history in `hamzadevs-arch/student-management-system`, copy the new **`campusflow/` source files** into the `campusflow/` folder of your **cloned original GitHub repository**, updating the previous Phase 9 source files. Do not copy local `students.db`, `.env` files, or `node_modules`. From your clone:

```powershell
git add campusflow
git status
# Confirm no databases, credentials or node_modules are staged.
git commit -m "Phase 10: Add secure academic AI assistant"
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

**Phase 11 — Machine Learning**: optional explainable academic performance predictions, with proper train/test validation and safeguards against misleading results.
