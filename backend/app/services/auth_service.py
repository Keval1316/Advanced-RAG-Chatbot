import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate
from backend.app.core.security import get_password_hash, verify_password
from backend.app.core.exceptions import AppException
from fastapi import status


class AuthService:
    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username.strip()).first()

    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        # Check if email is already registered
        if AuthService.get_by_email(db, user_in.email):
            raise AppException(
                message="A user with this email already exists.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Check if username is already registered
        if AuthService.get_by_username(db, user_in.username):
            raise AppException(
                message="A user with this username already exists.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = User(
            email=user_in.email.lower().strip(),
            username=user_in.username.strip(),
            hashed_password=get_password_hash(user_in.password),
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(
        db: Session,
        username_or_email: str,
        password: str
    ) -> Optional[User]:
        clean_input = username_or_email.strip()
        user = db.query(User).filter(
            or_(
                User.email == clean_input.lower(),
                User.username == clean_input
            )
        ).first()

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user


auth_service = AuthService()
