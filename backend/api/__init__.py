# RISKCORE API Routers
# On-premises PostgreSQL - NO CLOUD STORAGE

from fastapi import APIRouter

# Main API router that includes all sub-routers
api_router = APIRouter()

# Import sub-routers
from .positions import router as positions_router
from .trades import router as trades_router

# Include routers
api_router.include_router(positions_router, prefix="/positions", tags=["Positions"])
api_router.include_router(trades_router, prefix="/trades", tags=["Trades"])

# Future routers (Week 2)
# from .upload import router as upload_router
# api_router.include_router(upload_router, prefix="/upload", tags=["Upload"])
