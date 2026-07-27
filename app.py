import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime
import pandas as pd


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    return sqlite3.connect("pf_database.db")


# ==========================================
# PASSWORD FUNCTIONS
# ==========================================

def hash_password(password):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def check_password(password, hashed_password):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ==========================================
# LOGIN FUNCTION
# ==========================================

def login(username, password):

    connection = get_connection()
    cursor = connection.cursor()

    # Check Admin
    cursor.execute(
        """
        SELECT username, password
        FROM admins
        WHERE username = ?
        """,
        (username,)
    )

    admin = cursor.fetchone()

    if admin:

        if check_password(password, admin[1]):

            connection.close()

            return {
                "user_type": "admin",
                "user_id": username,
                "must_change_password": False
            }

    # Check Employee
    cursor.execute(
        """
        SELECT
            employee_id,
            employee_name,
            username,
            password,
            must_change_password
        FROM employees
        WHERE username = ?
        """,
        (username,)
    )

    employee = cursor.fetchone()

    connection.close()

    if employee:

        if check_password(password, employee[3]):

            return {
                "user_type": "employee",
                "user_id": employee[0],
                "employee_name": employee[1],
                "must_change_password": bool(employee[4])
            }

    return None


# ==========================================
# LOGIN PAGE
# ==========================================

def login_page():

    st.title("PF Contribution System")

    st.subheader("Login")

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        if not username or not password:

            st.warning(
                "Please enter username and password."
            )

            return

        user = login(
            username,
            password
        )

        if user:

            st.session_state.logged_in = True

            st.session_state.user_type = user["user_type"]

            st.session_state.user_id = user["user_id"]

            st.session_state.employee_name = user.get(
                "employee_name",
                ""
            )

            st.session_state.must_change_password = user[
                "must_change_password"
            ]

            st.rerun()

        else:

            st.error(
                "Invalid username or password."
            )


# ==========================================
# FORCE PASSWORD CHANGE
# ==========================================

