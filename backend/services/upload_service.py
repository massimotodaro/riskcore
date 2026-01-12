# RISKCORE Upload Service
# Business logic for file uploads
# Uses psycopg2 for direct PostgreSQL access (on-premises)

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
import logging
import json

import psycopg2
from psycopg2.extras import RealDictCursor

from .file_parser import FileParser
from .position_service import PositionService
from .trade_service import TradeService

logger = logging.getLogger(__name__)


class UploadService:
    """
    Service for managing file uploads.

    Handles:
    - Upload record creation/tracking
    - File parsing and preview
    - Data import to positions/trades tables

    Uses psycopg2 for direct PostgreSQL access.
    All data stays on-premises - no cloud storage.
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn
        self.file_parser = FileParser()

    def create_upload(
        self,
        tenant_id: UUID,
        uploaded_by: UUID,
        file_name: str,
        file_type: str,
        file_size_bytes: Optional[int] = None,
        mime_type: Optional[str] = None,
        storage_path: str = "",
        target_book_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Create an upload record."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            INSERT INTO uploads (
                tenant_id, uploaded_by, file_name, file_type,
                file_size_bytes, mime_type, storage_path, target_book_id,
                status
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                'pending'
            )
            RETURNING *
        """, (
            str(tenant_id), str(uploaded_by), file_name, file_type,
            file_size_bytes, mime_type, storage_path,
            str(target_book_id) if target_book_id else None,
        ))

        result = cur.fetchone()
        self.conn.commit()
        return dict(result) if result else None

    def get_upload(
        self,
        upload_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get upload by ID."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if tenant_id:
            cur.execute("""
                SELECT * FROM uploads
                WHERE id = %s AND tenant_id = %s
            """, (str(upload_id), str(tenant_id)))
        else:
            cur.execute("""
                SELECT * FROM uploads WHERE id = %s
            """, (str(upload_id),))

        result = cur.fetchone()
        return dict(result) if result else None

    def update_upload_status(
        self,
        upload_id: UUID,
        status: str,
        records_total: Optional[int] = None,
        records_processed: Optional[int] = None,
        records_failed: Optional[int] = None,
        error_message: Optional[str] = None,
        processing_log: Optional[Dict] = None,
        validation_errors: Optional[List] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update upload status and processing results."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Build update parts
        updates = ["status = %s", "updated_at = NOW()"]
        params = [status]

        if status == "processing":
            updates.append("processing_started_at = NOW()")

        if status in ["completed", "failed"]:
            updates.append("processing_completed_at = NOW()")

        if records_total is not None:
            updates.append("records_total = %s")
            params.append(records_total)

        if records_processed is not None:
            updates.append("records_processed = %s")
            params.append(records_processed)

        if records_failed is not None:
            updates.append("records_failed = %s")
            params.append(records_failed)

        if error_message is not None:
            updates.append("error_message = %s")
            params.append(error_message)

        if processing_log is not None:
            updates.append("processing_log = %s")
            params.append(json.dumps(processing_log))

        if validation_errors is not None:
            updates.append("validation_errors = %s")
            params.append(json.dumps(validation_errors))

        params.append(str(upload_id))

        query = f"""
            UPDATE uploads
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING *
        """

        cur.execute(query, params)
        result = cur.fetchone()
        self.conn.commit()
        return dict(result) if result else None

    def list_uploads(
        self,
        tenant_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """List uploads with filters and pagination."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        conditions = []
        params = []

        if tenant_id:
            conditions.append("tenant_id = %s")
            params.append(str(tenant_id))

        if status:
            conditions.append("status = %s")
            params.append(status)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        cur.execute(f"SELECT COUNT(*) FROM uploads {where_clause}", params)
        total = cur.fetchone()["count"]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        offset = (page - 1) * page_size

        # Get data
        cur.execute(f"""
            SELECT * FROM uploads
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [page_size, offset])

        items = [dict(row) for row in cur.fetchall()]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def process_positions_import(
        self,
        upload_id: UUID,
        data: List[Dict[str, Any]],
        mapping: Dict[str, str],
        tenant_id: UUID,
        book_id: UUID,
    ) -> Dict[str, Any]:
        """
        Process positions import from parsed file data.

        Returns import results with counts and errors.
        """
        # Update status to processing
        self.update_upload_status(upload_id, "processing", records_total=len(data))

        # Transform rows
        valid_rows, error_rows = self.file_parser.transform_rows(
            data, mapping, "positions", str(tenant_id), str(book_id)
        )

        # Import valid rows
        position_service = PositionService(self.conn)
        imported = 0
        import_errors = []

        for i, row in enumerate(valid_rows):
            try:
                # Resolve security if needed
                security_id = row.get("security_id")
                if not security_id:
                    security_id = position_service.resolve_security_id(
                        ticker=row.get("ticker"),
                        cusip=row.get("cusip"),
                        isin=row.get("isin"),
                        sedol=row.get("sedol"),
                    )

                if not security_id:
                    import_errors.append({
                        "row_number": i + 1,
                        "error": "Could not resolve security identifier",
                        "data": row,
                    })
                    continue

                # Create position
                position_service.create_position(
                    tenant_id=tenant_id,
                    book_id=book_id,
                    security_id=security_id,
                    quantity=row.get("quantity"),
                    direction=row.get("direction", "long"),
                    source="file_upload",
                    as_of_timestamp=datetime.fromisoformat(row.get("as_of_timestamp", datetime.utcnow().isoformat())),
                    price=row.get("price"),
                    cost_basis=row.get("cost_basis"),
                    local_currency=row.get("currency", "USD"),
                    base_currency=row.get("currency", "USD"),
                )
                imported += 1

            except Exception as e:
                import_errors.append({
                    "row_number": i + 1,
                    "error": str(e),
                    "data": row,
                })

        # Combine all errors
        all_errors = error_rows + import_errors
        failed = len(all_errors)

        # Update upload record
        final_status = "completed" if failed == 0 else ("failed" if imported == 0 else "completed")
        self.update_upload_status(
            upload_id,
            final_status,
            records_processed=imported,
            records_failed=failed,
            validation_errors=all_errors[:100] if all_errors else None,  # Limit errors stored
        )

        return {
            "success": imported > 0,
            "upload_id": str(upload_id),
            "records_total": len(data),
            "records_processed": imported,
            "records_failed": failed,
            "errors": all_errors[:50] if all_errors else None,
            "message": f"Imported {imported} positions, {failed} failed",
        }

    def process_trades_import(
        self,
        upload_id: UUID,
        data: List[Dict[str, Any]],
        mapping: Dict[str, str],
        tenant_id: UUID,
        book_id: UUID,
    ) -> Dict[str, Any]:
        """
        Process trades import from parsed file data.

        Returns import results with counts and errors.
        """
        # Update status to processing
        self.update_upload_status(upload_id, "processing", records_total=len(data))

        # Transform rows
        valid_rows, error_rows = self.file_parser.transform_rows(
            data, mapping, "trades", str(tenant_id), str(book_id)
        )

        # Import valid rows
        trade_service = TradeService(self.conn)
        imported = 0
        import_errors = []

        for i, row in enumerate(valid_rows):
            try:
                # Resolve security if needed
                security_id = row.get("security_id")
                if not security_id:
                    security_id = trade_service.resolve_security_id(
                        ticker=row.get("ticker"),
                        cusip=row.get("cusip"),
                        isin=row.get("isin"),
                        sedol=row.get("sedol"),
                    )

                if not security_id:
                    import_errors.append({
                        "row_number": i + 1,
                        "error": "Could not resolve security identifier",
                        "data": row,
                    })
                    continue

                # Parse trade_date
                trade_date = row.get("trade_date")
                if isinstance(trade_date, str):
                    from datetime import date as date_type
                    trade_date = date_type.fromisoformat(trade_date)

                # Create trade
                trade_service.create_trade(
                    tenant_id=tenant_id,
                    book_id=book_id,
                    security_id=security_id,
                    side=row.get("side"),
                    quantity=row.get("quantity"),
                    price=row.get("price"),
                    currency=row.get("currency", "USD"),
                    trade_date=trade_date,
                    source="file_upload",
                    broker=row.get("broker"),
                    counterparty=row.get("counterparty"),
                    commission=row.get("commission"),
                    fees=row.get("fees"),
                    trade_id_external=row.get("trade_id"),
                )
                imported += 1

            except Exception as e:
                import_errors.append({
                    "row_number": i + 1,
                    "error": str(e),
                    "data": row,
                })

        # Combine all errors
        all_errors = error_rows + import_errors
        failed = len(all_errors)

        # Update upload record
        final_status = "completed" if failed == 0 else ("failed" if imported == 0 else "completed")
        self.update_upload_status(
            upload_id,
            final_status,
            records_processed=imported,
            records_failed=failed,
            validation_errors=all_errors[:100] if all_errors else None,
        )

        return {
            "success": imported > 0,
            "upload_id": str(upload_id),
            "records_total": len(data),
            "records_processed": imported,
            "records_failed": failed,
            "errors": all_errors[:50] if all_errors else None,
            "message": f"Imported {imported} trades, {failed} failed",
        }
