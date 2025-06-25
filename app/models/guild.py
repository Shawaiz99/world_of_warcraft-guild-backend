from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, relationship


class Guild(db.Model):
    __tablename__ = "guilds"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False, unique=True)
    description = mapped_column(String(255))
    created_by = mapped_column(Integer, ForeignKey(
        "users.id"), nullable=False)  # must come before used
    created_at = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    members = relationship("User", back_populates="guild")
    creator = relationship("User", foreign_keys=[
                           created_by], backref="created_guilds")
