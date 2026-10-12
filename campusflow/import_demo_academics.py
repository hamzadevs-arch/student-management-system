"""One-time, repeat-safe CampusFlow demo marks/attendance import.

Place this file, CampusFlow_200_Marks.csv, and CampusFlow_200_Attendance.csv
beside students.db in the CampusFlow root. Stop the backend before running.

Only imports rows whose student IDs already exist; does not modify any
existing marks or attendance entries. Never run with real student data unless
intentionally adding this clearly fictional demo dataset.
"""
from __future__ import annotations

import csv
import datetime as dt
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "students.db"
MARKS = ROOT / "CampusFlow_200_Marks.csv"
ATTENDANCE = ROOT / "CampusFlow_200_Attendance.csv"


def load_rows(path: Path, headers: set[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise RuntimeError(f"Missing CSV file: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if set(reader.fieldnames or []) != headers:
            raise RuntimeError(f"Unexpected columns in {path.name}: {reader.fieldnames}")
        rows = list(reader)
    if not rows:
        raise RuntimeError(f"Empty CSV: {path.name}")
    return rows


def main():
    if not DB.exists():
        raise RuntimeError("students.db was not found. Put this script in your campusflow folder.")
    marks = load_rows(MARKS, {"student_id", "subject", "marks", "semester"})
    attendance = load_rows(ATTENDANCE, {"student_id", "date", "status", "semester"})

    parsed_marks = []
    parsed_attendance = []
    for index, item in enumerate(marks, 2):
        try:
            sid = int(item["student_id"])
            score = float(item["marks"])
            subject = item["subject"].strip()
            semester = item["semester"].strip()
        except (ValueError, TypeError, AttributeError) as exc:
            raise RuntimeError(f"Invalid marks row {index}") from exc
        if not 0 <= score <= 100 or not subject or not semester:
            raise RuntimeError(f"Invalid marks row {index}")
        parsed_marks.append((sid, subject, score, semester))

    for index, item in enumerate(attendance, 2):
        try:
            sid = int(item["student_id"])
            day = dt.date.fromisoformat(item["date"]).isoformat()
            status = item["status"].strip()
            semester = item["semester"].strip()
        except (ValueError, TypeError, AttributeError) as exc:
            raise RuntimeError(f"Invalid attendance row {index}") from exc
        if status not in {"P", "A"} or not semester:
            raise RuntimeError(f"Invalid attendance row {index}")
        parsed_attendance.append((sid, day, status, semester))

    expected = {sid for sid, _, _, _ in parsed_marks} | {sid for sid, _, _, _ in parsed_attendance}
    if len(expected) != 200 or len(parsed_marks) != 1000 or len(parsed_attendance) != 4000:
        raise RuntimeError("Unexpected number of records; expected 200 students, 1,000 marks and 4,000 attendance rows.")

    with sqlite3.connect(DB) as conn:
        found = {x[0] for x in conn.execute("SELECT id FROM students WHERE id BETWEEN 900001 AND 900200")}
        missing = expected - found
        if missing:
            raise RuntimeError(
                f"Import the 200 students first! Missing {len(missing)} IDs, including {sorted(missing)[:5]}. No records changed."
            )
        for table, required in (("marks", {"student_id", "subject", "marks", "semester"}),
                                ("attendance", {"student_id", "date", "status", "semester"})):
            current = {item[1] for item in conn.execute(f"PRAGMA table_info({table})")}
            if not required <= current:
                raise RuntimeError(f"Missing database table/columns for {table}; run Phase 13 backend first.")

    backup = ROOT / "students_before_demo_academics.db"
    if not backup.exists():
        shutil.copy2(DB, backup)
        print(f"Database backed up to: {backup.name}")

    inserted_marks = 0
    inserted_attendance = 0
    # One transaction: protects against a half-finished import.
    with sqlite3.connect(DB) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for sid, subject, score, semester in parsed_marks:
            existing = conn.execute(
                "SELECT 1 FROM marks WHERE student_id=? AND lower(subject)=lower(?) AND semester=? LIMIT 1",
                (sid, subject, semester),
            ).fetchone()
            if existing is None:
                conn.execute(
                    "INSERT INTO marks(student_id,subject,marks,semester) VALUES (?,?,?,?)",
                    (sid, subject, score, semester),
                )
                inserted_marks += 1
        for sid, day, status, semester in parsed_attendance:
            existing = conn.execute(
                "SELECT 1 FROM attendance WHERE student_id=? AND date=? LIMIT 1",
                (sid, day),
            ).fetchone()
            if existing is None:
                conn.execute(
                    "INSERT INTO attendance(student_id,date,status,semester) VALUES (?,?,?,?)",
                    (sid, day, status, semester),
                )
                inserted_attendance += 1

    print(f"Done: {inserted_marks} new marks, {inserted_attendance} new attendance entries.")
    print("Existing records were not overwritten. Restart backend and refresh CampusFlow.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, sqlite3.Error) as error:
        raise SystemExit(f"Import stopped: {error}")
