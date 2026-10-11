import sqlite3
import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox
from pathlib import Path

DB_FILE = Path(__file__).with_name('students.db')


class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Student Management System - Phase 6')
        self.root.geometry('1050x680')
        self.db_setup()
        self.build_gui()
        self.load_students()

    def connect(self):
        connection = sqlite3.connect(DB_FILE)
        connection.execute('PRAGMA foreign_keys = ON')
        return connection

    def db_setup(self):
        with self.connect() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                email TEXT,
                course TEXT
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                subject TEXT,
                marks REAL,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT,
                status TEXT,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )''')

    def build_gui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=12, pady=12)
        student_tab = ttk.Frame(notebook, padding=12)
        academic_tab = ttk.Frame(notebook, padding=12)
        notebook.add(student_tab, text='Students')
        notebook.add(academic_tab, text='Marks & Attendance')

        form = ttk.LabelFrame(student_tab, text='Student Details', padding=10)
        form.pack(fill='x')
        self.entries = {}
        for i, field in enumerate(('ID', 'Name', 'Age', 'Email', 'Course')):
            ttk.Label(form, text=field).grid(row=i // 3 * 2, column=i % 3, sticky='w', padx=6)
            entry = ttk.Entry(form, width=30)
            entry.grid(row=i // 3 * 2 + 1, column=i % 3, padx=6, pady=(0, 8), sticky='ew')
            self.entries[field] = entry
        for col in range(3):
            form.columnconfigure(col, weight=1)

        buttons = ttk.Frame(student_tab)
        buttons.pack(fill='x', pady=10)
        for label, command in (
            ('Add', self.add_student), ('Update', self.update_student),
            ('Delete', self.delete_student), ('Search by ID', self.search_student),
            ('Show All', self.load_students), ('Clear', self.clear_form)
        ):
            ttk.Button(buttons, text=label, command=command).pack(side='left', padx=4)

        columns = ('id', 'name', 'age', 'email', 'course')
        self.tree = ttk.Treeview(student_tab, columns=columns, show='headings', height=14)
        for col in columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=100 if col in ('id', 'age') else 190)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.select_student)

        ttk.Label(academic_tab, text='Student ID').grid(row=0, column=0, sticky='w')
        self.academic_id = ttk.Entry(academic_tab, width=25)
        self.academic_id.grid(row=1, column=0, padx=(0, 12), pady=(0, 14), sticky='w')

        ttk.Label(academic_tab, text='Subject').grid(row=2, column=0, sticky='w')
        self.subject = ttk.Entry(academic_tab, width=25)
        self.subject.grid(row=3, column=0, pady=(0, 10), sticky='w')
        ttk.Label(academic_tab, text='Marks (0-100)').grid(row=2, column=1, sticky='w')
        self.marks = ttk.Entry(academic_tab, width=25)
        self.marks.grid(row=3, column=1, pady=(0, 10), sticky='w')
        ttk.Button(academic_tab, text='Save Marks', command=self.save_marks).grid(row=4, column=0, sticky='w', pady=(0, 20))

        ttk.Label(academic_tab, text='Attendance for Today').grid(row=5, column=0, sticky='w')
        self.attendance = ttk.Combobox(academic_tab, values=('P', 'A'), state='readonly', width=22)
        self.attendance.set('P')
        self.attendance.grid(row=6, column=0, sticky='w', pady=(0, 10))
        ttk.Button(academic_tab, text='Save Attendance', command=self.save_attendance).grid(row=7, column=0, sticky='w', pady=(0, 20))
        ttk.Button(academic_tab, text='Generate Performance Report', command=self.show_report).grid(row=8, column=0, sticky='w')
        self.report = tk.Text(academic_tab, height=16, width=75, state='disabled')
        self.report.grid(row=9, column=0, columnspan=3, sticky='nsew', pady=12)
        academic_tab.columnconfigure(2, weight=1)
        academic_tab.rowconfigure(9, weight=1)

    def form_values(self):
        student_id = int(self.entries['ID'].get())
        name = self.entries['Name'].get().strip()
        age = int(self.entries['Age'].get())
        email = self.entries['Email'].get().strip()
        course = self.entries['Course'].get().strip()
        if not name or age < 0:
            raise ValueError('Enter a name and a valid age.')
        return student_id, name, age, email, course

    def add_student(self):
        try:
            values = self.form_values()
            with self.connect() as conn:
                conn.execute('INSERT INTO students (id, name, age, email, course) VALUES (?, ?, ?, ?, ?)', values)
            self.load_students()
            messagebox.showinfo('Success', 'Student added successfully.')
        except ValueError:
            messagebox.showerror('Input Error', 'Enter numeric ID/age, a nonempty name, and a valid age.')
        except sqlite3.IntegrityError:
            messagebox.showerror('Error', 'Student ID already exists.')

    def update_student(self):
        try:
            values = self.form_values()
            with self.connect() as conn:
                cursor = conn.execute('UPDATE students SET name=?, age=?, email=?, course=? WHERE id=?', (*values[1:], values[0]))
            if cursor.rowcount == 0:
                messagebox.showwarning('Not Found', 'Student not found.')
            else:
                self.load_students()
                messagebox.showinfo('Success', 'Student updated.')
        except ValueError:
            messagebox.showerror('Input Error', 'Enter valid student details.')

    def delete_student(self):
        try:
            student_id = int(self.entries['ID'].get())
        except ValueError:
            messagebox.showerror('Input Error', 'Enter a numeric student ID.')
            return
        if not messagebox.askyesno('Confirm Delete', f'Delete student {student_id} and their records?'):
            return
        with self.connect() as conn:
            conn.execute('DELETE FROM marks WHERE student_id=?', (student_id,))
            conn.execute('DELETE FROM attendance WHERE student_id=?', (student_id,))
            cursor = conn.execute('DELETE FROM students WHERE id=?', (student_id,))
        if cursor.rowcount:
            self.load_students()
            self.clear_form()
        else:
            messagebox.showwarning('Not Found', 'Student not found.')

    def load_students(self):
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM students ORDER BY id').fetchall()
        self.show_rows(rows)

    def search_student(self):
        try:
            student_id = int(self.entries['ID'].get())
        except ValueError:
            messagebox.showerror('Input Error', 'Enter a numeric student ID.')
            return
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM students WHERE id=?', (student_id,)).fetchall()
        self.show_rows(rows)
        if not rows:
            messagebox.showinfo('Not Found', 'No student matches that ID.')

    def show_rows(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert('', 'end', values=row)

    def select_student(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], 'values')
        for field, value in zip(('ID', 'Name', 'Age', 'Email', 'Course'), values):
            self.entries[field].delete(0, tk.END)
            self.entries[field].insert(0, value)
        self.academic_id.delete(0, tk.END)
        self.academic_id.insert(0, values[0])

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def get_academic_id(self):
        student_id = int(self.academic_id.get())
        with self.connect() as conn:
            exists = conn.execute('SELECT 1 FROM students WHERE id=?', (student_id,)).fetchone()
        if not exists:
            raise LookupError('Student not found.')
        return student_id

    def save_marks(self):
        try:
            student_id = self.get_academic_id()
            subject = self.subject.get().strip()
            mark = float(self.marks.get())
            if not subject or not 0 <= mark <= 100:
                raise ValueError()
            with self.connect() as conn:
                row = conn.execute('SELECT id FROM marks WHERE student_id=? AND subject=?', (student_id, subject)).fetchone()
                if row:
                    conn.execute('UPDATE marks SET marks=? WHERE id=?', (mark, row[0]))
                else:
                    conn.execute('INSERT INTO marks (student_id, subject, marks) VALUES (?, ?, ?)', (student_id, subject, mark))
            messagebox.showinfo('Success', 'Marks saved.')
        except (ValueError, LookupError) as error:
            messagebox.showerror('Input Error', str(error) or 'Enter a valid student ID, subject and marks from 0 to 100.')

    def save_attendance(self):
        try:
            student_id = self.get_academic_id()
            status = self.attendance.get()
            if status not in ('P', 'A'):
                raise ValueError('Select P or A.')
            today = date.today().isoformat()
            with self.connect() as conn:
                row = conn.execute('SELECT id FROM attendance WHERE student_id=? AND date=?', (student_id, today)).fetchone()
                if row:
                    conn.execute('UPDATE attendance SET status=? WHERE id=?', (status, row[0]))
                else:
                    conn.execute('INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)', (student_id, today, status))
            messagebox.showinfo('Success', 'Attendance saved.')
        except (ValueError, LookupError) as error:
            messagebox.showerror('Input Error', str(error) or 'Enter a valid student ID.')

    def show_report(self):
        try:
            student_id = self.get_academic_id()
        except (ValueError, LookupError):
            messagebox.showerror('Input Error', 'Enter an existing numeric student ID.')
            return
        with self.connect() as conn:
            student = conn.execute('SELECT name, course FROM students WHERE id=?', (student_id,)).fetchone()
            marks = conn.execute('SELECT subject, marks FROM marks WHERE student_id=? ORDER BY subject', (student_id,)).fetchall()
            attendance = conn.execute('SELECT status FROM attendance WHERE student_id=?', (student_id,)).fetchall()
        lines = [f'Student: {student[0]} (ID: {student_id})', f'Course: {student[1]}', '', 'MARKS']
        if marks:
            lines += [f'{subject}: {mark:g}' for subject, mark in marks]
            average = sum(mark for _, mark in marks) / len(marks)
            grade = ('A+' if average >= 90 else 'A' if average >= 80 else
                     'B' if average >= 70 else 'C' if average >= 60 else
                     'D' if average >= 50 else 'F')
            lines += [f'Average: {average:.2f}', f'Grade: {grade}']
        else:
            lines.append('No marks recorded.')
        lines += ['', 'ATTENDANCE']
        if attendance:
            present = sum(status == 'P' for (status,) in attendance)
            lines += [f'Present: {present} / {len(attendance)} recorded days',
                      f'Attendance: {present / len(attendance) * 100:.2f}%']
        else:
            lines.append('No attendance recorded.')
        self.report.config(state='normal')
        self.report.delete('1.0', tk.END)
        self.report.insert(tk.END, '\n'.join(lines))
        self.report.config(state='disabled')


if __name__ == '__main__':
    root = tk.Tk()
    StudentApp(root)
    root.mainloop()
