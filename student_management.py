students = []


def add_student():
    print("\n--- Add Student ---")

    student_id = int(input("Enter Student ID: "))
    name = input("Enter Student Name: ")
    age = int(input("Enter Age: "))
    email = input("Enter Email: ")
    course = input("Enter Course: ")

    student = {
        "id": student_id,
        "name": name,
        "age": age,
        "email": email,
        "course": course
    }

    students.append(student)

    print("Student added successfully!")


def view_students():
    print("\n--- All Students ---")

    if len(students) == 0:
        print("No students found.")
        return

    for student in students:
        print("-------------------------")
        print("ID:", student["id"])
        print("Name:", student["name"])
        print("Age:", student["age"])
        print("Email:", student["email"])
        print("Course:", student["course"])


def search_student():
    print("\n--- Search Student ---")

    student_id = int(input("Enter Student ID: "))

    for student in students:
        if student["id"] == student_id:
            print("\nStudent Found!")
            print("ID:", student["id"])
            print("Name:", student["name"])
            print("Age:", student["age"])
            print("Email:", student["email"])
            print("Course:", student["course"])
            return

    print("Student not found.")


def update_student():
    print("\n--- Update Student ---")

    student_id = int(input("Enter Student ID: "))

    for student in students:
        if student["id"] == student_id:

            print("\nStudent found.")

            student["name"] = input("Enter new name: ")
            student["age"] = int(input("Enter new age: "))
            student["email"] = input("Enter new email: ")
            student["course"] = input("Enter new course: ")

            print("Student updated successfully!")
            return

    print("Student not found.")


def delete_student():
    print("\n--- Delete Student ---")

    student_id = int(input("Enter Student ID: "))

    for student in students:
        if student["id"] == student_id:
            students.remove(student)
            print("Student deleted successfully!")
            return

    print("Student not found.")


def main():
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