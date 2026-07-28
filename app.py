import streamlit as st
import pandas as pd
import bcrypt
from supabase import create_client


# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="PF Contribution System",
    page_icon="💼",
    layout="wide"
)


# ==========================================
# SUPABASE CONNECTION
# ==========================================

@st.cache_resource
def get_supabase():

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


supabase = get_supabase()


# ==========================================
# PASSWORD FUNCTIONS
# ==========================================

def hash_password(password):

    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def check_password(password, hashed_password):

    try:

        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )

    except Exception:

        return False

# ==========================================
# LOGIN
# ==========================================

def login(username, password):

    admin_result = (
        supabase
        .table("admins")
        .select("id, username, password")
        .eq("username", username.strip())
        .execute()
    )

    if admin_result.data:

        admin = admin_result.data[0]

        if bcrypt.checkpw(
            password.encode("utf-8"),
            admin["password"].encode("utf-8")
        ):

            return {
                "user_type": "admin",
                "user_id": admin["username"],
                "must_change_password": False
            }

    return None
# ==========================================
# LOGIN PAGE
# ==========================================

def login_page():

    st.title("💼 PF Contribution System")

    st.subheader("Login")

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button(
        "Login",
        type="primary"
    ):

        if not username or not password:

            st.warning(
                "Please enter username and password."
            )

            return

        try:

            user = login(
                username,
                password
            )

            if user:

                st.session_state.logged_in = True

                st.session_state.user_type = (
                    user["user_type"]
                )

                st.session_state.user_id = (
                    user["user_id"]
                )

                st.session_state.employee_name = (
                    user.get(
                        "employee_name",
                        ""
                    )
                )

                st.session_state.must_change_password = (
                    user["must_change_password"]
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )

        except Exception as e:

            st.error(
                "Unable to connect to the database."
            )

            st.write(e)


# ==========================================
# FORCE PASSWORD CHANGE
# ==========================================

def force_password_change():

    employee_id = st.session_state.user_id

    st.title(
        "🔐 Change Temporary Password"
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
        "Set New Password",
        type="primary"
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

        try:

            (
                supabase
                .table("employees")
                .update(
                    {
                        "password": hashed_password,
                        "must_change_password": 0
                    }
                )
                .eq(
                    "employee_id",
                    employee_id
                )
                .execute()
            )

            st.session_state.must_change_password = False

            st.success(
                "Password changed successfully!"
            )

            st.rerun()

        except Exception as e:

            st.error(
                "Unable to change password."
            )

            st.write(e)


# ==========================================
# EMPLOYEE DASHBOARD
# ==========================================

def employee_dashboard():

    employee_id = st.session_state.user_id

    employee_name = st.session_state.employee_name

    st.title(
        "👤 Employee Dashboard"
    )

    st.write(
        f"Welcome, **{employee_name}**"
    )

    st.write(
        f"Employee ID: **{employee_id}**"
    )

    menu = st.sidebar.selectbox(
        "Menu",
        [
            "Submit PF Contribution",
            "My PF Records",
            "Change Password"
        ]
    )


    # ======================================
    # SUBMIT PF
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
            value=2026
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
            "Submit PF Contribution",
            type="primary"
        ):

            month_year = f"{month} {year}"

            try:

                # Check duplicate

                existing = (
                    supabase
                    .table("pf_contributions")
                    .select("id")
                    .eq(
                        "employee_id",
                        employee_id
                    )
                    .eq(
                        "month",
                        month_year
                    )
                    .execute()
                )

                if existing.data:

                    st.error(
                        "You have already submitted PF data for this month."
                    )

                else:

                    supabase.table(
                        "pf_contributions"
                    ).insert(
                        {
                            "employee_id": employee_id,
                            "month": month_year,
                            "basic_salary": basic_salary,
                            "employee_pf": employee_pf,
                            "employer_pf": employer_pf
                        }
                    ).execute()

                    st.success(
                        "PF contribution submitted successfully!"
                    )

            except Exception as e:

                st.error(
                    "Unable to submit PF contribution."
                )

                st.write(e)


    # ======================================
    # MY PF RECORDS
    # ======================================

    elif menu == "My PF Records":

        st.header(
            "📊 My PF Records"
        )

        try:

            result = (
                supabase
                .table("pf_contributions")
                .select(
                    "month, basic_salary, employee_pf, employer_pf, submission_date"
                )
                .eq(
                    "employee_id",
                    employee_id
                )
                .order(
                    "submission_date",
                    desc=True
                )
                .execute()
            )

            if result.data:

                df = pd.DataFrame(
                    result.data
                )

                st.dataframe(
                    df,
                    use_container_width=True
                )

            else:

                st.info(
                    "You have no PF records yet."
                )

        except Exception as e:

            st.error(
                "Unable to load your PF records."
            )

            st.write(e)


    # ======================================
    # CHANGE PASSWORD
    # ======================================

    elif menu == "Change Password":

        st.header(
            "🔐 Change Password"
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
            "Change Password",
            type="primary"
        ):

            try:

                result = (
                    supabase
                    .table("employees")
                    .select("password")
                    .eq(
                        "employee_id",
                        employee_id
                    )
                    .execute()
                )

                if not result.data:

                    st.error(
                        "Employee account not found."
                    )

                else:

                    stored_password = result.data[0][
                        "password"
                    ]

                    if not check_password(
                        current_password,
                        stored_password
                    ):

                        st.error(
                            "Current password is incorrect."
                        )

                    elif new_password != confirm_password:

                        st.error(
                            "New passwords do not match."
                        )

                    elif len(new_password) < 6:

                        st.error(
                            "Password must be at least 6 characters."
                        )

                    else:

                        new_hash = hash_password(
                            new_password
                        )

                        (
                            supabase
                            .table("employees")
                            .update(
                                {
                                    "password": new_hash
                                }
                            )
                            .eq(
                                "employee_id",
                                employee_id
                            )
                            .execute()
                        )

                        st.success(
                            "Password changed successfully!"
                        )

            except Exception as e:

                st.error(
                    "Unable to change password."
                )

                st.write(e)


