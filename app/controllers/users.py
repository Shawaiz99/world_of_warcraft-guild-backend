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


@users_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """
    Fetch a user by their ID.
    Returns 404 if not found.
    """
    user = UserService.get_user_by_id(user_id)

    if not user:
        return {"error": "User not found"}, 404

    return user.serialize(), 200