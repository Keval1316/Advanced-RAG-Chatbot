import uuid
from typing import Optional
from pydantic import BaseModel, Field
from backend.app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Email or Username")
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
