from app.repositories.user_repository import UserRepository
from app.models.user import User
from typing import Optional
from app.utils.security import hash_password

class UserService:
    @staticmethod
    def register_user(username: str, email: str, password: str) -> User:
        """
        Registers a new user if the email is not already taken.
        Raises a ValueError if email is already in use.
        """
        existing_user = UserRepository.get_by_email(email)
        if existing_user:
            raise ValueError("Email is already registered.")

        hashed_password = hash_password(password)
        return UserRepository.create_user(username, email, hashed_password)

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """
        Fetch a user by their unique ID.
        Returns None if not found.
        """
        return UserRepository.get_by_id(user_id)

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """
        Fetch a user by their email.
        Returns None if not found.
        """
        return UserRepository.get_by_email(email)
