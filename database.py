import sqlite3

# Create/connect to the database
connection = sqlite3.connect("pf_database.db")

# Create a cursor
cursor = connection.cursor()

# Create Employees table
cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    employee_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    employee_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    must_change_password INTEGER DEFAULT 1
)
""")
)
""")

# Create PF Contributions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS pf_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    month TEXT NOT NULL,
    basic_salary REAL NOT NULL,
    employee_pf REAL NOT NULL,
    employer_pf REAL NOT NULL,
    submission_date TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
)
""")

# Create Admin table
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Save the database
connection.commit()

# Close the database
connection.close()

print("Database created successfully!")