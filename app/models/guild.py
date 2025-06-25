from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, relationship


class Guild(db.Model):
    __tablename__ = "guilds"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False, unique=True)
    description = mapped_column(String(255))
    created_by = mapped_column(Integer, ForeignKey("users.id", use_alter=True), nullable=False)
    created_at = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    members = relationship(
        "User",
        back_populates="guild",
        foreign_keys="User.guild_id"
    )

    creator = relationship(
        "User", backref="created_guilds", foreign_keys=[created_by])
