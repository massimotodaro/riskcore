# RISKCORE FIX Protocol API Endpoints
# Parse FIX messages and import as positions/trades
# On-premises PostgreSQL - NO CLOUD STORAGE

from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import date
import logging

from ..database import get_db_connection
from ..services.fix_parser import FIXParser, FIXMsgType
from ..services.position_service import PositionService
from ..services.trade_service import TradeService

logger = logging.getLogger(__name__)
router = APIRouter()


class FIXMessageRequest(BaseModel):
    """Request to parse a single FIX message."""

    message: str = Field(..., description="Raw FIX message string")
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID for import")
    book_id: Optional[UUID] = Field(None, description="Book ID for import")
    import_data: bool = Field(False, description="Whether to import parsed data")


class FIXBatchRequest(BaseModel):
    """Request to parse multiple FIX messages."""

    messages: List[str] = Field(..., description="List of raw FIX message strings")
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID for import")
    book_id: Optional[UUID] = Field(None, description="Book ID for import")
    import_data: bool = Field(False, description="Whether to import parsed data")


class FIXParseResponse(BaseModel):
    """Response from parsing a FIX message."""

    success: bool
    msg_type: Optional[str] = None
    supported: bool = False
    data_type: Optional[str] = None  # "trade" or "position"
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    imported: bool = False
    import_id: Optional[UUID] = None


class FIXBatchResponse(BaseModel):
    """Response from parsing multiple FIX messages."""

    total: int
    parsed: int
    imported: int
    failed: int
    results: List[FIXParseResponse]


@router.post("/parse", response_model=FIXParseResponse)
def parse_fix_message(request: FIXMessageRequest):
    """
    Parse a single FIX message.

    **Supported message types:**
    - ExecutionReport (35=8): Extracts trade data
    - PositionReport (35=AP): Extracts position data

    **Parameters:**
    - **message**: Raw FIX message string (pipe-delimited or SOH-delimited)
    - **tenant_id**: Required if import_data=True
    - **book_id**: Required if import_data=True
    - **import_data**: Set to true to import parsed data to database

    **Returns:**
    - Parsed message data with trade or position fields
    - If import_data=True, includes import_id of created record
    """
    # Normalize delimiter (support both pipe | and SOH \x01)
    raw_message = request.message.replace("|", "\x01")
    if not raw_message.endswith("\x01"):
        raw_message += "\x01"

    parser = FIXParser()
    result = parser.parse_message(raw_message.encode("utf-8"))

    if not result["success"]:
        return FIXParseResponse(
            success=False,
            error=result.get("error"),
        )

    response = FIXParseResponse(
        success=True,
        msg_type=result.get("msg_type"),
        supported=result.get("supported", False),
        data_type=result.get("data_type"),
        data=result.get("data"),
    )

    # Import data if requested
    if request.import_data and result.get("supported") and result.get("data"):
        if not request.tenant_id or not request.book_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tenant_id and book_id required for import",
            )

        try:
            import_id = _import_fix_data(
                result["data_type"],
                result["data"],
                request.tenant_id,
                request.book_id,
            )
            response.imported = True
            response.import_id = import_id
        except Exception as e:
            logger.error(f"Error importing FIX data: {e}")
            response.error = f"Import failed: {str(e)}"

    return response


@router.post("/parse/batch", response_model=FIXBatchResponse)
def parse_fix_messages(request: FIXBatchRequest):
    """
    Parse multiple FIX messages in batch.

    **Parameters:**
    - **messages**: List of raw FIX message strings
    - **tenant_id**: Required if import_data=True
    - **book_id**: Required if import_data=True
    - **import_data**: Set to true to import all parsed data

    **Returns:**
    - Summary of parsing results
    - Individual results for each message
    """
    if request.import_data and (not request.tenant_id or not request.book_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id and book_id required for import",
        )

    parser = FIXParser()
    results = []
    parsed_count = 0
    imported_count = 0
    failed_count = 0

    for msg_str in request.messages:
        # Normalize delimiter
        raw_message = msg_str.replace("|", "\x01")
        if not raw_message.endswith("\x01"):
            raw_message += "\x01"

        result = parser.parse_message(raw_message.encode("utf-8"))

        if not result["success"]:
            failed_count += 1
            results.append(FIXParseResponse(
                success=False,
                error=result.get("error"),
            ))
            continue

        parsed_count += 1
        response = FIXParseResponse(
            success=True,
            msg_type=result.get("msg_type"),
            supported=result.get("supported", False),
            data_type=result.get("data_type"),
            data=result.get("data"),
        )

        # Import if requested
        if request.import_data and result.get("supported") and result.get("data"):
            try:
                import_id = _import_fix_data(
                    result["data_type"],
                    result["data"],
                    request.tenant_id,
                    request.book_id,
                )
                response.imported = True
                response.import_id = import_id
                imported_count += 1
            except Exception as e:
                logger.error(f"Error importing FIX data: {e}")
                response.error = f"Import failed: {str(e)}"

        results.append(response)

    return FIXBatchResponse(
        total=len(request.messages),
        parsed=parsed_count,
        imported=imported_count,
        failed=failed_count,
        results=results,
    )


