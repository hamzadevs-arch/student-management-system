# Final quality assurance — CampusFlow

Use **fictional records on a copied/test database only**. Do not perform destructive tests on your working 200-student database. Mark a box after you personally verify the browser behavior.

## Environment

- [ ] `python -m pytest -q` passes in `campusflow/backend`
- [ ] `npm run build` passes in `campusflow/frontend`
- [ ] `/api/health` responds with `{"status":"ok"}`
- [ ] `/api/version` reports Phase 13 Offline Smart Campus
- [ ] Launching without the frontend build in development still works through Vite

## Accounts and permissions

- [ ] Admin can sign in, sign out, and sign in again
- [ ] Invalid password is rejected without account details
- [ ] Teacher can see permitted data but cannot add/delete students
- [ ] Teacher cannot export protected individual/summary reports
- [ ] Demo viewer (`demo`) is read-only: attempts to POST marks/attendance return HTTP 403
- [ ] Anonymous requests to `/api/students`, `/api/marks`, `/api/attendance` return HTTP 401

## Core workflows

- [ ] Admin can add one fictional student, then find them in `Ctrl+K` search
- [ ] Student profile shows that person's correct program, marks, and attendance
- [ ] Admin can edit and remove the fictional test student
- [ ] Updating marks refreshes charts/report values
- [ ] Marking attendance changes that student's percentage correctly
- [ ] Duplicate student ID produces a helpful error

## Phase 13 features

- [ ] CSV student import preview detects invalid rows and duplicate IDs
- [ ] Import commit inserts valid fictional students and preserves existing ones
- [ ] Academic calendar can create, edit, and delete a fictional event
- [ ] Teachers and demo viewers can read the calendar but cannot modify it
- [ ] Branded PDF includes the saved university name/logo/footer
- [ ] Offline assistant counts students and finds a named student from current data
- [ ] A follow-up question about the same uniquely identified student uses current marks
- [ ] Assistant cannot bypass role restrictions for personal student data
- [ ] ML predictions distinguish synthetic demonstration from real-data training

## UI and device checks

- [ ] Dashboard tables and charts are readable on desktop and a narrow mobile viewport
- [ ] Side navigation opens/closes on mobile
- [ ] Modal dialogs and forms show input validation/errors clearly
- [ ] Exported PDF layout and CSV column formatting look correct
- [ ] Refresh, logout, and expired-session handling behave correctly

## Production

- [ ] GitHub Actions backend job passes
- [ ] GitHub Actions frontend production-build job passes
- [ ] Production smoke check script passes
- [ ] Public demo contains **only fictional information**, not your local `students.db`
- [ ] Viewer account cannot write to API, even with direct HTTP requests
- [ ] SQLite remains intact after a cloud instance restart/redeploy
- [ ] Public site shows no API secrets in frontend assets
