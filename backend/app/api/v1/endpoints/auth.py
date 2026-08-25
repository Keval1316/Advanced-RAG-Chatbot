from typing import Union
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token
from backend.app.core.exceptions import UnauthorizedException
from backend.app.db.session import get_db
from backend.app.schemas.common import APIResponse
from backend.app.schemas.user import UserCreate, UserResponse
from backend.app.schemas.auth import LoginRequest, Token
from backend.app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> APIResponse[UserResponse]:
    user = auth_service.register_user(db, user_in)
    return APIResponse(
        success=True,
        message="User registered successfully.",
        data=UserResponse.model_validate(user)
    )


@router.post(
    "/login",
    response_model=APIResponse[Token],
    status_code=status.HTTP_200_OK,
    summary="Log in and retrieve JWT access token"
)
def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> APIResponse[Token]:
    user = auth_service.authenticate_user(
        db,
        username_or_email=login_data.username_or_email,
        password=login_data.password
    )
    if not user:
        raise UnauthorizedException(message="Incorrect username/email or password.")

    access_token = create_access_token(subject=user.id)
    token_response = Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )
    return APIResponse(
        success=True,
        message="Login successful.",
        data=token_response
    )


@router.post(
    "/token",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="OAuth2 compatible token login for Swagger UI",
    include_in_schema=False
)
def login_oauth2_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    user = auth_service.authenticate_user(
        db,
        username_or_email=form_data.username,
        password=form_data.password
    )
    if not user:
        raise UnauthorizedException(message="Incorrect username or password.")

    access_token = create_access_token(subject=user.id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )
