"""StudyRAG FastAPI Application"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.health import router as health_router
from app.api.schema import router as schema_router
from app.api.v1 import v1_router
from app.core.config import get_settings
from app.db.session import init_database, cleanup_database
from app.openapi import custom_openapi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management"""
    # Startup
    logger.info(f"Starting StudyRAG API v{__version__}")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Application startup completed")
        
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down StudyRAG API")
        await cleanup_database()
        logger.info("Application shutdown completed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Create FastAPI instance
    app = FastAPI(
        title="StudyRAG API",
        description="RAG-Chat with Citations & Quiz Generation for Students",
        version=__version__,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for production
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=["*"]  # Configure appropriately for production
        )
    
    # Add routers
    app.include_router(health_router, prefix="", tags=["Health"])
    app.include_router(schema_router, prefix="/schema", tags=["Schema"])
    app.include_router(v1_router, prefix="/api")
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception handler caught: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "type": "internal_server_error",
                "title": "Internal Server Error", 
                "status": 500,
                "detail": "An unexpected error occurred"
            }
        )
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "StudyRAG API",
            "version": __version__,
            "docs_url": "/docs" if settings.debug else None
        }
    
    # Set custom OpenAPI schema
    app.openapi = lambda: custom_openapi(app)
    
    return app


# Create the app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )