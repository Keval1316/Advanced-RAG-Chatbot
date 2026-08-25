from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, auth, users, knowledge_bases, documents, chat

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
