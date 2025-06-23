from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from os import getenv

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

def generate_token(user_id: int) -> str:
    """
    Generates a JWT token with user ID and 1 hour expiration.
    """
    payload = {
        "sub": str(user_id),  # subject must be a string
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    secret = getenv("SECRET_KEY")
    token = jwt.encode(payload, secret, algorithm="HS256")

    # Ensure token is a string, not bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token
