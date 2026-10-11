
import sqlite3


class Database:

    def __init__(self):
        self.database_name = "students.db"
        self.create_table()

    def connect(self):
        connection = sqlite3.connect(self.database_name)
        return connection

    def create_table(self):
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

        connection.commit()
        connection.close()


class StudentManagementSystem:

    def __init__(self):
        self.db = Database()

    def add_student(self):
        print("\n--- Add Student ---")

        try:
            student_id = int(input("Enter Student ID: "))
            name = input("Enter Student Name: ")
            age = int(input("Enter Age: "))
            email = input("Enter Email: ")
            course = input("Enter Course: ")

        except ValueError:
            print("Student ID and age must be numbers!")
            return

        if not name.strip():
            print("Student name cannot be empty!")
            return

        connection = self.db.connect()

        try:
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO students (id, name, age, email, course)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, name, age, email, course))

            connection.commit()
            print("Student added successfully!")

        except sqlite3.IntegrityError:
            print("Student ID already exists!")

        finally:
            connection.close()

    def view_students(self):
        print("\n--- All Students ---")

        connection = self.db.connect()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()

        connection.close()

        if len(students) == 0:
            print("No students found.")
            return

        for student in students:
            self.display_student(student)

    def display_student(self, student):
        print("-------------------------")
        print("ID:", student[0])
        print("Name:", student[1])
        print("Age:", student[2])
        print("Email:", student[3])
        print("Course:", student[4])

    def search_student(self):
        print("\n--- Search Student ---")

        try:
            student_id = int(input("Enter Student ID: "))
        except ValueError:
            print("Please enter a valid Student ID!")
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
            print("\nStudent Found!")
            self.display_student(student)
        else:
            print("Student not found.")

    def update_student(self):
        print("\n--- Update Student ---")

        try:
            student_id = int(input("Enter Student ID: "))
        except ValueError:
            print("Please enter a valid Student ID!")
            return

        connection = self.db.connect()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        )

        student = cursor.fetchone()

        if student is None:
            print("Student not found.")
            connection.close()
            return

        print("\nCurrent Student Information:")
        self.display_student(student)

        try:
            name = input("Enter new name: ")
            age = int(input("Enter new age: "))
            email = input("Enter new email: ")
            course = input("Enter new course: ")

        except ValueError:
            print("Age must be a number!")
            connection.close()
            return

        if not name.strip():
            print("Student name cannot be empty!")
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

    def delete_student(self):
        print("\n--- Delete Student ---")

        try:
            student_id = int(input("Enter Student ID: "))
        except ValueError:
            print("Please enter a valid Student ID!")
            return

        connection = self.db.connect()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )

        deleted_rows = cursor.rowcount

        connection.commit()
        connection.close()

        if deleted_rows > 0:
            print("Student deleted successfully!")
        else:
            print("Student not found.")

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
            print("6. Exit")

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
                print("Thank you for using Student Management System!")
                break

            else:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    app = StudentManagementSystem()
    app.main()
