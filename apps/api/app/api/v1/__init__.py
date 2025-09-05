"""API v1 endpoints package"""

from fastapi import APIRouter

from .documents import router as documents_router
from .rag import router as rag_router
from .quiz import router as quiz_router
from .profile import router as profile_router

# Create v1 API router
v1_router = APIRouter(prefix="/v1")

# Include all endpoint routers
v1_router.include_router(documents_router, prefix="/docs", tags=["Documents"])
v1_router.include_router(rag_router, prefix="/rag", tags=["RAG"])  
v1_router.include_router(quiz_router, prefix="/quiz", tags=["Quiz"])
v1_router.include_router(profile_router, prefix="/profile", tags=["Profile"])

__all__ = ["v1_router"]