from flask import Blueprint, request, jsonify
from app.services.guild_service import GuildService
from app.utils.auth import token_required

guilds_bp = Blueprint("guilds", __name__)

@guilds_bp.route("/guilds", methods=["POST"])
@token_required
def create_guild():
    data = request.get_json() or {}
    name = data.get("name")
    description = data.get("description")

    if not name:
        return jsonify({"error": "Guild name is required"}), 400

    try:
        guild = GuildService.create_guild(name, description, request.user_id)
        return jsonify({
            "id": guild.id,
            "name": guild.name,
            "description": guild.description,
            "created_by": guild.created_by,
            "created_at": guild.created_at.isoformat()
        }), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
