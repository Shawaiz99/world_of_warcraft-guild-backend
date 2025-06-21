from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """
    Hashes a plain text password using Werkzeug.
    """
    return generate_password_hash(password)

def verify_password(stored_hash: str, plain_password: str) -> bool:
    """
    Checks if the plain password matches the hashed one.
    """
    return check_password_hash(stored_hash, plain_password)
