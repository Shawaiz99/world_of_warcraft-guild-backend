from typing import Optional, List
from app.models.guild import Guild
from app.models.user import User, RoleEnum
from app.extensions import db


class GuildService:
    @staticmethod
    def create_guild(name: str, description: str, user_id: int) -> Guild:
        # Check if a guild with the same name already exists
        existing_guild = Guild.query.filter_by(name=name).first()
        if existing_guild:
            raise ValueError("A guild with that name already exists.")

        # Check if the user is already in a guild
        user = db.session.get(User, user_id)
        if user is None:
            raise ValueError("User not found.")
        if user.guild_id is not None:
            raise ValueError("User is already in a guild.")

        # Create the new guild
        new_guild = Guild(
            name=name,
            description=description,
            created_by=user_id
        )

        # Add the user to the guild as a member
        user.guild = new_guild

        # Promote the user to guild leader
        user.role = RoleEnum.guild_leader

        # Save everything to the database
        db.session.add(new_guild)
        db.session.commit()

        return new_guild

    @staticmethod
    def get_guild_by_id(guild_id: int) -> Optional[Guild]:
        # Fetch the guild by its ID
        return db.session.get(Guild, guild_id)

    @staticmethod
    def get_guild_members(guild_id: int) -> Optional[List[User]]:
        """
        Returns a list of users who belong to the specified guild.
        If the guild doesn't exist, returns None.
        """
        guild = db.session.get(Guild, guild_id)

        if not guild:
            return None

        # Return all users related to this guild
        return guild.members

    @staticmethod
    def update_guild(guild_id: int, user_id: int, name: Optional[str],
                     description: Optional[str]) -> Guild:
        """
        Updates the name and/or description of a guild.
        Only the user who created the guild (guild leader) can update it.
        """

        # Step 1: Fetch the guild by its ID
        guild = db.session.get(Guild, guild_id)
        if not guild:
            raise ValueError("Guild not found")

        # Step 2: Ensure the user making the request is the guild creator
        if guild.created_by != int(user_id):
            raise ValueError("You do not have permission to update this guild")

        # Step 3: Check for name duplication (if name is changing)
        if name and name != guild.name:
            existing = Guild.query.filter_by(name=name).first()
            if existing:
                raise ValueError("Another guild with that name already exists")
            guild.name = name  # update name

        # Step 4: Update description if provided
        if description:
            guild.description = description

        # Step 5: Persist changes
        db.session.commit()

        return guild

    @staticmethod
    def leave_guild(user_id: int, guild_id: int) -> None:
        """
        Allows a user to leave a guild, unless they are the guild leader.
        """
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        if user.guild_id != guild_id:
            raise ValueError("You are not a member of this guild")

        if user.role == RoleEnum.guild_leader:
            raise ValueError(
                "Guild leaders must transfer leadership before leaving.")

        # Remove user from the guild
        user.guild_id = None
        db.session.commit()
