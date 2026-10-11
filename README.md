# Student Management System

A Python-based Student Management System developed step by step, starting with basic CRUD operations and progressing to a desktop application with a graphical user interface.

The project uses Python, SQLite, Object-Oriented Programming (OOP), and Tkinter to manage student records, academic marks, attendance, and performance reports.

## Features

- Add new students
- View all student records
- Search students by ID
- Update student information
- Delete student records
- Store student information permanently
- Add and update subject marks
- Record daily attendance
- Generate student performance reports
- Calculate average marks and grades
- Calculate attendance percentages
- Manage records through a desktop GUI

## Project Development Phases

### Phase 1 — Basic Student Management System

Developed a command-line application using Python fundamentals.

**Features:**
- Add students
- View students
- Search students
- Update student information
- Delete students

**Concepts Used:** Python lists, dictionaries, functions, loops, conditional statements, and user input.

In this phase, student data was stored temporarily in a Python list.

### Phase 2 — JSON File Storage

Implemented permanent data storage using JSON.

**Features:**
- Save student information to a JSON file
- Load saved records when the application starts
- Automatically save changes after adding, updating, or deleting students
- Handle missing JSON files using exception handling

**Concepts Used:** JSON, file handling, `json.load()`, `json.dump()`, and `try/except`.

### Phase 3 — SQLite Database Integration

Replaced JSON storage with SQLite for database management.

**Features:**
- Create a SQLite database
- Create a students table
- Insert student records
- Retrieve student information
- Update existing records
- Delete records
- Search students using SQL queries

**Concepts Used:** SQLite, SQL, database connections, cursors, `INSERT`, `SELECT`, `UPDATE`, and `DELETE`.

### Phase 4 — Object-Oriented Programming

Refactored the application using Python OOP principles.

**Features:**
- Created a `Database` class for database operations
- Created a `StudentManagementSystem` class
- Organized functionality into reusable methods
- Improved code organization and maintainability

**Concepts Used:** Classes, objects, constructors, methods, `self`, and encapsulation of functionality.

### Phase 5 — Marks, Attendance, and Reports

Extended the application with academic management features.

**Features:**
- Add and update student marks
- Record daily attendance
- Store marks and attendance in SQLite tables
- Calculate average marks
- Assign grades based on marks
- Calculate attendance percentages
- Generate individual student performance reports

**Concepts Used:** Database relationships, SQL queries, conditional statements, loops, calculations, and Python's `datetime` module.

### Phase 6 — Graphical User Interface

Introduced a desktop GUI using Python Tkinter.

**Features:**
- Student registration form
- Student records displayed in a table
- Buttons for adding, searching, updating, and deleting students
- Marks and attendance management
- Performance report functionality
- SQLite database integration

**Concepts Used:** Tkinter, GUI programming, event handling, widgets, and database integration.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| SQLite | Database management |
| Tkinter | Desktop graphical interface |
| JSON | File-based storage in Phase 2 |
| OOP | Application structure |
| Git | Version control |
| GitHub | Source code hosting |

## Project Structure

```text
student-management-system/
│
├── student_management.py
├── gui.py
├── students.db
├── students.json
├── .gitignore
└── README.md
```

**File Descriptions:**

- `student_management.py` — Command-line Student Management System
- `gui.py` — Desktop application using Tkinter
- `students.db` — SQLite database, generated locally
- `students.json` — JSON data file from Phase 2
- `.gitignore` — Excludes local data and generated files from Git
- `README.md` — Project documentation

The database and JSON files may not appear on GitHub because they are excluded using `.gitignore`.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/hamzadevs-arch/student-management-system.git
```

### 2. Open the Project Folder

```bash
cd student-management-system
```

### 3. Run the Command-Line Application

```bash
python student_management.py
```

### 4. Run the Desktop GUI

```bash
python gui.py
```

**Requirements:**

- Python 3.10 or later
- Tkinter support in your Python installation

SQLite, JSON, and Tkinter are part of Python's standard library on most desktop installations. No additional pip packages are required.

The SQLite database and its tables are created automatically when the application initializes.

## Example Student Record

```text
Student ID: 101
Name: Ali
Age: 20
Email: ali@example.com
Course: Computer Science
```

## Example Performance Report

```text
--- Student Performance Report ---

Student ID: 101
Name: Ali
Course: Computer Science

--- Marks ---
Python: 90
Database: 85
Networking: 80

Average Marks: 85.0
Grade: A

--- Attendance ---
Total Days: 20
Present Days: 18
Attendance Percentage: 90.0%
```

*The report above uses example data.*

## What I Learned

Through this project, I practiced:

- Writing Python programs using functions and loops
- Working with lists and dictionaries
- Reading and writing JSON files
- Performing CRUD operations using SQL
- Connecting Python applications to SQLite
- Applying Object-Oriented Programming principles
- Handling user input and exceptions
- Building graphical interfaces with Tkinter
- Generating academic performance reports
- Using Git and GitHub for version control

## Future Improvements

- Add login and authentication
- Improve input validation
- Add automated testing
- Export student reports to PDF
- Add charts for academic performance
- Improve the GUI design
- Add search filters and sorting
- Package the application as a desktop executable

## Author

**Muhammad Hamza**

GitHub: [hamzadevs-arch](https://github.com/hamzadevs-arch)

## Project Status

Phase 6 — Desktop GUI implementation.

This project was developed incrementally as a Python learning and portfolio project. Further improvements and testing are planned.