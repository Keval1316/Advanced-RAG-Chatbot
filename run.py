import os
import sys
import uvicorn
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.core.config import settings

def main():
    port = int(os.environ.get("PORT", settings.BACKEND_PORT))
    host = "0.0.0.0"
    is_prod = os.environ.get("APP_ENV") == "production" or bool(os.environ.get("PORT"))
    reload_flag = False if is_prod else settings.DEBUG

    print("=" * 65)
    print(f"🚀 Launching {settings.APP_NAME}")
    print("=" * 65)
    print(f"🌐 Server binding to     : http://{host}:{port}")
    print(f"📄 Swagger API Docs     : http://{host}:{port}{settings.API_V1_PREFIX}/docs")
    print(f"🩺 Health Check Endpoint : http://{host}:{port}/health")
    print("=" * 65)
    print("Server ready for incoming connections.\n")

    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=reload_flag,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )

if __name__ == "__main__":
    main()

