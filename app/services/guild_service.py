from app.models.guild import Guild
from app.extensions import db
from app.models.user import User

class GuildService:
    @staticmethod
    def create_guild(name: str, description: str, creator_id: int) -> Guild:
        """
        Creates a new guild and assigns the creator as the guild leader.
        """
        if db.session.execute(db.select(Guild).filter_by(name=name)).scalar():
            raise ValueError("A guild with this name already exists.")

        guild = Guild(name=name, description=description, created_by=creator_id)
        db.session.add(guild)
        db.session.flush()  # Assigns guild.id before committing

        user = db.session.execute(db.select(User).filter_by(id=creator_id)).scalar_one()
        user.guild_id = guild.id
        user.role = user.role  # Keep same role unless you want to force 'guild_leader'

        db.session.commit()
        return guild
