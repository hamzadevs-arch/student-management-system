# Phase 13 — Offline Smart Campus (corrected release)

Released: October 2026 · Backward-compatible with Phase 12's `students.db`.

## Files added

- `backend/smart_assistant.py`: offline question matching with parameterized read-only SQLite queries, student-name context, role checks, and Phase 10 fallback. No AI installation required.
- `backend/phase13.py`: import parser and validation, calendar event schemas, branding settings, and PNG/JPEG image sanitization.
- `backend/tests/test_phase13.py`: additional import, calendar, branded reports, migration and AI privacy tests.
- `frontend/src/ImportPage.jsx`: upload, validated preview and confirmation.
- `frontend/src/CalendarPage.jsx`: responsive month calendar and administrator editor.
- `frontend/src/BrandingPage.jsx`: university identity, secure logo upload, and PDF preview.
- `examples/student_import_template.csv`: fictional CSV sample.

## Files updated

- `backend/main.py`: Phase 13 migrations and authenticated endpoints; Phase 10 assistant uses the smart router; student and summary PDFs take saved report branding.
- `backend/reports.py`: per-institution header, optional logo and custom page footer.
- `backend/requirements.txt`: adds `openpyxl`, `Pillow`, `python-multipart`.
- `backend/.env.example`: sets safe offline mode by default.
- `frontend/src/App.jsx`: three new pages and sidebar/breadcrumb navigation.
- `frontend/src/Experience.jsx`: Ctrl+K search includes new pages.
- `frontend/src/AssistantPage.jsx`: provider status and student context follow-ups.
- `frontend/src/api.js`: authenticated multipart uploads and API actions.
- `frontend/src/styles.css`: polished responsive Phase 13 page styling.
- `README.md`: Phase 13 install, privacy and usage guidance.

## Security and quality commitments

- No user-provided SQL is executed; Ollama may select only whitelisted READ-ONLY tools. Teacher accounts cannot use individual-data tools.
- Offline mode requires no external connections or AI providers.
- Import preview is non-mutating. Import is admin-only and transactional; existing IDs are left intact. Invalid files do not partially import.
- Logo is sanitized and re-encoded to PNG before saving to SQLite.
- New SQL tables are created with `IF NOT EXISTS`; previously saved records are untouched.

## Known limitations

- This offline assistant is deterministic and does not claim to be an LLM. Some free-form questions may require rephrasing.
- The AI is not finetuned or incrementally trained; it uses current records at answer time. The model chooses *which allowed query* to perform and does not generate academic facts.
- The assistant does not perform autonomous edits, arbitrary cross-table joins, or open-ended SQL. Some nuanced questions may fall back to suggested queries.
- The calendar currently supports a single date per event rather than recurring events or student notifications.
- Bulk import currently adds students only (not marks/attendance), and existing students are skipped, not updated.
- npm production build and live Ollama response could not be verified in this environment; see README for local commands.

## Corrected release notes

- Added prominent Phase 13 dashboard entry points (calendar, student import, branding, live assistant).
- `GET /api/version` responds with the exact phase; use it to diagnose accidentally running Phase 12.
- Frontend development server uses strict port 5173 to prevent stale Phase 12 tabs.
- Offline live-data mode is default; no Ollama or external API needed.
- Kept preexisting Phase 10 answer shapes to avoid regression and added student context for follow-ups.
