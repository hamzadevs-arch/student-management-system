# Phase 12 — Professional Interface & Workflow Improvements

Built on the complete Phase 11 package. No student database migration or new Python dependency is required.

## New functionality

1. **Command menu (`Ctrl+K`)** — Search all permitted pages and locally loaded student records by name, ID, or program; keyboard arrow navigation, Enter to select, Esc to dismiss. Also opens from the top-bar search control. No extra external search service is used.
2. **Student profile drawer** — Click a student's name or the profile arrow in the directory, or a search result, to view their program, email, marks, attendance rate, individual assessments, and recent attendance history. Admins can start a marks or attendance form with that student already selected.
3. **Dashboard workflow insights** — Three actionable record-quality summaries: missing marks, missing attendance, and attendance under 75%. Derived from actual records, not guessed insights.
4. **Preferences page** — Compact rows, reduce motion, and toggle the dashboard welcome banner. Preferences are stored in this browser's localStorage, not in SQLite. Keyboard shortcut reference and current account role are included.
5. **Consistent visual styling** — Refreshed sidebar, header, cards, charts, tables, forms, dialogs, mobile search, typography spacing and accessible focus states.

## Unchanged

- Phase 8 authentication, teacher accounts and administrator permissions.
- Phase 9 advanced analytics, semester filters, CSV and PDF reports.
- Phase 10 academic assistant, including the first-name search fix.
- Phase 11 synthetic demonstration and restricted real-data ML prediction tools.
- All FastAPI database endpoints, SQL schema, and Python packages remain unchanged.

## Validation

- All 19 Phase 8–11 Python backend tests passed.
- React JSX parsed using TypeScript transpile syntax checks.
- CSS parsed with PostCSS.
- Full Vite production build **not verified** in this environment: npm registry DNS was unavailable. Run `npm install` then `npm run build` on your own computer to verify the full frontend build.

## Data handling

The downloadable ZIP does not include `students.db`, `.env`, or other local private records. Back up your real database and **copy** it to the new `campusflow/` root folder before running the upgraded application.
