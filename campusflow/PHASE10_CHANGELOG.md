# Phase 10 — Academic Assistant

**Added without replacing Phases 1–9 or changing the SQLite schema.**

## New interface
- **AI Assistant** item in the main CampusFlow sidebar.
- Responsive, multi-message chat with suggested questions and structured answer cards.
- Answers show verified statistics and any important caveats.
- Conversation is temporary React state and is cleared by **New chat**, refresh or logout. It is **not stored in SQLite**.
- Separate admin/teacher suggested questions.

## New authenticated API routes
- `GET /api/assistant/capabilities`: supported prompts, logged-in role, and local vs optional AI wording configuration.
- `POST /api/assistant/ask`: `{"question":"What is the average score?"}`.

## Local supported questions (no API key required)
- Student count (total and named program)
- Average recorded marks (overall, program, semester)
- Attendance rate (overall, program, semester)
- Highest-average subjects, subject-level averages
- Program comparisons by average recorded marks
- Semester counts of **students with records** (not official enrollment counts)
- Admin only: named-student marks/attendance, top five students, low attendance by threshold

The assistant is a **deterministic natural-language query router**, not a free-form general-purpose LLM. Unsupported questions get an honest help message. All database reads use fixed `SELECT` statements with SQL placeholders where user data is involved. No user-generated SQL is run.

## Optional true LLM enhancements
For developers who explicitly enable an OpenAI API key, Phase 10 can use the Responses API to *rephrase verified aggregate results*. The model **does not generate or execute SQL** and does not receive student names, email addresses, student IDs or individual records. It does receive aggregate labels (e.g., program/subject names) and associated summary statistics; enable only for non-sensitive/demo data you are comfortable sending to an external service. The original user question is not sent. Individual/admin results are never sent to an LLM. If API service is down, the local answer is returned.

Configuration: install `requirements-llm.txt`, set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` in the **backend terminal environment**, then restart the backend. Never put a real key into frontend code or GitHub. Optional calls may be billed by the provider. No API key is required for standard Phase 10.

## Safety / correctness
- Login required; teacher assistant responses are aggregate-only.
- No data modifications or arbitrary SQL through chat.
- No impersonated predictions; averages are based on saved assessments.
- Missing data reported as unavailable, not as zero.
- Student semester enrollment is not stored in the current schema, so semester counts reflect students with marks or attendance in that semester.
- Attendance rates reflect recorded attendance entries and not timetables or absences without records.
- Chat requests limited to 3–500 characters.
- The service is a learning project and is not a security-audited production student information system.

## Tests
All 12 backend regression tests (Phases 8–10) passed. JSX syntax verified using the TypeScript parser. Vite production build was not verified in this environment because npm dependency installation did not complete.
