# Student Management System (Windows Desktop)

A beginner-friendly Python desktop app using CustomTkinter and MySQL.

## Features
- Dashboard: total students, distinct courses, latest record ID
- Add, view, search, update and delete student records
- MySQL database/table auto-creation
- Input validation and parameterized SQL queries

## 1. Install requirements
Install Python 3.10+ and MySQL Server. MySQL Workbench is optional but useful.

Open Command Prompt in this project folder:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## 2. Configure MySQL
Copy `.env.example` to a new file named `.env`:

```bash
copy .env.example .env
```

Edit `.env` and enter the MySQL username/password you chose during MySQL setup.
Example:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
```

Do not share your `.env` file or publish it to GitHub.

## 3. Run the app

```bash
python app.py
```

The application creates the `student_management` database and `students` table automatically.

## 4. Optional: create the database manually
Run `sql/schema.sql` in MySQL Workbench. The app can also create these objects itself.

## Troubleshooting
- **Access denied**: verify DB_USER and DB_PASSWORD in `.env`.
- **Can't connect to MySQL server**: start the MySQL80 service in Windows Services.
- **No module named ...**: activate `.venv`, then run `python -m pip install -r requirements.txt`.
- **Port issue**: confirm the MySQL port in `.env` (usually 3306).

## Student fields
Full name (required), email, phone, course (required), study year, gender.

The email column is unique when supplied. Leave it blank if a student has no email address.
