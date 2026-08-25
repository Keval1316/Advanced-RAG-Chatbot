from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone

T = TypeVar("T")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None


class ErrorDetails(BaseModel):
    message: str
    status_code: int
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetails


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    environment: str
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=utc_now)
    services: dict = Field(default_factory=dict)
