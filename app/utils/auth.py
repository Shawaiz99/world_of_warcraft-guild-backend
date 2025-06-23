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

            # Decode token and attach user_id to the request context
            decoded = jwt.decode(token, secret, algorithms=["HS256"])
            request.user_id = decoded["sub"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated
