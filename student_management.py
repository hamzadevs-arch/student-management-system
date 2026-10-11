
import sqlite3
from datetime import date


# Database Class
class Database:

    def __init__(self):
        self.database_name = "students.db"
        self.create_tables()

    def connect(self):
        return sqlite3.connect(self.database_name)

    def create_tables(self):
        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                email TEXT,
                course TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                subject TEXT,
                marks REAL,
                FOREIGN KEY (student_id)
                REFERENCES students(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT,
                status TEXT,
                FOREIGN KEY (student_id)
                REFERENCES students(id)
            )
        """)

        connection.commit()
        connection.close()


# Student Management System Class
class StudentManagementSystem:

    def __init__(self):
        self.db = Database()

    # Display student information
    def display_student(self, student):
        print("-------------------------")
        print("ID:", student[0])
        print("Name:", student[1])
        print("Age:", student[2])
        print("Email:", student[3])
        print("Course:", student[4])

    # Add student
    def add_student(self):
        print("\n--- Add Student ---")

        try:
            student_id = int(input("Enter Student ID: "))
            name = input("Enter Student Name: ").strip()
            age = int(input("Enter Age: "))
            email = input("Enter Email: ")
            course = input("Enter Course: ")

        except ValueError:
            print("ID and age must be numbers!")
            return

        if not name:
            print("Student name cannot be empty!")
            return

        connection = self.db.connect()

        try:
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO students
                (id, name, age, email, course)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, name, age, email, course))

            connection.commit()
            print("Student added successfully!")

        except sqlite3.IntegrityError:
            print("Student ID already exists!")

        finally:
            connection.close()

    # View students
    def view_students(self):
        connection = self.db.connect()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()

        connection.close()

        if not students:
            print("No students found.")
            return

        for student in students:
            self.display_student(student)

    # Search student
    def search_student(self):
        try:
            student_id = int(input("Enter Student ID: "))
        except ValueError:
            print("Invalid Student ID!")
            return

        connection = self.db.connect()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        )

        student = cursor.fetchone()
        connection.close()

        if student:
            self.display_student(student)
        else:
            print("Student not found.")

    # Update student
    def update_student(self):
        try:
            student_id = int(input("Enter Student ID: "))
        except ValueError:
            print("Invalid Student ID!")
            return

        connection = self.db.connect()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        )

        student = cursor.fetchone()

        if not student:
            print("Student not found.")
            connection.close()
            return

        self.display_student(student)

        try:
            name = input("Enter new name: ").strip()
            age = int(input("Enter new age: "))
            email = input("Enter new email: ")
            course = input("Enter new course: ")

        except ValueError:
            print("Age must be a number!")
            connection.close()
            return

        if not name:
            print("Name cannot be empty!")
            connection.close()
            return

        cursor.execute("""
            UPDATE students
            SET name = ?, age = ?, email = ?, course = ?
            WHERE id = ?
        """, (name, age, email, course, student_id))

        connection.commit()
        connection.close()

        print("Student updated successfully!")

    # Delete student
    def delete_student(self):
        try:
            student_id = int(input("Enter Student ID: "))
        except ValueError:
            print("Invalid Student ID!")
            return

        connection = self.db.connect()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM marks WHERE student_id = ?",
            (student_id,)
        )

        cursor.execute(
            "DELETE FROM attendance WHERE student_id = ?",
            (student_id,)
        )

        cursor.execute(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )

        deleted = cursor.rowcount
        connection.commit()
        connection.close()

        if deleted:
            print("Student deleted successfully!")
        else:
            print("Student not found.")

    # Add student marks
    def add_marks(self):
        print("\n--- Add Student Marks ---")

        try:
            student_id = int(input("Enter Student ID: "))
            subject = input("Enter Subject: ").strip()
            marks = float(input("Enter Marks (0-100): "))

        except ValueError:
            print("Invalid input!")
            return

        if not subject or not 0 <= marks <= 100:
            print("Enter a subject and marks between 0 and 100!")
            return

        connection = self.db.connect()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM students WHERE id = ?",
            (student_id,)
        )

        if not cursor.fetchone():
            print("Student not found.")
            connection.close()
            return

        cursor.execute("""
            SELECT id FROM marks
            WHERE student_id = ? AND subject = ?
        """, (student_id, subject))

        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE marks
                SET marks = ?
                WHERE id = ?
            """, (marks, existing[0]))
        else:
            cursor.execute("""
                INSERT INTO marks
                (student_id, subject, marks)
                VALUES (?, ?, ?)
            """, (student_id, subject, marks))

        connection.commit()
        connection.close()

        print("Marks saved successfully!")

    # Mark attendance
    def mark_attendance(self):
        print("\n--- Mark Attendance ---")

        try:
            student_id = int(input("Enter Student ID: "))
        except ValueError:
            print("Invalid Student ID!")
            return

        status = input("Present or Absent (P/A): ").upper()

        if status not in ["P", "A"]:
            print("Enter P or A only!")
            return

        connection = self.db.connect()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM students WHERE id = ?",
            (student_id,)
        )

        if not cursor.fetchone():
            print("Student not found.")
            connection.close()
            return

        today = str(date.today())

        cursor.execute("""
            SELECT id FROM attendance
            WHERE student_id = ? AND date = ?
        """, (student_id, today))

        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE attendance
                SET status = ?
                WHERE id = ?
            """, (status, existing[0]))
        else:
            cursor.execute("""
                INSERT INTO attendance
                (student_id, date, status)
                VALUES (?, ?, ?)
            """, (student_id, today, status))

        connection.commit()
        connection.close()

        print("Attendance saved successfully!")

    # Calculate grade
    def calculate_grade(self, average):
        if average >= 90:
            return "A+"
        elif average >= 80:
            return "A"
        elif average >= 70:
            return "B"
        elif average >= 60:
            return "C"
        elif average >= 50:
            return "D"
        else:
            return "F"

    # Performance report
    def performance_report(self):
        print("\n--- Student Performance Report ---")

        try:
            student_id = int(input("Enter Student ID: "))
        except ValueError:
            print("Invalid Student ID!")
            return

        connection = self.db.connect()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        )

        student = cursor.fetchone()

        if not student:
            print("Student not found.")
            connection.close()
            return

        self.display_student(student)

        cursor.execute("""
            SELECT subject, marks
            FROM marks
            WHERE student_id = ?
        """, (student_id,))

        results = cursor.fetchall()

        print("\n--- Marks ---")

        if results:
            total = 0

            for subject, mark in results:
                print(subject, ":", mark)
                total += mark

            average = total / len(results)
            grade = self.calculate_grade(average)

            print("Average Marks:", round(average, 2))
            print("Grade:", grade)
        else:
            print("No marks recorded.")

        cursor.execute("""
            SELECT status
            FROM attendance
            WHERE student_id = ?
        """, (student_id,))

        attendance_records = cursor.fetchall()

        print("\n--- Attendance ---")

        if attendance_records:
            total_days = len(attendance_records)

            present_days = sum(
                1 for record in attendance_records
                if record[0] == "P"
            )

            percentage = (
                present_days / total_days
            ) * 100

            print("Total Days:", total_days)
            print("Present Days:", present_days)
            print(
                "Attendance Percentage:",
                round(percentage, 2),
                "%"
            )
        else:
            print("No attendance recorded.")

        connection.close()

    # Main menu
    def main(self):
        while True:
            print("\n==============================")
            print("   STUDENT MANAGEMENT SYSTEM")
            print("==============================")

            print("1. Add Student")
            print("2. View Students")
            print("3. Search Student")
            print("4. Update Student")
            print("5. Delete Student")
            print("6. Add Student Marks")
            print("7. Mark Attendance")
            print("8. Performance Report")
            print("9. Exit")

            choice = input("\nEnter your choice: ")

            if choice == "1":
                self.add_student()
            elif choice == "2":
                self.view_students()
            elif choice == "3":
                self.search_student()
            elif choice == "4":
                self.update_student()
            elif choice == "5":
                self.delete_student()
            elif choice == "6":
                self.add_marks()
            elif choice == "7":
                self.mark_attendance()
            elif choice == "8":
                self.performance_report()
            elif choice == "9":
                print("Thank you for using the system!")
                break
            else:
                print("Invalid choice!")


if __name__ == "__main__":
    app = StudentManagementSystem()
    app.main()
