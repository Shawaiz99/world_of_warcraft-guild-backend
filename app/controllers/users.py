from flask import Blueprint, request, jsonify
from app.utils.auth import requires_roles
from app.services.user_service import UserService
from app.utils.auth import token_required

users_bp = Blueprint("users_bp", __name__)


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
        return jsonify({"error": "User not found"}), 404

    return user.serialize(), 200


@users_bp.route("/login", methods=["POST"])
def login():
    """
    Logs in a user by verifying credentials.
    Expects JSON: { "email": ..., "password": ... }
    """
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    try:
        user, token = UserService.login(email, password)
        return jsonify({
            "user": user.serialize(),
            "token": token
        }), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 401


@users_bp.route("/protected", methods=["GET"])
@token_required
def protected_route():
    """
    A test route that requires a valid JWT.
    Returns the user_id from the token.
    """
    return jsonify({
        "message": "Access granted!",
        "user_id": request.user_id
    }), 200


@users_bp.route("/guild-leader-only", methods=["GET"])
@token_required
@requires_roles("guild_leader")
def guild_leader_only():
    """
    Only accessible by users with the 'guild_leader' role.
    """
    return jsonify({
        "message": "Welcome Guild Leader!",
        "user_id": request.user_id,
        "role": request.user_role
    }), 200
