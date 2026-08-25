import uuid
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import decode_token
from backend.app.core.exceptions import UnauthorizedException, ForbiddenException
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.auth_service import auth_service

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedException(message="Invalid or expired authentication token.")

    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(message="Token missing subject identifier.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(message="Invalid user identifier format in token.")

    user = auth_service.get_by_id(db, user_id=user_id)
    if not user:
        raise UnauthorizedException(message="User associated with this token no longer exists.")

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise ForbiddenException(message="Inactive user account.")
    return current_user
