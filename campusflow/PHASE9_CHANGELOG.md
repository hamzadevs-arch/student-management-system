# Phase 9 technical changelog

### Database migration
- Added `semester TEXT NOT NULL DEFAULT 'Unassigned'` to `marks` and `attendance` when absent.
- Existing records remain unchanged; they receive the backward-compatible semester label `Unassigned`.
- `POST /api/marks` accepts `semester` (default `Unassigned`) and considers `(student_id, subject, semester)` when updating results.
- `POST /api/attendance` accepts `semester` (default `Unassigned`). A student still has one attendance entry per calendar date. Saving for an existing date updates the status and semester.
- Existing Phase 8 endpoints continue to accept old request bodies without `semester`.

### New API routes (all require login)
- `GET /api/reports/analytics?course=&semester=&start_date=&end_date=` — filtered aggregate statistics, trends, charts
- `GET /api/reports/summary.pdf` — admin only
- `GET /api/reports/summary.csv` — admin only
- `GET /api/reports/student/{student_id}.pdf` — admin only

All export routes accept the appropriate report filters. Only summary endpoints accept a course filter; individual student reports use student ID, semester and attendance dates. Filter date strings must be ISO `YYYY-MM-DD`, and the start date must not exceed the end date.

### Frontend
- Replaced simple Phase 8 Reports view with an interactive `ReportsPage.jsx`.
- Added semester selection to grade and attendance entry forms and semester columns to both tables.
- Preserved full student directory CSV export button.
- Added responsive Phase 9 styles without replacing the existing application design.

### Verification
- Phase 8 and Phase 9 Python tests passed (6/6).
- All changed React/JavaScript files passed TypeScript JSX parser syntax checks.
- A representative PDF report was rendered and checked for layout issues.
- A complete Vite build was not available in the packaging environment because `npm install` could not finish there; run `npm install && npm run build` in your VS Code frontend directory if you want to verify the production bundle.
