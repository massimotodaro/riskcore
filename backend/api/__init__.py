# RISKCORE API Routers
# On-premises PostgreSQL - NO CLOUD STORAGE

from fastapi import APIRouter

# Main API router that includes all sub-routers
api_router = APIRouter()

# Import sub-routers
from .positions import router as positions_router
from .trades import router as trades_router
from .upload import router as upload_router
from .fix import router as fix_router
from .risk import router as risk_router
from .aggregation import router as aggregation_router

# Include routers
api_router.include_router(positions_router, prefix="/positions", tags=["Positions"])
api_router.include_router(trades_router, prefix="/trades", tags=["Trades"])
api_router.include_router(upload_router, prefix="/upload", tags=["Upload"])
api_router.include_router(fix_router, prefix="/fix", tags=["FIX Protocol"])
api_router.include_router(risk_router, prefix="/risk", tags=["Risk"])
api_router.include_router(aggregation_router, prefix="/aggregation", tags=["Aggregation"])
