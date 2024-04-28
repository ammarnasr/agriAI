# authentication.py
import streamlit as st
import pandas as pd
import sqlite3
import time
import re
import hashlib
import hmac
import os
import shutil

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    ds = total_size/10**6
    total, used, free = shutil.disk_usage("/")
    total = total/ (2**30)
    free = free/ (2**30)
    st.write(f'Your Data size is {ds :.2f}MB; Space left {free :.2f}GB out of {total :.2f}GB')
    return ds


def greeting(msg="Welcome"):
    current_user = st.session_state['current_user']
    st.write(f"{msg} {current_user}!")
    get_size(start_path=f'./{current_user}')
    return current_user


def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        st.info("Demo credentials: dfr4 / 12345")
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        st.session_state['current_user'] = st.session_state["username"]
        if st.session_state["username"] in st.secrets[
            "passwords" # here is where you should connect to the database
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False


# Security
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# DB Management
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

# DB Functions
def create_usertable():
    c.execute('''CREATE TABLE IF NOT EXISTS userstable (
                 username TEXT UNIQUE, 
                 email TEXT UNIQUE, 
                 password TEXT)''')
    conn.commit()

def add_userdata(username, email, password):
    c.execute('INSERT INTO userstable(username, email, password) VALUES (?, ?, ?)', (username, email, password))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username, password))
    data = c.fetchall()
    return data

def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data

def username_exists(username):
    c.execute('SELECT * FROM userstable WHERE username = ?', (username,))
    return c.fetchone() is not None

def email_exists(email):
    # c.execute('SELECT * FROM userstable WHERE email = ?', (email,))
    # return c.fetchone() is not None
    return False

# Validators
def is_valid_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.fullmatch(regex, email)

def is_strong_password(password):
    regex = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
    return re.fullmatch(regex, password)

# Signup Function
def signup():
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    Email_address = st.text_input("Email")
    new_password = st.text_input("Password", type='password')
    confirm_password = st.text_input("Confirm Password", type='password')

    create = st.button("Signup")
    if create:
        if username_exists(new_user):
            st.error("Username is already taken")
        elif email_exists(Email_address):
            st.error("Email is already registered")
        elif not is_valid_email(Email_address):
            st.error("Invalid email address")
        elif not is_strong_password(new_password):
            st.error("Password too weak. Must be 8 characters long and include numbers and letters.")
        elif new_password != confirm_password:
            st.error("Passwords do not match")
        else:
            add_userdata(new_user, Email_address, make_hashes(new_password))
            st.success("You have successfully created a valid Account")
            st.info("Go to Login Menu to login")
            # Clearing the form
            for field in ['new_user', 'Email_address', 'new_password', 'confirm_password']:
                if field in st.session_state:
                    st.session_state[field] = ''

# Login Function
def login():
    username = st.text_input("User Name", key="username")
    password = st.text_input("Password", type='password', key='password')

    if st.button("Login"):
        hashed_pswd = make_hashes(password)

        result = login_user(username, hashed_pswd)
        if result:
            st.success("Logged In as {}".format(username))
            st.session_state.authenticated = True
            st.session_state['current_user'] = username
            # Clear sensitive states
            del st.session_state["password"]
            del st.session_state["username"]
            st.rerun()
        else:
            st.warning("Incorrect Username/Password")

# Call create_usertable to ensure the table is created/updated when the script runs
create_usertable()