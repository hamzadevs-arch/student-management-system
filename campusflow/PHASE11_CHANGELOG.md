# Phase 11 — ML Performance Prediction

- Added administrator-only ML Predictions navigation and React scenario screen.
- Added local scikit-learn Ridge regression, predict endpoint, and a clearly marked fictional-data demo.
- Added historical outcome-entry form and non-destructive `performance_examples` SQLite table.
- Added data-readiness checks (12 examples, 4 different students), grouped holdout MAE, baseline comparison, bounds validation, and zero third-party transmission.
- Explicitly restrict ML endpoint access to administrators. Teacher sessions receive HTTP 403.
- Kept authentication, Phase 9 reports and PDF/CSV exports, and Phase 10 academic assistant and name search.
- Added Phase 11 security, migration, demo, and real-training tests (`tests/test_phase11.py`).

**Honesty about predictive limits:** Phase 8–10 `marks` and `attendance` tables do not encode earlier-exam-to-next-exam labels. The app therefore does not make real ML predictions from those tables until actual paired historical outcomes have been recorded. Synthetic demo estimates are fictional illustrations only, never student grades.
