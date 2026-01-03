"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.config import get_settings
from app.database import init_db
from app.routes import router

settings = get_settings()

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    level="INFO" if not settings.DEBUG else "DEBUG"
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)

# Create FastAPI app
app = FastAPI(
    title="Newsletter AI API",
    description="AI-powered newsletter generation with semantic search and personalization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["Newsletter"])


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Newsletter AI application...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Newsletter AI application...")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Newsletter AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
