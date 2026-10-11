"""Run this ONCE to create an administrator: python create_admin.py"""
import getpass
import sqlite3

from main import db
from security import hash_password, validate_username


def main():
    with db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
    if count:
        print("An administrator already exists. No changes were made.")
        return

    username = input("Choose administrator username (3–32 characters): ").strip()
    if not validate_username(username):
        print("Invalid username. Start with a letter, then use letters, numbers, '.', '_' or '-'.")
        return
    password = getpass.getpass("Choose administrator password (12+ characters): ")
    repeated = getpass.getpass("Confirm password: ")
    if password != repeated:
        print("Passwords do not match. No account created.")
        return
    try:
        digest = hash_password(password)
    except ValueError as exc:
        print(exc)
        return
    try:
        with db() as conn:
            conn.execute("INSERT INTO users(username,password_hash,role) VALUES (?,?, 'admin')", (username, digest))
        print(f"Administrator '{username}' created. You can now sign in at http://127.0.0.1:5173")
    except sqlite3.IntegrityError:
        print("Username already exists. No changes made.")


if __name__ == "__main__":
    main()
