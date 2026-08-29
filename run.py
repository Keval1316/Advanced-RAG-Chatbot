import os
import sys
import uvicorn
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.core.config import settings

def main():
    print("=" * 65)
    print(f"🚀 Launching {settings.APP_NAME}")
    print("=" * 65)
    print(f"🌐 Frontend Web UI       : http://localhost:{settings.BACKEND_PORT}")
    print(f"📄 Swagger API Docs     : http://localhost:{settings.BACKEND_PORT}/api/v1/docs")
    print(f"🩺 Health Check Endpoint : http://localhost:{settings.BACKEND_PORT}/health")
    print(f"📊 Streamlit UI (Option) : http://localhost:{settings.FRONTEND_PORT} (run: streamlit run frontend/app.py)")
    print("=" * 65)
    print("Press CTRL+C to stop the server.\n")

    uvicorn.run(
        "backend.app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )

if __name__ == "__main__":
    main()
