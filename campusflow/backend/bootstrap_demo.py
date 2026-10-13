"""Opt-in FIRST START ONLY portfolio demo bootstrap.

Never use on a real student database. Never commit the credentials.
Docker CMD calls this at startup; unless CAMPUSFLOW_BOOTSTRAP_DEMO=1 it exits.
"""
import os
from datetime import date, timedelta

from main import db, setup_db
from security import hash_password, validate_username


def main():
    if os.getenv('CAMPUSFLOW_BOOTSTRAP_DEMO') != '1':
        return
    admin = os.getenv('CAMPUSFLOW_ADMIN_USERNAME', '').strip()
    password = os.getenv('CAMPUSFLOW_ADMIN_PASSWORD', '')
    viewer = os.getenv('CAMPUSFLOW_PUBLIC_VIEWER_USERNAME', '').strip()
    viewer_password = os.getenv('CAMPUSFLOW_VIEWER_PASSWORD', '')
    if not all((admin, password, viewer, viewer_password)):
        raise SystemExit('Missing demo bootstrapping environment variables; see DEPLOYMENT.md')
    if not validate_username(admin) or not validate_username(viewer) or admin.lower() == viewer.lower():
        raise SystemExit('Choose two distinct, valid account usernames')
    try:
        admin_hash = hash_password(password)
        viewer_hash = hash_password(viewer_password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    setup_db()
    with db() as conn:
        existing_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        existing_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
        if existing_users or existing_students:
            print('Demo bootstrap skipped: database already contains accounts or students.')
            return
        conn.execute('INSERT INTO users(username,password_hash,role) VALUES (?, ?, ?)',
                     (admin, admin_hash, 'admin'))
        conn.execute('INSERT INTO users(username,password_hash,role) VALUES (?, ?, ?)',
                     (viewer, viewer_hash, 'teacher'))
        first_names = ('Amna','Bilal','Sana','Zain','Ayesha','Omar','Hira','Saad','Laiba','Hassan',
                       'Mariam','Daniyal','Noor','Hamza','Iqra','Ali','Fatima','Usman','Anaya','Rayan',
                       'Mahnoor','Ahmed','Zoya','Haris')
        subjects = ('Programming Fundamentals', 'Database Systems', 'Mathematics', 'Computer Networks')
        courses = ('BS Computer Science', 'BS Software Engineering', 'BS Information Technology')
        today = date.today()
        for i, given in enumerate(first_names):
            sid = 800001 + i
            conn.execute('INSERT INTO students (id,name,age,email,course) VALUES (?, ?, ?, ?, ?)',
                (sid, f'{given} Demo', 19 + i % 5, f'demo{sid}@example.com', courses[i % 3]))
            for j, subject in enumerate(subjects):
                score = 57 + ((i * 7 + j * 13) % 39)
                conn.execute('INSERT INTO marks (student_id,subject,marks,semester) VALUES (?,?,?,?)',
                    (sid, subject, score, 'Semester 1'))
            for d in range(12):
                when = (today - timedelta(days=d)).isoformat()
                status = 'A' if (i + d * 3) % 8 == 0 else 'P'
                conn.execute('INSERT INTO attendance (student_id,date,status,semester) VALUES (?,?,?,?)',
                    (sid, when, status, 'Semester 1'))
    print('Created 24 fictional students and two initial accounts. No credentials printed.')


if __name__ == '__main__':
    main()
