import hashlib

# Demo users for the project
# In a production application, credentials should be stored
# securely in a database with proper password hashing.

USERS = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest(),
    "candidate": hashlib.sha256("candidate123".encode()).hexdigest(),
}


def authenticate(username, password):
    """Validate username and password."""

    if not username or not password:
        return False

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    return USERS.get(username) == password_hash