"""Small standard-library authentication helpers for the CampusFlow local project.

Password hashes: PBKDF2-HMAC-SHA256 with per-user random salts.
Sessions: cryptographically random bearer tokens; only SHA-256 token digests stored.
"""
import hashlib
import hmac
import re
import secrets
import time

ITERATIONS = 420_000
SESSION_TTL_SECONDS = 8 * 60 * 60
LOCK_SECONDS = 5 * 60
MAX_FAILED_LOGINS = 5
USERNAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{2,31}$")


def validate_username(username):
    return bool(USERNAME_PATTERN.fullmatch(username))


def hash_password(password):
    if not 12 <= len(password) <= 128:
        raise ValueError("Password must contain 12–128 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, encoded):
    try:
        method, rounds, salt, expected = encoded.split("$")
        if method != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError, AttributeError):
        return False


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def issue_token():
    return secrets.token_urlsafe(48)


def now():
    return int(time.time())


def setup_auth_tables(connection):
    connection.executescript("""
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin','teacher')),
        active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
        attempts INTEGER NOT NULL DEFAULT 0,
        locked_until INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      );
      CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at INTEGER NOT NULL
      );
      CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
    """)


def account_view(row):
    return {"id": row["id"], "username": row["username"], "role": row["role"], "active": bool(row["active"])}
