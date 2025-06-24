from functools import wraps
from flask import request, jsonify
import jwt
from os import getenv

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing!"}), 401

        try:
            secret = getenv("SECRET_KEY")
            if not secret:
                return jsonify({"error": "Server configuration issue"}), 500

            # Decode token and attach user_id and role to the request context
            decoded = jwt.decode(token, secret, algorithms=["HS256"])
            request.user_id = decoded["sub"]
            request.user_role = decoded.get("role")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated

def requires_roles(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check if user_id and role are set by token_required
            if not hasattr(request, "user_id") or not hasattr(request, "user_role"):
                return jsonify({"error": "Missing authentication context"}), 403

            # Reject if user doesn't have one of the allowed roles
            if request.user_role not in roles:
                return jsonify({"error": "Forbidden: Insufficient role"}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator
