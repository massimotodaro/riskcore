# RISKCORE Upload API Endpoints
# On-premises PostgreSQL - NO CLOUD STORAGE
# Files processed locally, data stored in local database only

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, status
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, Dict, Any
import logging
import tempfile
import os

from ..database import get_db_connection
from ..models.upload import (
    FilePreviewResponse,
    ImportRequest,
    ImportResponse,
    UploadResponse,
    UploadList,
)
from ..services.file_parser import FileParser
from ..services.upload_service import UploadService
from ..services.google_sheets import GoogleSheetsService

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Google Sheets Models
# =============================================================================

class GoogleSheetsPreviewRequest(BaseModel):
    """Request to preview a Google Sheet."""
    url: str = Field(..., description="Google Sheets URL or ID")
    sheet_name: Optional[str] = Field(None, description="Specific sheet/tab name")
    file_type: str = Field("positions", description="'positions' or 'trades'")


class GoogleSheetsImportRequest(BaseModel):
    """Request to import from a Google Sheet."""
    url: str = Field(..., description="Google Sheets URL or ID")
    sheet_name: Optional[str] = Field(None, description="Specific sheet/tab name")
    file_type: str = Field(..., description="'positions' or 'trades'")
    mapping: Dict[str, str] = Field(..., description="Column mapping")
    tenant_id: UUID = Field(..., description="Tenant ID")
    book_id: UUID = Field(..., description="Target book ID")
    uploaded_by: UUID = Field(..., description="User ID performing import")

# Temporary storage for parsed file data (keyed by upload_id)
# In production, this could be Redis or a database table
_parsed_data_cache: dict = {}


