
import sqlite3


# Connect to SQLite database
def connect_db():
    connection = sqlite3.connect("students.db")
    return connection


# Create students table
def create_table():
    connection = connect_db()
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


# Add student
def add_student():
    print("\n--- Add Student ---")

    try:
        student_id = int(input("Enter Student ID: "))
        name = input("Enter Student Name: ")
        age = int(input("Enter Age: "))
        email = input("Enter Email: ")
        course = input("Enter Course: ")

        connection = connect_db()
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

    except ValueError:
        print("Student ID and age must be numbers!")


# View all students
def view_students():
    print("\n--- All Students ---")

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    connection.close()

    if len(students) == 0:
        print("No students found.")
        return

    for student in students:
        print("-------------------------")
        print("ID:", student[0])
        print("Name:", student[1])
        print("Age:", student[2])
        print("Email:", student[3])
        print("Course:", student[4])


# Search student
def search_student():
    print("\n--- Search Student ---")

    try:
        student_id = int(input("Enter Student ID: "))
    except ValueError:
        print("Please enter a valid Student ID!")
        return

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    )

    student = cursor.fetchone()
    connection.close()

    if student:
        print("\nStudent Found!")
        print("ID:", student[0])
        print("Name:", student[1])
        print("Age:", student[2])
        print("Email:", student[3])
        print("Course:", student[4])
    else:
        print("Student not found.")


# Update student
def update_student():
    print("\n--- Update Student ---")

    try:
        student_id = int(input("Enter Student ID: "))
    except ValueError:
        print("Please enter a valid Student ID!")
        return

    connection = connect_db()
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

    print("\nStudent found!")

    try:
        name = input("Enter new name: ")
        age = int(input("Enter new age: "))
        email = input("Enter new email: ")
        course = input("Enter new course: ")
    except ValueError:
        print("Age must be a number!")
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
def delete_student():
    print("\n--- Delete Student ---")

    try:
        student_id = int(input("Enter Student ID: "))
    except ValueError:
        print("Please enter a valid Student ID!")
        return

    connection = connect_db()
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


# Main menu
def main():
    create_table()

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
            add_student()

        elif choice == "2":
            view_students()

        elif choice == "3":
            search_student()

        elif choice == "4":
            update_student()

        elif choice == "5":
            delete_student()

        elif choice == "6":
            print("Thank you for using Student Management System!")
            break

        else:
            print("Invalid choice. Please try again.")


main()
