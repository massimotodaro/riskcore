# RISKCORE Upload Models

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any
from enum import Enum


class UploadFileType(str, Enum):
    """Upload file type enum - matches database."""
    POSITIONS_CSV = "positions_csv"
    POSITIONS_XLSX = "positions_xlsx"
    TRADES_CSV = "trades_csv"
    TRADES_XLSX = "trades_xlsx"
    FIX_MESSAGE = "fix_message"


class UploadStatus(str, Enum):
    """Upload status enum - matches database."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ColumnMapping(BaseModel):
    """Column mapping for file upload."""
    ticker: Optional[str] = None
    cusip: Optional[str] = None
    isin: Optional[str] = None
    sedol: Optional[str] = None
    quantity: Optional[str] = None
    price: Optional[str] = None
    direction: Optional[str] = None
    side: Optional[str] = None
    cost_basis: Optional[str] = None
    market_value: Optional[str] = None
    currency: Optional[str] = None
    book: Optional[str] = None
    as_of_date: Optional[str] = None
    trade_date: Optional[str] = None
    settlement_date: Optional[str] = None
    trade_time: Optional[str] = None
    broker: Optional[str] = None
    counterparty: Optional[str] = None
    commission: Optional[str] = None
    fees: Optional[str] = None
    trade_id: Optional[str] = None


class FilePreviewResponse(BaseModel):
    """Response for file preview (before import)."""
    success: bool
    error: Optional[str] = None
    filename: str
    file_type: str
    columns: List[str] = []
    mapping: Dict[str, str] = {}
    unmapped_columns: List[str] = []
    preview: List[Dict[str, Any]] = []
    row_count: int = 0


class ImportRequest(BaseModel):
    """Request to import file after preview."""
    tenant_id: UUID = Field(..., description="Tenant ID")
    book_id: UUID = Field(..., description="Target book for positions/trades")
    file_type: str = Field(..., description="'positions' or 'trades'")
    mapping: Dict[str, str] = Field(..., description="Column mapping to use")
    # File data is stored server-side after preview, referenced by upload_id
    upload_id: Optional[UUID] = Field(None, description="Upload ID from preview step")


class ImportResponse(BaseModel):
    """Response from import operation."""
    success: bool
    upload_id: UUID
    records_total: int
    records_processed: int
    records_failed: int
    errors: Optional[List[Dict[str, Any]]] = None
    message: str


class UploadCreate(BaseModel):
    """Model for creating upload record."""
    tenant_id: UUID
    uploaded_by: UUID
    file_name: str
    file_type: UploadFileType
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    storage_path: str
    target_book_id: Optional[UUID] = None


class UploadResponse(BaseModel):
    """Upload response model."""
    id: UUID
    tenant_id: UUID
    uploaded_by: UUID
    file_name: str
    file_type: UploadFileType
    file_size_bytes: Optional[int] = None
    status: UploadStatus
    target_book_id: Optional[UUID] = None
    records_total: Optional[int] = None
    records_processed: Optional[int] = None
    records_failed: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UploadList(BaseModel):
    """Paginated list of uploads."""
    items: List[UploadResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1
