from flask import Blueprint, request, jsonify
from app.services.user_service import UserService

users_bp = Blueprint("users", __name__)

@users_bp.route("/register", methods=["POST"])
def register():
    """
    Registers a new user.
    Expects JSON: { "username": ..., "email": ..., "password": ... }
    """
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Basic validation
    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    try:
        user = UserService.register_user(username, email, password)
        return jsonify(user.serialize()), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
