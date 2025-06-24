from typing import Optional
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.utils.security import hash_password, verify_password, generate_token


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
    def login(email: str, password: str) -> tuple[User, str]:
        """
        Authenticates a user and returns the user and JWT token.
        Raises ValueError if credentials are invalid.
        """
        user = UserRepository.get_by_email(email)
        if not user or not verify_password(user.password, password):
            raise ValueError("Invalid email or password")

        token = generate_token(user.id, user.role.value)
        return user, token

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
