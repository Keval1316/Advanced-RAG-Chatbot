import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from backend.app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode...")
    logger.info(f"API documentation available at {settings.API_V1_PREFIX}/docs")
    yield
    # Shutdown lifecycle
    logger.info(f"Shutting down {settings.APP_NAME}...")


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Production-grade Enterprise AI Knowledge Assistant with Advanced RAG, Hybrid Search & Citations.",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan
    )

    # CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS if isinstance(settings.BACKEND_CORS_ORIGINS, list) else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    application.add_exception_handler(AppException, app_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(Exception, generic_exception_handler)

    # Request Processing Time Middleware
    @application.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time-Seconds"] = f"{process_time:.4f}"
        return response

    # Include API Routers
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "environment": settings.APP_ENV,
            "docs": f"{settings.API_V1_PREFIX}/docs",
            "health": f"{settings.API_V1_PREFIX}/health"
        }

    return application


app = create_application()
