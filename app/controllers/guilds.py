from flask import Blueprint, request, jsonify
from app.services.guild_service import GuildService
from app.utils.auth import token_required

# This blueprint handles all /api/v1/guilds routes
guilds_bp = Blueprint("guilds", __name__)


@guilds_bp.route("/guilds", methods=["POST"])
@token_required  # Ensures only logged-in users can access this route
def create_guild():
    # Parse incoming JSON data
    data = request.get_json() or {}
    name = data.get("name")
    description = data.get("description")

    # Check that a name was provided
    if not name:
        return jsonify({"error": "Guild name is required"}), 400

    try:
        # Attempt to create a new guild using a service layer
        # This method will handle checks like duplicate name or user already in a guild
        guild = GuildService.create_guild(name, description, request.user_id)

        # If successful, return the new guild's data
        return jsonify({
            "id": guild.id,
            "name": guild.name,
            "description": guild.description,
            "created_by": guild.created_by,
            "created_at": guild.created_at.isoformat()
        }), 201

    except ValueError as ve:
        # If something went wrong (like name already taken), return the error
        return jsonify({"error": str(ve)}), 400


@guilds_bp.route("/guilds/<int:guild_id>", methods=["GET"])
@token_required
def get_guild_details(guild_id):
    guild = GuildService.get_guild_by_id(guild_id)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    return jsonify({
        "id": guild.id,
        "name": guild.name,
        "description": guild.description,
        "created_by": guild.created_by,
        "created_at": guild.created_at.isoformat()
    })
