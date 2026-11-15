import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

APP_TITLE = "Student Management System"
DB_NAME = "student_management"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def db_config(include_database=True):
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
    }
    if include_database:
        config["database"] = DB_NAME
    return config


def initialize_database():
    """Create the database and table if they do not already exist."""
    connection = mysql.connector.connect(**db_config(include_database=False))
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    connection.close()

    connection = mysql.connector.connect(**db_config())
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(120) UNIQUE,
            phone VARCHAR(20),
            course VARCHAR(80) NOT NULL,
            study_year VARCHAR(20),
            gender VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()
    cursor.close()
    connection.close()


def get_connection():
    return mysql.connector.connect(**db_config())


class StudentManagementApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x740")
        self.minsize(1000, 650)
        self.configure(fg_color="#F4F7FB")
        self.selected_student_id = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()
        self.load_students()
        self.update_dashboard()

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#17243A")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="CAMPUS\nMANAGER", font=ctk.CTkFont(size=23, weight="bold"),
            text_color="white", justify="left"
        ).pack(anchor="w", padx=24, pady=(34, 8))
        ctk.CTkLabel(
            sidebar, text="STUDENT PORTAL", font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#9FB0C8"
        ).pack(anchor="w", padx=25, pady=(0, 35))

        self.nav_button(sidebar, "▦   Dashboard", self.show_dashboard)
        self.nav_button(sidebar, "♙   Students", self.show_students)
        self.nav_button(sidebar, "＋   Add Student", self.clear_form)

        ctk.CTkLabel(
            sidebar, text="DATABASE CONNECTED\nMySQL • Local server",
            font=ctk.CTkFont(size=11), text_color="#9FB0C8", justify="left"
        ).pack(side="bottom", anchor="w", padx=23, pady=25)

    def nav_button(self, parent, text, command):
        ctk.CTkButton(
            parent, text=text, command=command, anchor="w", height=43,
            corner_radius=9, fg_color="transparent", hover_color="#263954",
            text_color="#EAF0F8", font=ctk.CTkFont(size=14)
        ).pack(fill="x", padx=14, pady=4)

    def create_main_area(self):
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=28, pady=24)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header, text="Student Management", text_color="#17243A",
            font=ctk.CTkFont(size=27, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header, text="Manage student records in one place",
            text_color="#718096", font=ctk.CTkFont(size=13)
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ctk.CTkButton(
            header, text="＋  Add student", width=140, height=38,
            command=self.clear_form
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        self.stats_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.total_value = self.stat_card(self.stats_frame, 0, "TOTAL STUDENTS", "0", "#E8F1FF")
        self.course_value = self.stat_card(self.stats_frame, 1, "COURSES", "0", "#E8F8F1")
        self.latest_value = self.stat_card(self.stats_frame, 2, "LATEST RECORD", "—", "#FFF4E5")

        content = ctk.CTkFrame(self.main, fg_color="white", corner_radius=14)
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(content, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=18, pady=16)
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            toolbar, text="Student records", text_color="#17243A",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        self.search_entry = ctk.CTkEntry(
            toolbar, placeholder_text="Search by name, ID or course...",
            width=280, height=36
        )
        self.search_entry.grid(row=0, column=1, padx=(8, 8))
        self.search_entry.bind("<KeyRelease>", lambda _event: self.load_students())
        ctk.CTkButton(
            toolbar, text="Refresh", width=85, height=36,
            command=self.refresh_all
        ).grid(row=0, column=2)

        table_frame = tk.Frame(content, bg="white")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", background="white", foreground="#263449",
            rowheight=34, fieldbackground="white", borderwidth=0,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading", background="#F0F4F9", foreground="#43536A",
            font=("Segoe UI", 9, "bold"), relief="flat"
        )
        style.map("Treeview", background=[("selected", "#DCEAFF")],
                  foreground=[("selected", "#17243A")])

        columns = ("id", "name", "email", "phone", "course", "year")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {
            "id": ("ID", 55), "name": ("STUDENT NAME", 180),
            "email": ("EMAIL", 205), "phone": ("PHONE", 115),
            "course": ("COURSE", 140), "year": ("YEAR", 90)
        }
        for col, (label, width) in headings.items():
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, minwidth=50, anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="e", padx=18, pady=(0, 16))
        ctk.CTkButton(
            actions, text="Edit selected", width=120, fg_color="#E8F1FF",
            hover_color="#D7E6FC", text_color="#1C5DA8", command=self.edit_selected
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            actions, text="Delete selected", width=130, fg_color="#FDECEC",
            hover_color="#FBDADA", text_color="#B42318", command=self.delete_selected
        ).pack(side="left", padx=5)

        self.create_form()

    def stat_card(self, parent, col, title, value, color):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 8))
        ctk.CTkLabel(
            card, text=title, text_color="#77869A",
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack(anchor="w", padx=16, pady=(14, 4))
        label = ctk.CTkLabel(
            card, text=value, text_color="#17243A",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        label.pack(anchor="w", padx=16, pady=(0, 14))
        return label

    def create_form(self):
        self.form = ctk.CTkFrame(self.main, fg_color="white", corner_radius=14)
        self.form.grid(row=3, column=0, sticky="ew", pady=(18, 0))
        self.form.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            self.form, text="Student details", text_color="#17243A",
            font=ctk.CTkFont(size=17, weight="bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=18, pady=(15, 10))

        self.name_entry = self.add_field("Full name *", 1, 0)
        self.email_entry = self.add_field("Email", 1, 1)
        self.phone_entry = self.add_field("Phone", 1, 2)
        self.course_entry = self.add_field("Course *", 2, 0)
        self.year_menu = self.add_option("Study year", 2, 1, ["1st Year", "2nd Year", "3rd Year", "4th Year"])
        self.gender_menu = self.add_option("Gender", 2, 2, ["Prefer not to say", "Male", "Female", "Other"])

        buttons = ctk.CTkFrame(self.form, fg_color="transparent")
        buttons.grid(row=3, column=0, columnspan=3, sticky="e", padx=18, pady=(8, 16))
        ctk.CTkButton(
            buttons, text="Clear", width=90, fg_color="#EEF2F7",
            hover_color="#E0E7EF", text_color="#344054", command=self.clear_form
        ).pack(side="left", padx=5)
        self.save_button = ctk.CTkButton(
            buttons, text="＋  Save student", width=145, command=self.save_student
        )
        self.save_button.pack(side="left", padx=5)

    def add_field(self, label, row, col):
        frame = ctk.CTkFrame(self.form, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="ew", padx=18, pady=5)
        ctk.CTkLabel(frame, text=label, text_color="#536278").pack(anchor="w", pady=(0, 4))
        entry = ctk.CTkEntry(frame, height=36, border_color="#D8E0EA")
        entry.pack(fill="x")
        return entry

    def add_option(self, label, row, col, values):
        frame = ctk.CTkFrame(self.form, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="ew", padx=18, pady=5)
        ctk.CTkLabel(frame, text=label, text_color="#536278").pack(anchor="w", pady=(0, 4))
        menu = ctk.CTkOptionMenu(frame, values=values, height=36)
        menu.pack(fill="x")
        return menu

    def show_dashboard(self):
        self.load_students()
        self.update_dashboard()

    def show_students(self):
        self.load_students()
        self.search_entry.focus_set()

    def refresh_all(self):
        self.search_entry.delete(0, "end")
        self.clear_form()
        self.load_students()
        self.update_dashboard()

    def load_students(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        search = self.search_entry.get().strip()
        try:
            connection = get_connection()
            cursor = connection.cursor()
            if search:
                query = """
                    SELECT student_id, full_name, email, phone, course, study_year
                    FROM students
                    WHERE CAST(student_id AS CHAR) LIKE %s
                       OR full_name LIKE %s OR course LIKE %s
                    ORDER BY student_id DESC
                """
                pattern = f"%{search}%"
                cursor.execute(query, (pattern, pattern, pattern))
            else:
                cursor.execute("""
                    SELECT student_id, full_name, email, phone, course, study_year
                    FROM students ORDER BY student_id DESC
                """)
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)
            cursor.close()
            connection.close()
        except Error as error:
            messagebox.showerror("Database error", f"Could not load students.\n\n{error}")

    def update_dashboard(self):
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*), COUNT(DISTINCT course), MAX(student_id) FROM students")
            total, courses, latest = cursor.fetchone()
            self.total_value.configure(text=str(total))
            self.course_value.configure(text=str(courses))
            self.latest_value.configure(text=f"#{latest}" if latest else "—")
            cursor.close()
            connection.close()
        except Error as error:
            messagebox.showerror("Database error", str(error))

    def save_student(self):
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip() or None
        phone = self.phone_entry.get().strip() or None
        course = self.course_entry.get().strip()
        year = self.year_menu.get()
        gender = self.gender_menu.get()

        if not name or not course:
            messagebox.showwarning("Missing information", "Full name and course are required.")
            return
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            messagebox.showwarning("Invalid email", "Please enter a valid email address.")
            return

        try:
            connection = get_connection()
            cursor = connection.cursor()
            if self.selected_student_id:
                cursor.execute("""
                    UPDATE students
                    SET full_name=%s, email=%s, phone=%s, course=%s, study_year=%s, gender=%s
                    WHERE student_id=%s
                """, (name, email, phone, course, year, gender, self.selected_student_id))
                message = "Student details updated successfully."
            else:
                cursor.execute("""
                    INSERT INTO students (full_name, email, phone, course, study_year, gender)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, email, phone, course, year, gender))
                message = "Student added successfully."
            connection.commit()
            cursor.close()
            connection.close()
            messagebox.showinfo("Success", message)
            self.clear_form()
            self.load_students()
            self.update_dashboard()
        except Error as error:
            messagebox.showerror("Database error", f"Could not save student.\n\n{error}")

    def on_row_select(self, _event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.selected_student_id = int(values[0])

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select a student", "Choose a student record from the table first.")
            return
        student_id = int(self.tree.item(selected[0], "values")[0])
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT full_name, email, phone, course, study_year, gender
                FROM students WHERE student_id=%s
            """, (student_id,))
            row = cursor.fetchone()
            cursor.close()
            connection.close()
            if not row:
                return
            self.selected_student_id = student_id
            for entry, value in zip(
                [self.name_entry, self.email_entry, self.phone_entry, self.course_entry],
                row[:4]
            ):
                entry.delete(0, "end")
                entry.insert(0, value or "")
            if row[4] in self.year_menu.cget("values"):
                self.year_menu.set(row[4])
            if row[5] in self.gender_menu.cget("values"):
                self.gender_menu.set(row[5])
            self.save_button.configure(text="Save changes")
        except Error as error:
            messagebox.showerror("Database error", str(error))

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select a student", "Choose a student record from the table first.")
            return
        student_id = int(self.tree.item(selected[0], "values")[0])
        if not messagebox.askyesno("Confirm delete", f"Delete student record #{student_id}?"):
            return
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
            connection.commit()
            cursor.close()
            connection.close()
            self.clear_form()
            self.load_students()
            self.update_dashboard()
            messagebox.showinfo("Deleted", "Student record deleted.")
        except Error as error:
            messagebox.showerror("Database error", str(error))

    def clear_form(self):
        self.selected_student_id = None
        for entry in [self.name_entry, self.email_entry, self.phone_entry, self.course_entry]:
            entry.delete(0, "end")
        self.year_menu.set("1st Year")
        self.gender_menu.set("Prefer not to say")
        self.save_button.configure(text="＋  Save student")
        if hasattr(self, "name_entry"):
            self.name_entry.focus_set()


if __name__ == "__main__":
    try:
        initialize_database()
        app = StudentManagementApp()
        app.mainloop()
    except Error as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "MySQL connection failed",
            "Unable to connect to MySQL.\n\n"
            "Check that MySQL Server is running and your .env settings are correct.\n\n"
            f"Details: {error}"
        )
        root.destroy()
