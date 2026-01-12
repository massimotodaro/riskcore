# RISKCORE Backend - FastAPI Application
# On-premises deployment - NO CLOUD STORAGE

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from .config import get_settings
from .database import check_database_connection, close_all_connections

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("DEPLOYMENT MODE: On-premises (all data stays local)")

    # Verify database connection
    db_check = check_database_connection()
    if db_check["status"] == "connected":
        logger.info("Database connection verified (local PostgreSQL)")
    else:
        logger.warning(f"Database connection check failed: {db_check['error']}")

    yield

    # Shutdown
    logger.info("Shutting down RISKCORE")
    close_all_connections()
    logger.info("Database connections closed")


# Create FastAPI application
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="""
## Multi-Manager Risk Aggregation Platform

**RISKCORE is designed for on-premises deployment.**

All position, trade, and risk data stays on YOUR servers.
No cloud storage - ever.

### Features
- Position & trade ingestion (API, CSV, FIX)
- Multi-PM aggregation
- Cross-PM netting & overlap detection
- Risk calculations (VaR, exposures, Greeks)
- Natural language queries (Claude)
""",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        },
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


@app.get("/", tags=["Health"])
def root():
    """Root endpoint with API information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "deployment": "on-premises",
        "docs": "/docs",
        "health": "/health",
        "api": f"{settings.api_v1_prefix}/status",
    }


@app.get(f"{settings.api_v1_prefix}/status", tags=["Health"])
def api_status():
    """
    API status with database connectivity check.

    Returns:
        Status information including database connectivity.
    """
    db_check = check_database_connection()

    return {
        "status": "operational",
        "version": settings.app_version,
        "deployment": "on-premises",
        "database": db_check["status"],
        "database_error": db_check["error"],
        "environment": "development" if settings.debug else "production",
    }


# Include API routers
from .api import api_router

app.include_router(api_router, prefix=settings.api_v1_prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
