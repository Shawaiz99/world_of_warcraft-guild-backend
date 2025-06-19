from app.extensions import db
from app.models.user import User
from sqlalchemy import select
from typing import Optional

class UserRepository:
    @staticmethod
    def create_user(username: str, email: str, password: str) -> User:
        """Create and save a new user"""
        user = User(
            username=username,
            email=email,
            password=password  # (we'll hash it later)
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """Get a user by their ID"""
        stmt = select(User).where(User.id == user_id)
        result = db.session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Get a user by their email"""
        stmt = select(User).where(User.email == email)
        result = db.session.execute(stmt)
        return result.scalars().first()
