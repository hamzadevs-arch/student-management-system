"""Optional, explicit demo-data seeder. Run ONLY on a scratch database."""
from __future__ import annotations
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from main import DB_PATH, setup_db

setup_db()
random.seed(21)
first = ["Ali", "Sara", "Ahmed", "Ayesha", "Bilal", "Hira", "Hamza", "Fatima", "Zain", "Mariam", "Omar", "Noor", "Usman", "Iqra", "Daniyal", "Sana", "Hassan", "Laiba", "Haris", "Mahnoor", "Saad", "Zoya", "Rayan", "Anaya"]
last = ["Khan", "Malik", "Sheikh", "Ahmed", "Raza", "Ali"]
courses = ["Computer Science", "Data Science", "Software Engineering", "Cyber Security", "Artificial Intelligence"]
subjects = ["Python Programming", "Database Systems", "Data Structures", "Networking", "Mathematics"]

connection = sqlite3.connect(DB_PATH)
if connection.execute("SELECT COUNT(*) FROM students").fetchone()[0] > 0:
    raise SystemExit("Database has students already. Demo seed aborted to protect existing records.")
for i, first_name in enumerate(first):
    student_id = 1001 + i
    full = f"{first_name} {last[i % len(last)]}"
    course = courses[i % len(courses)]
    connection.execute("INSERT INTO students VALUES (?,?,?,?,?)",(student_id,full,19+i%5, f"student{student_id}@example.com",course))
    for j, sub in enumerate(subjects):
        score = min(98, max(49, 70 + (i*9+j*7)%27 - (j%3)*4))
        connection.execute("INSERT INTO marks (student_id,subject,marks) VALUES (?,?,?)",(student_id,sub,score))
    for day_index in range(75):
        when = date.today() - timedelta(days=day_index*2)
        status = 'A' if (i*7+day_index*3)%11==0 else 'P'
        connection.execute("INSERT INTO attendance (student_id,date,status) VALUES (?,?,?)",(student_id,when.isoformat(),status))
connection.commit()
connection.close()
print(f"Demo data added to: {DB_PATH}")