@router.post("/preview", response_model=FilePreviewResponse)
async def preview_file(
    file: UploadFile = File(..., description="CSV or Excel file to upload"),
    file_type: str = Form("positions", description="'positions' or 'trades'"),
):
    """
    Upload a file and get preview with auto-detected column mapping.

    **Supported formats:**
    - CSV (.csv)
    - Excel (.xlsx, .xls)

    **Returns:**
    - Column names from file
    - Auto-detected column mapping
    - First 10 rows as preview
    - Total row count

    Use the returned mapping in the /import endpoint to complete the import.
    """
    if file_type not in ["positions", "trades"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_type must be 'positions' or 'trades'",
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    # Parse file
    parser = FileParser()
    result = parser.parse_file(content, file.filename or "upload.csv", file_type)

    if not result["success"]:
        return FilePreviewResponse(
            success=False,
            error=result["error"],
            filename=file.filename or "unknown",
            file_type=file_type,
            columns=[],
            mapping={},
            unmapped_columns=[],
            preview=[],
            row_count=0,
        )

    # Store parsed data temporarily for import step
    # In production, store in database or Redis with expiration
    import uuid
    temp_id = str(uuid.uuid4())
    _parsed_data_cache[temp_id] = {
        "data": result["data"],
        "filename": file.filename,
        "file_type": file_type,
        "file_size": len(content),
    }

    return FilePreviewResponse(
        success=True,
        error=None,
        filename=file.filename or "unknown",
        file_type=file_type,
        columns=result["columns"],
        mapping=result["mapping"],
        unmapped_columns=result.get("unmapped_columns", []),
        preview=result["preview"],
        row_count=result["row_count"],
    )


@router.post("/import", response_model=ImportResponse)
def import_file(
    tenant_id: UUID = Form(..., description="Tenant ID"),
    book_id: UUID = Form(..., description="Target book ID"),
    file_type: str = Form(..., description="'positions' or 'trades'"),
    mapping: str = Form(..., description="JSON column mapping"),
    file: UploadFile = File(..., description="CSV or Excel file"),
    uploaded_by: UUID = Form(..., description="User ID performing upload"),
):
    """
    Import a file directly (parse + import in one step).

    **Parameters:**
    - **tenant_id**: Tenant UUID
    - **book_id**: Target book/portfolio UUID
    - **file_type**: 'positions' or 'trades'
    - **mapping**: JSON string of column mapping (from preview or manual)
    - **file**: The file to import
    - **uploaded_by**: User UUID performing the upload

    **Example mapping:**
    ```json
    {
        "ticker": "symbol",
        "quantity": "qty",
        "price": "price",
        "direction": "side"
    }
    ```

    **Returns:**
    - Import results with counts
    - List of errors (if any)
    """
    import json

    # Parse mapping JSON
    try:
        column_mapping = json.loads(mapping)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mapping JSON",
        )

    if file_type not in ["positions", "trades"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_type must be 'positions' or 'trades'",
        )

    # Read and parse file
    try:
        import asyncio
        content = asyncio.get_event_loop().run_until_complete(file.read())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}",
        )

    parser = FileParser()
    result = parser.parse_file(content, file.filename or "upload.csv", file_type)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    # Determine file type for database
    extension = "." + (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else ".csv"
    if file_type == "positions":
        db_file_type = "positions_xlsx" if extension in [".xlsx", ".xls"] else "positions_csv"
    else:
        db_file_type = "trades_xlsx" if extension in [".xlsx", ".xls"] else "trades_csv"

    try:
        with get_db_connection() as conn:
            service = UploadService(conn)

            # Create upload record
            upload = service.create_upload(
                tenant_id=tenant_id,
                uploaded_by=uploaded_by,
                file_name=file.filename or "upload",
                file_type=db_file_type,
                file_size_bytes=len(content),
                mime_type=file.content_type,
                storage_path=f"uploads/{tenant_id}/{file.filename}",
                target_book_id=book_id,
            )

            upload_id = UUID(str(upload["id"]))

            # Process import
            if file_type == "positions":
                import_result = service.process_positions_import(
                    upload_id=upload_id,
                    data=result["data"],
                    mapping=column_mapping,
                    tenant_id=tenant_id,
                    book_id=book_id,
                )
            else:
                import_result = service.process_trades_import(
                    upload_id=upload_id,
                    data=result["data"],
                    mapping=column_mapping,
                    tenant_id=tenant_id,
                    book_id=book_id,
                )

            return ImportResponse(
                success=import_result["success"],
                upload_id=upload_id,
                records_total=import_result["records_total"],
                records_processed=import_result["records_processed"],
                records_failed=import_result["records_failed"],
                errors=import_result.get("errors"),
                message=import_result["message"],
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import file: {str(e)}",
        )


@router.get("/", response_model=UploadList)
def list_uploads(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """
    List upload records with optional filtering.

    - **tenant_id**: Filter by tenant
    - **status**: Filter by status (pending, processing, completed, failed, cancelled)
    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (max 100)
    """
    try:
        with get_db_connection() as conn:
            service = UploadService(conn)
            result = service.list_uploads(
                tenant_id=tenant_id,
                status=status,
                page=page,
                page_size=page_size,
            )

            return UploadList(
                items=[UploadResponse(**item) for item in result["items"]],
                total=result["total"],
                page=result["page"],
                page_size=result["page_size"],
                total_pages=result["total_pages"],
            )
    except Exception as e:
        logger.error(f"Error listing uploads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list uploads: {str(e)}",
        )


@router.get("/{upload_id}", response_model=UploadResponse)
def get_upload(
    upload_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID for RLS"),
):
    """
    Get upload record by ID.

    - **upload_id**: UUID of the upload
    - **tenant_id**: Optional tenant ID for row-level security
    """
    try:
        with get_db_connection() as conn:
            service = UploadService(conn)
            upload = service.get_upload(upload_id, tenant_id)

            if not upload:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Upload {upload_id} not found",
                )

            return UploadResponse(**upload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting upload {upload_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upload: {str(e)}",
        )


@router.post("/{upload_id}/cancel")
def cancel_upload(
    upload_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID for RLS"),
):
    """
    Cancel a pending or processing upload.

    Only uploads with status 'pending' or 'processing' can be cancelled.
    """
    try:
        with get_db_connection() as conn:
            service = UploadService(conn)

            # Get current upload
            upload = service.get_upload(upload_id, tenant_id)
            if not upload:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Upload {upload_id} not found",
                )

            if upload["status"] not in ["pending", "processing"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot cancel upload with status '{upload['status']}'",
                )

            # Update status
            result = service.update_upload_status(upload_id, "cancelled")

            return {"message": "Upload cancelled", "upload_id": str(upload_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling upload {upload_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel upload: {str(e)}",
        )


# =============================================================================
# Google Sheets Endpoints
# =============================================================================

@router.post("/google-sheets/preview", response_model=FilePreviewResponse)
def preview_google_sheet(request: GoogleSheetsPreviewRequest):
    """
    Preview data from a public Google Sheet.

    **Requirements:**
    - Sheet must be shared as "Anyone with the link can view"
    - Works with any Google Sheets URL format

    **Parameters:**
    - **url**: Google Sheets URL (e.g., https://docs.google.com/spreadsheets/d/{id}/edit)
    - **sheet_name**: Optional specific sheet/tab name (defaults to first sheet)
    - **file_type**: 'positions' or 'trades'

    **Returns:**
    - Column names from sheet
    - Auto-detected column mapping
    - First 10 rows as preview
    - Total row count

    **Example URL formats:**
    - `https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit`
    - `https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=123`
    """
    if request.file_type not in ["positions", "trades"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_type must be 'positions' or 'trades'",
        )

    # Fetch sheet data
    sheets_service = GoogleSheetsService()
    result = sheets_service.fetch_sheet_data(request.url, request.sheet_name)

    if not result["success"]:
        return FilePreviewResponse(
            success=False,
            error=result["error"],
            filename=f"google-sheet-{result.get('sheet_id', 'unknown')}",
            file_type=request.file_type,
            columns=[],
            mapping={},
            unmapped_columns=[],
            preview=[],
            row_count=0,
        )

    # Auto-detect column mapping
    parser = FileParser()
    columns = result["columns"]

    # Clean column names for mapping
    cleaned_columns = [parser._clean_column_name(col) for col in columns]
    mapping = parser._auto_detect_columns(cleaned_columns, request.file_type)

    # Create preview (first 10 rows)
    preview = result["data"][:10]

    # Store parsed data for import step
    import uuid
    temp_id = str(uuid.uuid4())
    _parsed_data_cache[temp_id] = {
        "data": result["data"],
        "url": request.url,
        "sheet_name": request.sheet_name,
        "file_type": request.file_type,
    }

    return FilePreviewResponse(
        success=True,
        error=None,
        filename=f"google-sheet-{result.get('sheet_id', 'unknown')}",
        file_type=request.file_type,
        columns=columns,
        mapping=mapping,
        unmapped_columns=[c for c in cleaned_columns if c not in mapping.values()],
        preview=preview,
        row_count=result["row_count"],
    )


@router.post("/google-sheets/import", response_model=ImportResponse)
def import_google_sheet(request: GoogleSheetsImportRequest):
    """
    Import positions or trades from a public Google Sheet.

    **Requirements:**
    - Sheet must be shared as "Anyone with the link can view"

    **Parameters:**
    - **url**: Google Sheets URL
    - **sheet_name**: Optional specific sheet/tab name
    - **file_type**: 'positions' or 'trades'
    - **mapping**: Column mapping JSON (from preview or manual)
    - **tenant_id**: Tenant UUID
    - **book_id**: Target book/portfolio UUID
    - **uploaded_by**: User UUID performing the import

    **Example mapping:**
    ```json
    {
        "ticker": "symbol",
        "quantity": "qty",
        "price": "price",
        "direction": "side"
    }
    ```

    **Returns:**
    - Import results with counts
    - List of errors (if any)
    """
    if request.file_type not in ["positions", "trades"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_type must be 'positions' or 'trades'",
        )

    # Fetch sheet data
    sheets_service = GoogleSheetsService()
    result = sheets_service.fetch_sheet_data(request.url, request.sheet_name)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    # Clean column names in data to match mapping
    parser = FileParser()
    cleaned_data = []
    for row in result["data"]:
        cleaned_row = {parser._clean_column_name(k): v for k, v in row.items()}
        cleaned_data.append(cleaned_row)

    try:
        with get_db_connection() as conn:
            service = UploadService(conn)

            # Create upload record
            upload = service.create_upload(
                tenant_id=request.tenant_id,
                uploaded_by=request.uploaded_by,
                file_name=f"google-sheet-{result.get('sheet_id', 'import')}",
                file_type=f"{request.file_type}_google_sheets",
                file_size_bytes=None,
                mime_type="application/vnd.google-apps.spreadsheet",
                storage_path=request.url,
                target_book_id=request.book_id,
            )

            upload_id = UUID(str(upload["id"]))

            # Process import
            if request.file_type == "positions":
                import_result = service.process_positions_import(
                    upload_id=upload_id,
                    data=cleaned_data,
                    mapping=request.mapping,
                    tenant_id=request.tenant_id,
                    book_id=request.book_id,
                )
            else:
                import_result = service.process_trades_import(
                    upload_id=upload_id,
                    data=cleaned_data,
                    mapping=request.mapping,
                    tenant_id=request.tenant_id,
                    book_id=request.book_id,
                )

            return ImportResponse(
                success=import_result["success"],
                upload_id=upload_id,
                records_total=import_result["records_total"],
                records_processed=import_result["records_processed"],
                records_failed=import_result["records_failed"],
                errors=import_result.get("errors"),
                message=import_result["message"],
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing Google Sheet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import Google Sheet: {str(e)}",
        )


@router.get("/google-sheets/validate")
def validate_google_sheet_url(
    url: str = Query(..., description="Google Sheets URL to validate"),
):
    """
    Validate a Google Sheets URL and check if it's accessible.

    **Parameters:**
    - **url**: Google Sheets URL to validate

    **Returns:**
    - Whether the URL is valid
    - Whether the sheet is accessible (publicly shared)
    - Extracted sheet ID
    """
    sheets_service = GoogleSheetsService()

    try:
        sheet_id = sheets_service.extract_sheet_id(url)
    except ValueError as e:
        return {
            "valid_url": False,
            "accessible": False,
            "sheet_id": None,
            "error": str(e),
        }

    # Try to fetch the sheet
    result = sheets_service.fetch_sheet_data(url)

    return {
        "valid_url": True,
        "accessible": result["success"],
        "sheet_id": sheet_id,
        "row_count": result.get("row_count", 0),
        "columns": result.get("columns", []),
        "error": result.get("error"),
    }
