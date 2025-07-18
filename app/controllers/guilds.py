from flask import Blueprint, request, jsonify
from app.services.guild_service import GuildService
from app.utils.auth import token_required
import traceback

# This blueprint handles all /api/v1/guilds routes
guilds_bp = Blueprint("guilds", __name__)


@guilds_bp.route("/guilds", methods=["POST"])
@token_required  # Ensures only logged-in users can access this route
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


@guilds_bp.route("/guilds/<int:guild_id>", methods=["GET"])
@token_required  # Logged-in users can view guild details
def get_guild_details(guild_id):
    print(f"📥 Fetching guild with ID: {guild_id}")
    print(f"📥 [GET] /guilds/{guild_id} requested by user {request.user_id}")

    try:
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

    except Exception as e:
        print("❌ Unexpected error in get_guild_details:", e)
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@guilds_bp.route("/guilds/<int:guild_id>/members", methods=["GET"])
@token_required  # Users must be logged in to view guild members
def get_guild_members(guild_id):
    """
    Returns a list of users who are members of the specified guild.
    """
    members = GuildService.get_guild_members(guild_id)

    if members is None:
        return jsonify({"error": "Guild not found"}), 404

    return jsonify([member.serialize() for member in members])


@guilds_bp.route("/guilds/<int:guild_id>", methods=["PATCH"])
@token_required
def update_guild(guild_id):
    """
    Allows a guild leader to update the name and/or description of their guild.
    Only the creator (guild leader) can make changes.
    """
    data = request.get_json() or {}
    new_name = data.get("name")
    new_description = data.get("description")

    if not new_name and not new_description:
        return jsonify({"error": "No update fields provided"}), 400

    try:
        updated_guild = GuildService.update_guild(
            guild_id=guild_id,
            user_id=request.user_id,
            name=new_name,
            description=new_description
        )
        return jsonify({
            "id": updated_guild.id,
            "name": updated_guild.name,
            "description": updated_guild.description,
            "created_by": updated_guild.created_by,
            "created_at": updated_guild.created_at.isoformat()
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400


@guilds_bp.route("/guilds/<int:guild_id>/leave", methods=["DELETE"])
@token_required  # Ensure the user is authenticated
def leave_guild(guild_id):
    """
    Allows a logged-in user to leave their current guild.
    Guild leaders are not allowed to leave unless they transfer leadership.
    """
    try:
        GuildService.leave_guild(user_id=request.user_id, guild_id=guild_id)
        return jsonify({"message": "You have successfully left the guild."}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400


@guilds_bp.route("/guilds/<int:guild_id>/transfer-leadership", methods=["POST"])
@token_required  # Only authenticated users can perform this action
def transfer_guild_leadership(guild_id):
    """
    Allows the current guild leader to transfer leadership to another member of the guild.
    Expects 'new_leader_id' in the JSON payload.
    """
    data = request.get_json() or {}
    new_leader_raw = data.get("new_leader_id")

    if new_leader_raw is None:
        return jsonify({"error": "New leader ID is required"}), 400

    try:
        new_leader_id = int(new_leader_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "New leader ID must be a valid integer"}), 400

    try:
        GuildService.transfer_leadership(
            guild_id=guild_id,
            current_leader_id=request.user_id,
            new_leader_id=new_leader_id
        )
        return jsonify({"message": "Guild leadership has been successfully transferred."}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400


@guilds_bp.route("/guilds/<int:guild_id>/members/<int:member_id>", methods=["DELETE"])
@token_required  # Only logged-in users can access
def kick_guild_member(guild_id, member_id):
    """
    Allows a guild leader to kick a member from their guild.
    Only the leader of the guild can perform this action.
    """
    try:
        GuildService.kick_member(
            guild_id=guild_id,
            leader_id=request.user_id,
            member_id=member_id
        )
        return jsonify({"message": "Member has been removed from the guild."}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
