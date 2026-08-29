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
    port = settings.BACKEND_PORT
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode...")
    print("\n" + "=" * 65)
    print(f"🚀 {settings.APP_NAME} is Running!")
    print("=" * 65)
    print(f"🌐 Frontend Web UI       : http://localhost:{port}")
    print(f"📄 Swagger API Docs     : http://localhost:{port}{settings.API_V1_PREFIX}/docs")
    print(f"🩺 Health Check Endpoint : http://localhost:{port}/health")
    print(f"📊 Streamlit UI (Option) : http://localhost:{settings.FRONTEND_PORT} (run: streamlit run frontend/app.py)")
    print("=" * 65 + "\n")

    # Initialize database tables if not already created
    try:
        from backend.app.db.session import engine
        from backend.app.models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized and verified successfully.")
    except Exception as e:
        logger.warning(f"Database table initialization notice: {str(e)}")

    # Warm up models asynchronously so server is immediately responsive
    try:
        from backend.app.rag.embeddings import embedding_service
        from backend.app.rag.reranker import reranker
        from backend.app.services.vector_service import vector_service
        embedding_service.warmup()
        reranker.warmup()
        vector_service.get_client()
        logger.info("All RAG pipelines and vector connections warmed up successfully.")
    except Exception as e:
        logger.warning(f"Startup warmup note: {str(e)}")

    yield
    # Shutdown lifecycle
    logger.info(f"Shutting down {settings.APP_NAME}...")


import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Root workspace directory for frontend static assets
BASE_DIR = Path(__file__).resolve().parents[2]
INDEX_HTML_PATH = BASE_DIR / "index.html"
STYLE_CSS_PATH = BASE_DIR / "style.css"
SCRIPT_JS_PATH = BASE_DIR / "script.js"

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

    # Health & System Status Endpoint
    @application.get("/api/v1/system/status", tags=["System"])
    @application.get("/health", tags=["System"])
    async def health_status():
        return {
            "status": "healthy",
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "environment": settings.APP_ENV,
            "docs": f"{settings.API_V1_PREFIX}/docs"
        }

    # Frontend UI Routes
    @application.get("/", tags=["Frontend"])
    async def serve_index(request: Request):
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header and "text/html" not in accept_header:
            return JSONResponse({
                "name": settings.APP_NAME,
                "version": "1.0.0",
                "status": "healthy",
                "health": f"{settings.API_V1_PREFIX}/health",
                "docs": f"{settings.API_V1_PREFIX}/docs"
            })
        if INDEX_HTML_PATH.exists():
            return FileResponse(INDEX_HTML_PATH, media_type="text/html")
        return JSONResponse({
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "status": "healthy",
            "health": f"{settings.API_V1_PREFIX}/health",
            "docs": f"{settings.API_V1_PREFIX}/docs"
        })

    @application.get("/style.css", include_in_schema=False)
    async def serve_style():
        if STYLE_CSS_PATH.exists():
            return FileResponse(STYLE_CSS_PATH, media_type="text/css")
        return JSONResponse({"error": "style.css not found"}, status_code=404)

    @application.get("/script.js", include_in_schema=False)
    async def serve_script():
        if SCRIPT_JS_PATH.exists():
            return FileResponse(SCRIPT_JS_PATH, media_type="application/javascript")
        return JSONResponse({"error": "script.js not found"}, status_code=404)

    # Mount uploads directory if it exists
    uploads_path = BASE_DIR / "uploads"
    if uploads_path.exists():
        application.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

    return application


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )

