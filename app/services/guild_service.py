from typing import Optional
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
        user = db.session.get(User, user_id)  # Updated from User.query.get
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
        """
        Retrieves a guild by its unique ID.

        Args:
            guild_id (int): The ID of the guild to retrieve.

        Returns:
            Guild or None: The Guild object if found, otherwise None.
        """
        return db.session.get(Guild, guild_id)
