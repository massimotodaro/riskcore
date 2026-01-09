# API Skill

> FastAPI conventions for RISKCORE backend

---

## Project Structure

```
/backend
├── main.py                 # FastAPI app entry point
├── requirements.txt
├── .env.example
├── /api
│   ├── __init__.py
│   ├── positions.py        # /api/v1/positions
│   ├── portfolios.py       # /api/v1/portfolios
│   ├── risk.py             # /api/v1/risk
│   ├── securities.py       # /api/v1/securities
│   └── ai.py               # /api/v1/ai
├── /core
│   ├── __init__.py
│   ├── config.py           # Settings/environment
│   ├── database.py         # Supabase client
│   ├── security.py         # Auth helpers
│   └── exceptions.py       # Custom exceptions
├── /services
│   ├── __init__.py
│   ├── aggregation.py      # Core aggregation logic
│   ├── pricing.py          # FinancePy integration
│   ├── risk_engine.py      # Riskfolio-Lib integration
│   └── market_data.py      # OpenBB integration
├── /models
│   ├── __init__.py
│   ├── position.py         # Pydantic models
│   ├── portfolio.py
│   └── risk.py
└── /tests
    ├── __init__.py
    ├── test_positions.py
    └── test_risk.py
```

---

## Main App Setup

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import positions, portfolios, risk, securities, ai
from core.config import settings

app = FastAPI(
    title="RISKCORE API",
    description="Multi-manager risk aggregation platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(positions.router, prefix="/api/v1/positions", tags=["positions"])
app.include_router(portfolios.router, prefix="/api/v1/portfolios", tags=["portfolios"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])
app.include_router(securities.router, prefix="/api/v1/securities", tags=["securities"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
```

---

## Router Pattern

```python
# api/positions.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List, Optional
from models.position import Position, PositionCreate, PositionResponse
from services.aggregation import AggregationService
from core.database import get_db

router = APIRouter()

@router.get("/", response_model=List[PositionResponse])
async def list_positions(
    portfolio_id: Optional[str] = None,
    as_of_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db = Depends(get_db)
):
    """List positions with optional filters."""
    query = db.table("positions").select("*, securities(ticker, name)")
    
    if portfolio_id:
        query = query.eq("portfolio_id", portfolio_id)
    if as_of_date:
        query = query.eq("as_of_date", as_of_date)
    
    result = query.range(skip, skip + limit - 1).execute()
    return result.data

@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(position_id: str, db = Depends(get_db)):
    """Get a single position by ID."""
    result = db.table("positions") \
        .select("*, securities(*)") \
        .eq("id", position_id) \
        .single() \
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Position not found")
    
    return result.data

@router.post("/", response_model=PositionResponse, status_code=201)
async def create_position(position: PositionCreate, db = Depends(get_db)):
    """Create a new position."""
    result = db.table("positions") \
        .insert(position.model_dump()) \
        .execute()
    
    return result.data[0]

@router.post("/upload")
async def upload_positions(
    file: UploadFile = File(...),
    portfolio_id: Optional[str] = None,
    db = Depends(get_db)
):
    """Upload positions from CSV/Excel file."""
    # Handle file upload
    service = AggregationService(db)
    result = await service.process_file_upload(file, portfolio_id)
    
    return {
        "status": "success",
        "positions_created": result.created,
        "positions_updated": result.updated,
        "errors": result.errors
    }
```

---

## Pydantic Models

```python
# models/position.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

class PositionBase(BaseModel):
    portfolio_id: UUID
    security_id: UUID
    quantity: Decimal
    market_value: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
    currency: str = "USD"
    as_of_date: date

class PositionCreate(PositionBase):
    source_system: Optional[str] = None
    source_id: Optional[str] = None

class PositionResponse(PositionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Joined data
    securities: Optional[dict] = None
    
    class Config:
        from_attributes = True

class PositionUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
```

---

## Config Pattern

```python
# core/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Claude AI
    ANTHROPIC_API_KEY: str
    
    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Database Dependency

```python
# core/database.py
from supabase import create_client, Client
from core.config import settings

def get_db() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
```

---

## Error Handling

```python
# core/exceptions.py
from fastapi import HTTPException

class NotFoundError(HTTPException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            status_code=404,
            detail=f"{resource} with id {id} not found"
        )

class ValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=422,
            detail=message
        )

class DuplicateError(HTTPException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=409,
            detail=f"{resource} already exists"
        )
```

---

## API Response Patterns

### Success responses
```python
# Single item
return result.data

# List with pagination
return {
    "items": result.data,
    "total": total_count,
    "skip": skip,
    "limit": limit
}

# Action result
return {
    "status": "success",
    "message": "Positions uploaded",
    "count": 150
}
```

### Error responses
```python
# 404
raise HTTPException(status_code=404, detail="Position not found")

# 422 Validation
raise HTTPException(status_code=422, detail="Invalid date format")

# 500
raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Endpoint Naming

| Action | Method | Path | Example |
|--------|--------|------|---------|
| List | GET | `/resources` | `GET /positions` |
| Get one | GET | `/resources/{id}` | `GET /positions/123` |
| Create | POST | `/resources` | `POST /positions` |
| Update | PUT | `/resources/{id}` | `PUT /positions/123` |
| Partial update | PATCH | `/resources/{id}` | `PATCH /positions/123` |
| Delete | DELETE | `/resources/{id}` | `DELETE /positions/123` |
| Action | POST | `/resources/{id}/action` | `POST /positions/123/recalculate` |
| Upload | POST | `/resources/upload` | `POST /positions/upload` |

---

## Testing

```python
# tests/test_positions.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_positions():
    response = client.get("/api/v1/positions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_position():
    position_data = {
        "portfolio_id": "...",
        "security_id": "...",
        "quantity": 100,
        "as_of_date": "2025-01-09"
    }
    response = client.post("/api/v1/positions", json=position_data)
    assert response.status_code == 201

def test_get_position_not_found():
    response = client.get("/api/v1/positions/nonexistent-id")
    assert response.status_code == 404
```

---

## Don't

- ❌ Don't put business logic in routers (use services)
- ❌ Don't skip input validation (use Pydantic)
- ❌ Don't hardcode credentials
- ❌ Don't return raw database errors to clients
- ❌ Don't skip error handling
- ❌ Don't use sync operations in async endpoints

---

*API patterns for RISKCORE*
