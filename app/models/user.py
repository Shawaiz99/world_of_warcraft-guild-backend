from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Enum
from sqlalchemy.orm import mapped_column
from app.extensions import db
import enum

class RoleEnum(enum.Enum):
    member = "member"
    guild_leader = "guild_leader"
    raider = "raider"
    recruiter = "recruiter"

class User(db.Model):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(String(150), nullable=False, unique=True)
    email = mapped_column(String(255), nullable=False, unique=True, index=True)
    password = mapped_column(String(255), nullable=False)
    is_active = mapped_column(Boolean, default=True)
    role = mapped_column(Enum(RoleEnum), default=RoleEnum.member)
    created_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "created_at": self.created_at.isoformat()
        }
