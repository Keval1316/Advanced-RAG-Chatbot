from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from backend.app.core.logging import logger


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, details=details)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication required or credentials invalid", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Permission denied for this resource", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class LLMServiceException(AppException):
    def __init__(self, message: str = "LLM inference service error", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY, details=details)


class VectorStoreException(AppException):
    def __init__(self, message: str = "Vector database operation error", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, details=details)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.error(f"AppException on {request.method} {request.url.path}: {exc.message} (status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "status_code": exc.status_code,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "message": "Request validation failed",
                "status_code": 422,
                "details": exc.errors()
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "An internal server error occurred.",
                "status_code": 500,
                "details": str(exc) if settings_debug_enabled() else None
            }
        }
    )


def settings_debug_enabled() -> bool:
    from backend.app.core.config import settings
    return settings.DEBUG