@router.post("/sample/execution-report")
def get_sample_execution_report(
    symbol: str = "AAPL",
    side: str = "1",
    quantity: int = 100,
    price: float = 150.50,
):
    """
    Generate a sample ExecutionReport FIX message for testing.

    **Parameters:**
    - **symbol**: Security symbol (default: AAPL)
    - **side**: FIX side (1=Buy, 2=Sell, 5=Short)
    - **quantity**: Order quantity
    - **price**: Execution price

    **Returns:**
    - Sample FIX message in pipe-delimited format
    """
    raw_bytes = FIXParser.create_sample_execution_report(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
    )

    # Convert SOH to pipe for readability
    readable = raw_bytes.decode("utf-8").replace("\x01", "|")

    return {
        "message": readable,
        "msg_type": "8",
        "msg_type_name": "ExecutionReport",
        "description": "Sample filled execution report",
    }


@router.post("/sample/position-report")
def get_sample_position_report(
    symbol: str = "AAPL",
    long_qty: int = 1000,
    short_qty: int = 0,
    price: float = 150.50,
):
    """
    Generate a sample PositionReport FIX message for testing.

    **Parameters:**
    - **symbol**: Security symbol (default: AAPL)
    - **long_qty**: Long quantity
    - **short_qty**: Short quantity
    - **price**: Settlement price

    **Returns:**
    - Sample FIX message in pipe-delimited format
    """
    raw_bytes = FIXParser.create_sample_position_report(
        symbol=symbol,
        long_qty=long_qty,
        short_qty=short_qty,
        price=price,
    )

    # Convert SOH to pipe for readability
    readable = raw_bytes.decode("utf-8").replace("\x01", "|")

    return {
        "message": readable,
        "msg_type": "AP",
        "msg_type_name": "PositionReport",
        "description": "Sample position report",
    }


def _import_fix_data(
    data_type: str,
    data: Dict[str, Any],
    tenant_id: UUID,
    book_id: UUID,
) -> UUID:
    """
    Import parsed FIX data to database.

    Returns the ID of the created record.
    """
    with get_db_connection() as conn:
        if data_type == "trade":
            service = TradeService(conn)

            # Resolve security ID
            security_id = service.resolve_security_id(
                ticker=data.get("ticker"),
                cusip=data.get("cusip"),
                isin=data.get("isin"),
                sedol=data.get("sedol"),
            )

            # Map side
            side = data.get("side", "buy")

            # Parse trade date
            trade_date = data.get("trade_date")
            if isinstance(trade_date, str):
                trade_date = date.fromisoformat(trade_date)
            elif trade_date is None:
                trade_date = date.today()

            result = service.create_trade(
                tenant_id=tenant_id,
                book_id=book_id,
                security_id=security_id,
                side=side,
                quantity=data.get("quantity"),
                price=data.get("price"),
                currency=data.get("currency", "USD"),
                trade_date=trade_date,
                source="fix_message",
                trade_id_external=data.get("trade_id_external"),
                order_id_external=data.get("order_id_external"),
                broker=data.get("broker"),
                counterparty=data.get("counterparty"),
            )

            return UUID(str(result["id"]))

        elif data_type == "position":
            service = PositionService(conn)

            # Resolve security ID
            security_id = service.resolve_security_id(
                ticker=data.get("ticker"),
                cusip=data.get("cusip"),
                isin=data.get("isin"),
                sedol=data.get("sedol"),
            )

            from datetime import datetime
            result = service.create_position(
                tenant_id=tenant_id,
                book_id=book_id,
                security_id=security_id,
                quantity=data.get("quantity"),
                direction=data.get("direction", "long"),
                source="fix_message",
                as_of_timestamp=datetime.utcnow(),
                price=data.get("price"),
                local_currency=data.get("currency", "USD"),
                base_currency=data.get("currency", "USD"),
            )

            return UUID(str(result["id"]))

        else:
            raise ValueError(f"Unknown data type: {data_type}")