def force_password_change():

    employee_id = st.session_state.user_id

    st.title(
        "Change Temporary Password"
    )

    st.warning(
        "You must change your temporary password before continuing."
    )

    new_password = st.text_input(
        "New Password",
        type="password"
    )

    confirm_password = st.text_input(
        "Confirm New Password",
        type="password"
    )

    if st.button(
        "Set New Password"
    ):

        if not new_password:

            st.error(
                "Please enter a new password."
            )

            return

        if new_password != confirm_password:

            st.error(
                "Passwords do not match."
            )

            return

        if len(new_password) < 6:

            st.error(
                "Password must be at least 6 characters."
            )

            return

        hashed_password = hash_password(
            new_password
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE employees
            SET password = ?,
                must_change_password = 0
            WHERE employee_id = ?
            """,
            (
                hashed_password,
                employee_id
            )
        )

        connection.commit()
        connection.close()

        st.session_state.must_change_password = False

        st.success(
            "Password changed successfully!"
        )

        st.rerun()


# ==========================================
# EMPLOYEE DASHBOARD
# ==========================================

def employee_dashboard():

    employee_id = st.session_state.user_id

    employee_name = st.session_state.employee_name

    st.title(
        "Employee Dashboard"
    )

    st.write(
        f"Welcome, **{employee_name}**"
    )

    st.write(
        f"Employee ID: **{employee_id}**"
    )

    # Sidebar menu

    menu = st.sidebar.selectbox(
        "Menu",
        [
            "Submit PF Contribution",
            "My PF Records",
            "Change Password"
        ]
    )

    # ======================================
    # SUBMIT PF CONTRIBUTION
    # ======================================

    if menu == "Submit PF Contribution":

        st.header(
            "Submit PF Contribution"
        )

        month = st.selectbox(
            "Select Month",
            [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December"
            ]
        )

        year = st.number_input(
            "Year",
            min_value=2020,
            max_value=2100,
            value=datetime.now().year
        )

        basic_salary = st.number_input(
            "Basic Salary",
            min_value=0.0,
            step=100.0
        )

        employee_pf = st.number_input(
            "Employee PF Contribution",
            min_value=0.0,
            step=100.0
        )

        employer_pf = st.number_input(
            "Employer PF Contribution",
            min_value=0.0,
            step=100.0
        )

        if st.button(
            "Submit PF Contribution"
        ):

            connection = get_connection()
            cursor = connection.cursor()

            month_year = f"{month} {year}"

            # Check duplicate submission

            cursor.execute(
                """
                SELECT id
                FROM pf_contributions
                WHERE employee_id = ?
                AND month = ?
                """,
                (
                    employee_id,
                    month_year
                )
            )

            existing = cursor.fetchone()

            if existing:

                st.error(
                    "You have already submitted PF data for this month."
                )

            else:

                submission_date = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                cursor.execute(
                    """
                    INSERT INTO pf_contributions
                    (
                        employee_id,
                        month,
                        basic_salary,
                        employee_pf,
                        employer_pf,
                        submission_date
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        employee_id,
                        month_year,
                        basic_salary,
                        employee_pf,
                        employer_pf,
                        submission_date
                    )
                )

                connection.commit()

                st.success(
                    "PF contribution submitted successfully!"
                )

            connection.close()


    # ======================================
    # MY PF RECORDS
    # ======================================

    elif menu == "My PF Records":

        st.header(
            "My PF Records"
        )

        connection = get_connection()

        df = pd.read_sql_query(
            """
            SELECT
                month,
                basic_salary,
                employee_pf,
                employer_pf,
                submission_date
            FROM pf_contributions
            WHERE employee_id = ?
            ORDER BY submission_date DESC
            """,
            connection,
            params=(employee_id,)
        )

        connection.close()

        if df.empty:

            st.info(
                "You have no PF records yet."
            )

        else:

            st.dataframe(
                df,
                use_container_width=True
            )


    # ======================================
    # CHANGE PASSWORD
    # ======================================

    elif menu == "Change Password":

        st.header(
            "Change Password"
        )

        current_password = st.text_input(
            "Current Password",
            type="password"
        )

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        if st.button(
            "Change Password"
        ):

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT password
                FROM employees
                WHERE employee_id = ?
                """,
                (employee_id,)
            )

            result = cursor.fetchone()

            if result:

                if check_password(
                    current_password,
                    result[0]
                ):

                    if new_password != confirm_password:

                        st.error(
                            "New passwords do not match."
                        )

                    elif len(new_password) < 6:

                        st.error(
                            "Password must be at least 6 characters."
                        )

                    else:

                        new_hashed_password = hash_password(
                            new_password
                        )

                        cursor.execute(
                            """
                            UPDATE employees
                            SET password = ?
                            WHERE employee_id = ?
                            """,
                            (
                                new_hashed_password,
                                employee_id
                            )
                        )

                        connection.commit()

                        st.success(
                            "Password changed successfully!"
                        )

                else:

                    st.error(
                        "Current password is incorrect."
                    )

            connection.close()


# ==========================================
# ADMIN DASHBOARD
# ==========================================

def admin_dashboard():

    st.title(
        "Admin Dashboard"
    )

    menu = st.sidebar.selectbox(
        "Admin Menu",
        [
            "All PF Contributions",
            "Employee List",
            "Create Employee"
        ]
    )


    # ======================================
    # ALL PF CONTRIBUTIONS
    # ======================================

    if menu == "All PF Contributions":

        st.header(
            "All Employee PF Contributions"
        )

        connection = get_connection()

        df = pd.read_sql_query(
            """
            SELECT
                p.employee_id,
                e.employee_name,
                p.month,
                p.basic_salary,
                p.employee_pf,
                p.employer_pf,
                p.submission_date
            FROM pf_contributions p
            JOIN employees e
            ON p.employee_id = e.employee_id
            ORDER BY p.submission_date DESC
            """,
            connection
        )

        connection.close()

        if df.empty:

            st.info(
                "No PF submissions yet."
            )

        else:

            st.dataframe(
                df,
                use_container_width=True
            )

            csv_data = df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="Download PF Data",
                data=csv_data,
                file_name="PF_Contributions.csv",
                mime="text/csv"
            )


    # ======================================
    # EMPLOYEE LIST
    # ======================================

    elif menu == "Employee List":

        st.header(
            "Employee List"
        )

        connection = get_connection()

        df = pd.read_sql_query(
            """
            SELECT
                employee_id,
                employee_name,
                username
            FROM employees
            ORDER BY employee_id
            """,
            connection
        )

        connection.close()

        st.dataframe(
            df,
            use_container_width=True
        )


    # ======================================
    # CREATE EMPLOYEE
    # ======================================

    elif menu == "Create Employee":

        st.header(
            "Create New Employee"
        )

        employee_id = st.text_input(
            "Employee ID"
        )

        employee_name = st.text_input(
            "Employee Name"
        )

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Temporary Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm Temporary Password",
            type="password"
        )

        if st.button(
            "Create Employee"
        ):

            if (
                not employee_id
                or not employee_name
                or not username
                or not password
            ):

                st.error(
                    "Please fill in all fields."
                )

            elif password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            elif len(password) < 6:

                st.error(
                    "Password must be at least 6 characters."
                )

            else:

                connection = get_connection()
                cursor = connection.cursor()

                try:

                    hashed_password = hash_password(
                        password
                    )

                    cursor.execute(
                        """
                        INSERT INTO employees
                        (
                            employee_id,
                            employee_name,
                            username,
                            password,
                            must_change_password
                        )
                        VALUES (?, ?, ?, ?, 1)
                        """,
                        (
                            employee_id,
                            employee_name,
                            username,
                            hashed_password
                        )
                    )

                    connection.commit()

                    st.success(
                        f"Employee {employee_name} created successfully!"
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        "Employee ID or Username already exists."
                    )

                finally:

                    connection.close()


# ==========================================
# MAIN APPLICATION
# ==========================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if not st.session_state.logged_in:

    login_page()


else:

    # ======================================
    # EMPLOYEE
    # ======================================

    if st.session_state.user_type == "employee":

        if st.session_state.must_change_password:

            force_password_change()

        else:

            employee_dashboard()


    # ======================================
    # ADMIN
    # ======================================

    elif st.session_state.user_type == "admin":

        admin_dashboard()


    # ======================================
    # LOGOUT
    # ======================================

    if st.sidebar.button(
        "Logout"
    ):

        st.session_state.clear()

        st.rerun()