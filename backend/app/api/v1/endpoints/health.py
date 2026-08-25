from fastapi import APIRouter, status
from backend.app.schemas.common import APIResponse, HealthResponse, utc_now
from backend.app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=APIResponse[HealthResponse],
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Returns current server status, environment, and subsystem health indications."
)
async def health_check() -> APIResponse[HealthResponse]:
    health_data = HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        version="1.0.0",
        timestamp=utc_now(),
        services={
            "api": "operational",
            "database": "configured",
            "vector_store": "configured",
            "llm": "configured" if bool(settings.GROQ_API_KEY) else "groq_api_key_pending"
        }
    )
    return APIResponse(
        success=True,
        message="Service is healthy",
        data=health_data
    )
