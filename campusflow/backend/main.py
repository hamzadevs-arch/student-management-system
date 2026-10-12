"""CampusFlow API — compatible with the Student Management System SQLite schema."""
from __future__ import annotations

import csv
import io
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from reports import report_analytics, student_report, summary_pdf, student_pdf, summary_csv
from pydantic import BaseModel, Field, field_validator

from security import (LOCK_SECONDS, MAX_FAILED_LOGINS, SESSION_TTL_SECONDS,
                      account_view, hash_password, issue_token, now,
                      setup_auth_tables, token_digest, validate_username, verify_password)

DB_PATH = Path(os.getenv("STUDENTS_DB", Path(__file__).resolve().parent.parent / "students.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="CampusFlow API", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@contextmanager
def db():
    connection = sqlite3.connect(str(DB_PATH), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def setup_db():
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                email TEXT,
                course TEXT
            );
            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                subject TEXT,
                marks REAL,
                FOREIGN KEY (student_id) REFERENCES students(id)
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT,
                status TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id)
            );
        """)
        # Non-destructive migration: Phase 8 records remain "Unassigned".
        for table in ("marks", "attendance"):
            columns = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            if "semester" not in columns:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN semester TEXT NOT NULL DEFAULT 'Unassigned'")
        setup_auth_tables(conn)


setup_db()


bearer = HTTPBearer(auto_error=False)


class LoginPayload(BaseModel):
    username: str
    password: str


class TeacherPayload(BaseModel):
    username: str
    password: str


class AccountStatusPayload(BaseModel):
    active: bool


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Please sign in", headers={"WWW-Authenticate": "Bearer"})
    with db() as conn:
        row = conn.execute("""
           SELECT u.id,u.username,u.role,u.active FROM sessions s
           JOIN users u ON u.id=s.user_id
           WHERE s.token_hash=? AND s.expires_at>? AND u.active=1
        """, (token_digest(credentials.credentials), now())).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid", headers={"WWW-Authenticate": "Bearer"})
    return account_view(row)


def require_admin(user=Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


@app.get("/api/auth/setup-status")
def setup_status():
    with db() as conn:
        configured = conn.execute("SELECT EXISTS(SELECT 1 FROM users WHERE role='admin')").fetchone()[0]
    return {"configured": bool(configured)}


@app.post("/api/auth/login")
def login(payload: LoginPayload):
    username = payload.username.strip()
    invalid = HTTPException(status_code=401, detail="Invalid username or password")
    token = None
    result = None
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if row is not None and row["active"] and row["locked_until"] <= now():
            if verify_password(payload.password, row["password_hash"]):
                token = issue_token()
                conn.execute("UPDATE users SET attempts=0,locked_until=0 WHERE id=?", (row["id"],))
                conn.execute("DELETE FROM sessions WHERE user_id=? OR expires_at<=?", (row["id"], now()))
                conn.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)",
                             (token_digest(token), row["id"], now()+SESSION_TTL_SECONDS))
                result = {"access_token": token, "token_type": "bearer", "user": account_view(row)}
            else:
                attempts = row["attempts"] + 1
                locked_until = now()+LOCK_SECONDS if attempts >= MAX_FAILED_LOGINS else 0
                conn.execute("UPDATE users SET attempts=?,locked_until=? WHERE id=?", (attempts, locked_until, row["id"]))
    if result is None:
        raise invalid
    return result


@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return user


@app.post("/api/auth/logout")
def logout(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), user=Depends(current_user)):
    with db() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash=?", (token_digest(credentials.credentials),))
    return {"message": "Signed out"}


@app.get("/api/accounts")
def list_accounts(admin=Depends(require_admin)):
    with db() as conn:
        return [account_view(r) for r in conn.execute("SELECT id,username,role,active FROM users ORDER BY id").fetchall()]


@app.post("/api/accounts", status_code=201)
def add_teacher(payload: TeacherPayload, admin=Depends(require_admin)):
    username = payload.username.strip()
    if not validate_username(username):
        raise HTTPException(status_code=422, detail="Username must be 3–32 characters and begin with a letter")
    try:
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    with db() as conn:
        try:
            cursor = conn.execute("INSERT INTO users(username,password_hash,role) VALUES (?,?,'teacher')",
                                  (username, password_hash))
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="That username is already taken")
        return {"id": cursor.lastrowid, "username": username, "role": "teacher", "active": True}


@app.patch("/api/accounts/{user_id}/status")
def change_account_status(user_id: int, payload: AccountStatusPayload, admin=Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="You cannot disable your own account")
    with db() as conn:
        account = conn.execute("SELECT id,role FROM users WHERE id=?", (user_id,)).fetchone()
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")
        if account["role"] == "admin":
            raise HTTPException(status_code=403, detail="Administrator accounts cannot be modified here")
        conn.execute("UPDATE users SET active=? WHERE id=?", (int(payload.active), user_id))
        if not payload.active:
            conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    return {"message": "Account status updated"}


class StudentPayload(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=1, le=120)
    email: str = Field(default="", max_length=200)
    course: str = Field(min_length=1, max_length=120)

    @field_validator("name", "course")
    @classmethod
    def trim_required(cls, value: str):
        if not value.strip():
            raise ValueError("Cannot be blank")
        return value.strip()

    @field_validator("email")
    @classmethod
    def email_format(cls, value: str):
        v = value.strip()
        if v and ("@" not in v or "." not in v.split("@")[-1]):
            raise ValueError("Enter a valid email address")
        return v


class MarksPayload(BaseModel):
    student_id: int
    subject: str = Field(min_length=1, max_length=120)
    marks: float = Field(ge=0, le=100)
    semester: str = Field(default="Unassigned", min_length=1, max_length=40)

    @field_validator("semester")
    @classmethod
    def validate_semester(cls, value: str):
        if not value.strip():
            raise ValueError("Semester cannot be blank")
        return value.strip()

    @field_validator("subject")
    @classmethod
    def trim_subject(cls, value: str):
        if not value.strip():
            raise ValueError("Subject is required")
        return value.strip()


class AttendancePayload(BaseModel):
    student_id: int
    date: date
    status: Literal["P", "A"]
    semester: str = Field(default="Unassigned", min_length=1, max_length=40)

    @field_validator("semester")
    @classmethod
    def validate_attendance_semester(cls, value: str):
        if not value.strip():
            raise ValueError("Semester cannot be blank")
        return value.strip()


def student_or_404(conn, student_id: int):
    row = conn.execute("SELECT id FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Student not found")


def grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/students")
def students(search: str = "", user=Depends(current_user)):
    needle = f"%{search.strip()}%"
    with db() as conn:
        rows = conn.execute("""
            SELECT s.id, s.name, s.age, s.email, s.course,
                   ROUND((SELECT AVG(m.marks) FROM marks m WHERE m.student_id = s.id), 1) AS average,
                   ROUND(100.0 * (SELECT COUNT(*) FROM attendance a WHERE a.student_id = s.id AND a.status = 'P') /
                     NULLIF((SELECT COUNT(*) FROM attendance a WHERE a.student_id = s.id), 0), 1) AS attendance_rate
            FROM students s
            WHERE CAST(s.id AS TEXT) LIKE ? OR s.name LIKE ? OR s.email LIKE ? OR s.course LIKE ?
            ORDER BY s.id DESC
        """, (needle, needle, needle, needle)).fetchall()
        return [dict(row) for row in rows]


@app.post("/api/students", status_code=201)
def add_student(payload: StudentPayload, admin=Depends(require_admin)):
    with db() as conn:
        try:
            conn.execute("INSERT INTO students (id,name,age,email,course) VALUES (?,?,?,?,?)",
                         (payload.id, payload.name, payload.age, payload.email, payload.course))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Student ID already exists")
    return {"message": "Student created"}


@app.put("/api/students/{student_id}")
def edit_student(student_id: int, payload: StudentPayload, admin=Depends(require_admin)):
    if student_id != payload.id:
        raise HTTPException(400, "Student ID cannot be changed")
    with db() as conn:
        student_or_404(conn, student_id)
        conn.execute("UPDATE students SET name=?,age=?,email=?,course=? WHERE id=?",
                     (payload.name, payload.age, payload.email, payload.course, student_id))
    return {"message": "Student updated"}


@app.delete("/api/students/{student_id}")
def delete_student(student_id: int, admin=Depends(require_admin)):
    with db() as conn:
        student_or_404(conn, student_id)
        conn.execute("DELETE FROM marks WHERE student_id=?", (student_id,))
        conn.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
        conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    return {"message": "Student deleted"}


@app.get("/api/marks")
def list_marks(user=Depends(current_user)):
    with db() as conn:
        return [dict(row) for row in conn.execute("""
            SELECT m.id, m.student_id, s.name AS student_name, m.subject, m.marks, m.semester
            FROM marks m JOIN students s ON s.id=m.student_id ORDER BY m.id DESC
        """).fetchall()]


@app.post("/api/marks")
def save_marks(payload: MarksPayload, user=Depends(current_user)):
    with db() as conn:
        student_or_404(conn, payload.student_id)
        existing = conn.execute("SELECT id FROM marks WHERE student_id=? AND LOWER(subject)=LOWER(?) AND semester=? ORDER BY id LIMIT 1",
                                (payload.student_id, payload.subject, payload.semester)).fetchone()
        if existing:
            conn.execute("UPDATE marks SET marks=?,subject=? WHERE id=?",
                         (payload.marks, payload.subject, existing["id"]))
        else:
            conn.execute("INSERT INTO marks (student_id,subject,marks,semester) VALUES (?,?,?,?)",
                         (payload.student_id, payload.subject, payload.marks, payload.semester))
    return {"message": "Marks saved"}


@app.get("/api/attendance")
def list_attendance(user=Depends(current_user)):
    with db() as conn:
        return [dict(row) for row in conn.execute("""
            SELECT a.id, a.student_id, s.name AS student_name, s.course, a.date, a.status, a.semester
            FROM attendance a JOIN students s ON s.id=a.student_id
            ORDER BY a.date DESC, a.id DESC
        """).fetchall()]


@app.post("/api/attendance")
def save_attendance(payload: AttendancePayload, user=Depends(current_user)):
    with db() as conn:
        student_or_404(conn, payload.student_id)
        existing = conn.execute("SELECT id FROM attendance WHERE student_id=? AND date=? ORDER BY id LIMIT 1",
                                (payload.student_id, payload.date.isoformat())).fetchone()
        if existing:
            conn.execute("UPDATE attendance SET status=?,semester=? WHERE id=?", (payload.status, payload.semester, existing["id"]))
        else:
            conn.execute("INSERT INTO attendance (student_id,date,status,semester) VALUES (?,?,?,?)",
                         (payload.student_id, payload.date.isoformat(), payload.status, payload.semester))
    return {"message": "Attendance saved"}


@app.get("/api/dashboard")
def dashboard(user=Depends(current_user)):
    today = date.today()
    month_keys = []
    for offset in range(5, -1, -1):
        y = today.year
        m = today.month - offset
        while m <= 0:
            y -= 1
            m += 12
        month_keys.append(f"{y:04d}-{m:02d}")

    with db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        course_count = conn.execute("SELECT COUNT(DISTINCT course) FROM students WHERE TRIM(course) != ''").fetchone()[0]
        avg = conn.execute("SELECT AVG(marks) FROM marks WHERE marks BETWEEN 0 AND 100").fetchone()[0]
        presence = conn.execute("SELECT COUNT(*) FROM attendance WHERE status='P'").fetchone()[0]
        attendance_total = conn.execute("SELECT COUNT(*) FROM attendance WHERE status IN ('P','A')").fetchone()[0]
        courses = [dict(row) for row in conn.execute("""
          SELECT COALESCE(NULLIF(TRIM(course),''),'Unassigned') AS name, COUNT(*) AS value
          FROM students GROUP BY COALESCE(NULLIF(TRIM(course),''),'Unassigned')
          ORDER BY value DESC, name ASC LIMIT 8
        """)]
        subjects = [dict(row) for row in conn.execute("""
          SELECT subject AS name, ROUND(AVG(marks),1) AS score, COUNT(*) AS attempts
          FROM marks WHERE marks BETWEEN 0 AND 100
          GROUP BY LOWER(TRIM(subject)) ORDER BY attempts DESC, name ASC LIMIT 7
        """)]
        score_rows = conn.execute("SELECT marks FROM marks WHERE marks BETWEEN 0 AND 100").fetchall()
        distribution = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for row in score_rows:
            distribution[grade(row[0])] += 1
        month_marks = dict(conn.execute("""
          SELECT strftime('%Y-%m', date) AS month, COUNT(*) AS count
          FROM attendance WHERE status='P' GROUP BY strftime('%Y-%m', date)
        """).fetchall())
        month_total = dict(conn.execute("""
          SELECT strftime('%Y-%m', date) AS month, COUNT(*) AS count
          FROM attendance WHERE status IN ('P','A') GROUP BY strftime('%Y-%m', date)
        """).fetchall())
        trend = [{"month": datetime.strptime(m,"%Y-%m").strftime("%b"),
                  "full_month": m,
                  "attendance": round(month_marks.get(m, 0)*100/month_total[m], 1) if month_total.get(m,0) else None}
                 for m in month_keys]
        newest = [dict(row) for row in conn.execute("""
            SELECT s.id,s.name,s.email,s.course,
             ROUND((SELECT AVG(m.marks) FROM marks m WHERE m.student_id=s.id), 1) AS average
            FROM students s ORDER BY s.id DESC LIMIT 5
        """)]
        return {
            "stats": {"students": total, "courses": course_count,
                      "average": round(avg, 1) if avg is not None else None,
                      "attendance": round(presence * 100 / attendance_total, 1) if attendance_total else None,
                      "assessments": len(score_rows), "attendance_records": attendance_total},
            "courses": courses, "subjects": subjects,
            "grades": [{"name": k, "count": v} for k, v in distribution.items()],
            "attendance_trend": trend, "recent_students": newest,
        }


@app.get("/api/reports/students.csv")
def export_students(admin=Depends(require_admin)):
    with db() as conn:
        rows = conn.execute("SELECT id,name,age,email,course FROM students ORDER BY id").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Age", "Email", "Course"])
    for row in rows:
        # Defend CSV consumers from formula injection in user-supplied text fields.
        safe = []
        for value in row:
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                value = "'" + value
            safe.append(value)
        writer.writerow(safe)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=student-report.csv"})


# ------------------- Phase 9: reporting -------------------

def check_report_dates(start_date: date | None, end_date: date | None):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="Attendance start date must be on or before end date")


@app.get("/api/reports/analytics")
def get_reports(course: str = "", semester: str = "", start_date: date | None = None,
                end_date: date | None = None, user=Depends(current_user)):
    check_report_dates(start_date, end_date)
    with db() as conn:
        return report_analytics(conn, course.strip(), semester.strip(), start_date, end_date)


@app.get("/api/reports/summary.pdf")
def download_summary_pdf(course: str = "", semester: str = "", start_date: date | None = None,
                         end_date: date | None = None, admin=Depends(require_admin)):
    check_report_dates(start_date, end_date)
    with db() as conn:
        data = report_analytics(conn, course.strip(), semester.strip(), start_date, end_date)
    return Response(summary_pdf(data), media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=campusflow-academic-report.pdf",
                             "Cache-Control": "no-store"})


@app.get("/api/reports/summary.csv")
def download_summary_csv(course: str = "", semester: str = "", start_date: date | None = None,
                         end_date: date | None = None, admin=Depends(require_admin)):
    check_report_dates(start_date, end_date)
    with db() as conn:
        data = report_analytics(conn, course.strip(), semester.strip(), start_date, end_date)
    return Response(summary_csv(data), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=campusflow-program-summary.csv",
                             "Cache-Control": "no-store"})


@app.get("/api/reports/student/{student_id}.pdf")
def download_student_pdf(student_id: int, semester: str = "", start_date: date | None = None,
                         end_date: date | None = None, admin=Depends(require_admin)):
    check_report_dates(start_date, end_date)
    with db() as conn:
        data = student_report(conn, student_id, semester.strip(), start_date, end_date)
    if data is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return Response(student_pdf(data, semester.strip(), start_date, end_date), media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=campusflow-student-{student_id}.pdf",
                             "Cache-Control": "no-store"})
