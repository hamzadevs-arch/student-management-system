# START HERE — Phase 13 Offline Edition (Windows)

**Do not run the old Phase 12 terminals.** Stop them with Ctrl+C first.

1. Back up `students.db` from Phase 12. Copy it into this new `campusflow` folder next to `backend` and `frontend`.
2. In VS Code, open **this new campusflow folder** (File → Open Folder).
3. Terminal 1: `cd backend` then `python -m pip install -r requirements.txt` then `python -m uvicorn main:app --reload`.
4. Terminal 2 (from campusflow): `cd frontend` then `npm install` then `npm run dev`.
5. Verify actual backend: open http://127.0.0.1:8000/api/version — it should say `"phase": 13`.
6. Open http://127.0.0.1:5173 and press **Ctrl+Shift+R**. Sign in as **administrator** to see all new modules.

You should see a **NEW · PHASE 13** panel on your Dashboard with buttons for:
- **Import students** (admin): real Excel/CSV preview and safe import.
- **Academic calendar**: create/edit events as an administrator, or view as teacher.
- **University branding** (admin): customize institution logo, name, footer in PDF exports.
- **Live database assistant**: natural-language-pattern Q&A from current student records; supports student pronoun follow-ups; no Ollama, model, API key or external AI required.

If a page is missing, confirm you're in `campusflow/frontend` from the corrected ZIP and the `GET /api/version` endpoint returns Phase 13. Port 5173 must be free or Vite stops with an error instead of silently starting a different port.

Do not upload `students.db` or `.env` to GitHub.