# ==========================================
# ADMIN DASHBOARD
# ==========================================

def admin_dashboard():

    st.title(
        "🛡️ Admin Dashboard"
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
            "📊 All Employee PF Contributions"
        )

        try:

            result = (
                supabase
                .table("pf_contributions")
                .select(
                    "employee_id, month, basic_salary, employee_pf, employer_pf, submission_date"
                )
                .order(
                    "submission_date",
                    desc=True
                )
                .execute()
            )

            if result.data:

                df = pd.DataFrame(
                    result.data
                )

                st.dataframe(
                    df,
                    use_container_width=True
                )

                csv_data = df.to_csv(
                    index=False
                ).encode(
                    "utf-8"
                )

                st.download_button(
                    label="Download PF Data",
                    data=csv_data,
                    file_name="PF_Contributions.csv",
                    mime="text/csv"
                )

            else:

                st.info(
                    "No PF submissions yet."
                )

        except Exception as e:

            st.error(
                "Unable to load PF data."
            )

            st.write(e)


    # ======================================
    # EMPLOYEE LIST
    # ======================================

    elif menu == "Employee List":

        st.header(
            "👥 Employee List"
        )

        try:

            result = (
                supabase
                .table("employees")
                .select(
                    "employee_id, employee_name, username"
                )
                .order(
                    "employee_id"
                )
                .execute()
            )

            if result.data:

                df = pd.DataFrame(
                    result.data
                )

                st.dataframe(
                    df,
                    use_container_width=True
                )

            else:

                st.info(
                    "No employees found."
                )

        except Exception as e:

            st.error(
                "Unable to load employees."
            )

            st.write(e)


    # ======================================
    # CREATE EMPLOYEE
    # ======================================

    elif menu == "Create Employee":

        st.header(
            "➕ Create New Employee"
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
            "Create Employee",
            type="primary"
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

                try:

                    hashed_password = hash_password(
                        password
                    )

                    (
                        supabase
                        .table("employees")
                        .insert(
                            {
                                "employee_id": employee_id,
                                "employee_name": employee_name,
                                "username": username,
                                "password": hashed_password,
                                "must_change_password": 1
                            }
                        )
                        .execute()
                    )

                    st.success(
                        f"Employee {employee_name} created successfully!"
                    )

                except Exception as e:

                    st.error(
                        "Employee ID or Username may already exist."
                    )

                    st.write(e)


# ==========================================
# MAIN APPLICATION
# ==========================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if not st.session_state.logged_in:

    login_page()


else:

    if st.session_state.user_type == "employee":

        if st.session_state.must_change_password:

            force_password_change()

        else:

            employee_dashboard()


    elif st.session_state.user_type == "admin":

        admin_dashboard()


    if st.sidebar.button(
        "Logout"
    ):

        st.session_state.clear()

        st.rerun()
