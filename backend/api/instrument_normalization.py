"""
Instrument Normalization API Endpoints

Provides REST API for normalizing instrument names to canonical forms
and managing alias mappings.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..database import get_db_connection
from ..services.instrument_normalization import (
    InstrumentNormalizationService,
    NormalizationResult,
)
from ..services.composition_service import CompositionService

router = APIRouter(prefix="/instrument", tags=["Instrument Normalization"])


# =============================================================================
# Request/Response Models
# =============================================================================

class NormalizeRequest(BaseModel):
    """Request to normalize a single instrument name."""
    value: str = Field(..., description="Instrument name to normalize", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {"value": "CDS 5Y"}
        }


class NormalizeBatchRequest(BaseModel):
    """Request to normalize multiple instrument names."""
    values: List[str] = Field(
        ...,
        description="List of instrument names to normalize",
        min_items=1,
        max_items=1000
    )

    class Config:
        json_schema_extra = {
            "example": {"values": ["CDS 5Y", "Interest Rate Swap", "UST 10Y"]}
        }


class NormalizeResponse(BaseModel):
    """Response from instrument normalization."""
    success: bool = Field(..., description="Whether normalization succeeded")
    input_value: str = Field(..., description="Original input value")
    instrument_type_code: Optional[str] = Field(None, description="Canonical type code (e.g., 'CDS')")
    canonical_name: Optional[str] = Field(None, description="Full canonical name")
    asset_class: Optional[str] = Field(None, description="Asset class for database")
    riskpod: Optional[str] = Field(None, description="RiskPod assignment")
    extracted_tenor: Optional[str] = Field(None, description="Extracted tenor (e.g., '5Y')")
    confidence: float = Field(..., description="Match confidence (0.0 to 1.0)")
    match_method: str = Field(..., description="Method used to match")
    matched_alias: Optional[str] = Field(None, description="Alias that matched")
    is_cached: bool = Field(default=False, description="Whether result came from cache")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "input_value": "CDS 5Y",
                "instrument_type_code": "CDS",
                "canonical_name": "Credit Default Swap",
                "asset_class": "cds",
                "riskpod": "credit",
                "extracted_tenor": "5Y",
                "confidence": 1.0,
                "match_method": "exact",
                "matched_alias": "CDS 5Y",
                "is_cached": False
            }
        }


class InstrumentTypeResponse(BaseModel):
    """Canonical instrument type."""
    id: str
    code: str
    canonical_name: str
    asset_class: str
    riskpod: str
    has_tenor: bool
    default_tenor: Optional[str]


class AliasResponse(BaseModel):
    """Alias mapping."""
    id: str
    alias: str
    match_type: str
    priority: int
    instrument_type_code: str
    canonical_name: str
    asset_class: str
    riskpod: str
    is_global: bool


class CreateAliasRequest(BaseModel):
    """Request to create a new alias."""
    instrument_type_code: str = Field(..., description="Type code to map to (e.g., 'CDS')")
    alias: str = Field(..., description="Alias text", min_length=1)
    match_type: str = Field(default="exact", description="Match type: exact, prefix, contains, regex")
    priority: int = Field(default=100, description="Priority (higher = preferred)", ge=1, le=1000)
    tenant_specific: bool = Field(default=False, description="If true, alias is tenant-specific")

    class Config:
        json_schema_extra = {
            "example": {
                "instrument_type_code": "CDS",
                "alias": "Credit Protection 5Y",
                "match_type": "exact",
                "priority": 90,
                "tenant_specific": True
            }
        }


class UnmatchedResponse(BaseModel):
    """Unmatched instrument record."""
    id: str
    input_value: str
    occurrence_count: int
    status: str
    created_at: str
    updated_at: Optional[str]


class ResolveUnmatchedRequest(BaseModel):
    """Request to resolve an unmatched instrument."""
    instrument_type_code: str = Field(..., description="Type code to assign")
    create_alias: bool = Field(default=True, description="Create alias for future matching")
    notes: Optional[str] = Field(None, description="Resolution notes")


class DecomposeComponentInput(BaseModel):
    """Component for decomposition."""
    name: str = Field(..., description="Component name")
    type_code: str = Field(..., description="Instrument type code")
    allocation: float = Field(..., description="Allocation percentage", gt=0, le=100)


class DecomposeUnmatchedRequest(BaseModel):
    """Request to decompose an unmatched instrument into components."""
    name: str = Field(..., description="Composition name")
    components: List[DecomposeComponentInput] = Field(
        ...,
        description="Component breakdown",
        min_items=1
    )
    create_template: bool = Field(
        default=True,
        description="Save as template for future imports"
    )
    apply_to_existing: bool = Field(
        default=True,
        description="Apply to positions already imported with this name"
    )
    notes: Optional[str] = Field(None, description="Resolution notes")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ABC Structured Note",
                "components": [
                    {"name": "S&P Future", "type_code": "FUTURE", "allocation": 33.33},
                    {"name": "NVIDIA Put", "type_code": "EQO", "allocation": 33.33},
                    {"name": "NVIDIA Bond", "type_code": "CORPBOND", "allocation": 33.34}
                ],
                "create_template": True,
                "apply_to_existing": True,
                "notes": "Decomposed into equity and credit components"
            }
        }


# =============================================================================
# Normalization Endpoints
# =============================================================================

@router.post("/normalize", response_model=NormalizeResponse)
def normalize_instrument(
    request: NormalizeRequest,
    tenant_id: Optional[UUID] = Query(None, description="Tenant UUID for tenant-specific mappings"),
):
    """
    Normalize a single instrument name to canonical form.

    Matches the input against known aliases and returns the canonical
    instrument type, asset class, and RiskPod assignment.

    **Matching Priority:**
    1. Exact match (confidence: 1.0)
    2. Prefix match (confidence: 0.95)
    3. Fuzzy match (confidence: 0.85+)
    4. Pattern/regex match (confidence: 0.80)
    5. Unmatched (queued for review)

    **Examples:**
    - "CDS 5Y" → asset_class='cds', riskpod='credit', tenor='5Y'
    - "Interest Rate Swap" → asset_class='swap', riskpod='rates'
    - "UST 10Y" → asset_class='fixed_income', riskpod='rates', tenor='10Y'
    """
    with get_db_connection() as conn:
        service = InstrumentNormalizationService(conn, tenant_id)
        result = service.normalize(request.value)
        return NormalizeResponse(**result.to_dict())


@router.post("/normalize/batch", response_model=List[NormalizeResponse])
def normalize_instruments_batch(
    request: NormalizeBatchRequest,
    tenant_id: Optional[UUID] = Query(None, description="Tenant UUID"),
):
    """
    Normalize multiple instrument names in batch.

    More efficient than calling /normalize multiple times.
    Maximum 1000 values per request.
    """
    with get_db_connection() as conn:
        service = InstrumentNormalizationService(conn, tenant_id)
        results = service.normalize_batch(request.values)
        return [NormalizeResponse(**r.to_dict()) for r in results]


# =============================================================================
# Instrument Type Endpoints
# =============================================================================

@router.get("/types", response_model=List[InstrumentTypeResponse])
def list_instrument_types(
    tenant_id: Optional[UUID] = Query(None, description="Tenant UUID"),
):
    """
    List all canonical instrument types.

    Returns the master list of instrument types with their codes,
    canonical names, asset classes, and RiskPod assignments.
    """
    with get_db_connection() as conn:
        service = InstrumentNormalizationService(conn, tenant_id)
        types = service.get_instrument_types()
        return [
            InstrumentTypeResponse(
                id=str(t['id']),
                code=t['code'],
                canonical_name=t['canonical_name'],
                asset_class=t['asset_class'],
                riskpod=t['riskpod'],
                has_tenor=t.get('has_tenor', False),
                default_tenor=t.get('default_tenor'),
            )
            for t in types
        ]


@router.get("/types/{code}")
def get_instrument_type(
    code: str,
    tenant_id: Optional[UUID] = Query(None),
):
    """Get a specific instrument type by code."""
    with get_db_connection() as conn:
        service = InstrumentNormalizationService(conn, tenant_id)
        types = service.get_instrument_types()
        for t in types:
            if t['code'] == code.upper():
                return InstrumentTypeResponse(
                    id=str(t['id']),
                    code=t['code'],
                    canonical_name=t['canonical_name'],
                    asset_class=t['asset_class'],
                    riskpod=t['riskpod'],
                    has_tenor=t.get('has_tenor', False),
                    default_tenor=t.get('default_tenor'),
                )
        raise HTTPException(status_code=404, detail=f"Instrument type '{code}' not found")


# =============================================================================
# Alias Endpoints
# =============================================================================

@router.get("/aliases", response_model=List[AliasResponse])
def list_aliases(
    instrument_type_code: Optional[str] = Query(None, description="Filter by type code"),
    include_global: bool = Query(True, description="Include global aliases"),
    tenant_id: Optional[UUID] = Query(None),
):
    """
    List alias mappings.

    Can be filtered by instrument type code. By default includes
    both global and tenant-specific aliases.
    """
    with get_db_connection() as conn:
        service = InstrumentNormalizationService(conn, tenant_id)
        aliases = service.get_aliases(
            instrument_type_code=instrument_type_code.upper() if instrument_type_code else None,
            include_global=include_global,
        )
        return [AliasResponse(**a) for a in aliases]


@router.post("/aliases", status_code=201)
def create_alias(
    request: CreateAliasRequest,
    tenant_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None, description="User creating the alias"),
):
    """
    Create a new alias mapping.

    Maps a client-specific instrument name to a canonical type.
    Can be global (available to all tenants) or tenant-specific.
    """
    with get_db_connection() as conn:
        service = InstrumentNormalizationService(conn, tenant_id)
        success = service.add_alias(
            instrument_type_code=request.instrument_type_code.upper(),
            alias=request.alias,
            match_type=request.match_type,
            priority=request.priority,
            tenant_specific=request.tenant_specific,
            created_by=str(user_id) if user_id else None,
        )
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create alias. Check that instrument type '{request.instrument_type_code}' exists."
            )
        return {"status": "created", "alias": request.alias}


# =============================================================================
# Unmatched Queue Endpoints
# =============================================================================

@router.get("/unmatched", response_model=List[UnmatchedResponse])
def list_unmatched(
    status: str = Query("pending", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    tenant_id: Optional[UUID] = Query(None),
):
    """
    List unmatched instruments awaiting review.

    Instruments that couldn't be normalized are queued here for
    manual mapping by administrators.

    **Status values:**
    - pending: Awaiting review
    - mapped: Resolved with alias created
    - ignored: Marked as not applicable
    - escalated: Escalated for further review
    """
    with get_db_connection() as conn:
        service = InstrumentNormalizationService(conn, tenant_id)
        offset = (page - 1) * page_size
        records = service.get_unmatched(
            status=status,
            limit=page_size,
            offset=offset,
        )
        return [
            UnmatchedResponse(
                id=str(r['id']),
                input_value=r['input_value'],
                occurrence_count=r['occurrence_count'],
                status=r['status'],
                created_at=r['created_at'].isoformat() if r['created_at'] else '',
                updated_at=r['updated_at'].isoformat() if r.get('updated_at') else None,
            )
            for r in records
        ]


@router.post("/unmatched/{unmatched_id}/resolve")
def resolve_unmatched(
    unmatched_id: UUID,
    request: ResolveUnmatchedRequest,
    tenant_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None, description="User resolving"),
):
    """
    Resolve an unmatched instrument by assigning a type.

    Optionally creates an alias mapping for future automatic matching.
    """
    with get_db_connection() as conn:
        service = InstrumentNormalizationService(conn, tenant_id)
        success = service.resolve_unmatched(
            unmatched_id=str(unmatched_id),
            instrument_type_code=request.instrument_type_code.upper(),
            create_alias=request.create_alias,
            reviewed_by=str(user_id) if user_id else None,
            notes=request.notes,
        )
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to resolve unmatched instrument"
            )
        return {"status": "resolved", "id": str(unmatched_id)}


@router.post("/unmatched/{unmatched_id}/ignore")
def ignore_unmatched(
    unmatched_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    notes: Optional[str] = Query(None),
):
    """Mark an unmatched instrument as ignored (not applicable)."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE unmatched_instruments
                SET status = 'ignored',
                    reviewed_by = %s,
                    reviewed_at = NOW(),
                    resolution_notes = %s
                WHERE id = %s
            """, (str(user_id) if user_id else None, notes, str(unmatched_id)))
            conn.commit()
            return {"status": "ignored", "id": str(unmatched_id)}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/unmatched/{unmatched_id}/escalate")
def escalate_unmatched(
    unmatched_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    notes: Optional[str] = Query(None),
):
    """Escalate an unmatched instrument for further review."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE unmatched_instruments
                SET status = 'escalated',
                    reviewed_by = %s,
                    reviewed_at = NOW(),
                    resolution_notes = %s
                WHERE id = %s
            """, (str(user_id) if user_id else None, notes, str(unmatched_id)))
            conn.commit()
            return {"status": "escalated", "id": str(unmatched_id)}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/unmatched/{unmatched_id}/decompose")
def decompose_unmatched(
    unmatched_id: UUID,
    request: DecomposeUnmatchedRequest,
    tenant_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
):
    """
    Decompose an unmatched instrument into components.

    Creates a composition template from a structured note or complex
    instrument, allowing risk attribution across RiskPods while keeping
    the position in the "Other" RiskPod.

    **Use Case:**
    When a client uploads "ABC Structured Note", the instrument doesn't
    match any known type. Instead of mapping it to a single type, the
    user can decompose it:

    - 33.33% → S&P 500 Future (Equity)
    - 33.33% → NVIDIA Put (Equity)
    - 33.34% → NVIDIA Bond (Credit)

    **Options:**
    - `create_template`: Save as template for automatic matching on future imports
    - `apply_to_existing`: Apply composition to positions already imported with this name
    """
    with get_db_connection() as conn:
        from psycopg2.extras import RealDictCursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Get the unmatched record
            cur.execute("""
                SELECT id, input_value, status
                FROM unmatched_instruments
                WHERE id = %s
            """, (str(unmatched_id),))
            unmatched = cur.fetchone()

            if not unmatched:
                raise HTTPException(status_code=404, detail="Unmatched instrument not found")

            if unmatched['status'] != 'pending':
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot decompose: status is '{unmatched['status']}', expected 'pending'"
                )

            # Validate total allocation
            total_allocation = sum(c.allocation for c in request.components)
            if abs(total_allocation - 100.0) > 0.01:
                raise HTTPException(
                    status_code=400,
                    detail=f"Component allocations must sum to 100%, got {total_allocation:.2f}%"
                )

            # Create the composition
            composition_service = CompositionService(conn, str(tenant_id) if tenant_id else None)

            components = [
                {
                    "name": c.name,
                    "type_code": c.type_code,
                    "allocation": c.allocation,
                    "allocation_type": "percentage",
                }
                for c in request.components
            ]

            composition_id = composition_service.create_composition(
                name=request.name,
                components=components,
                description=f"Decomposed from unmatched: {unmatched['input_value']}",
                is_template=request.create_template,
                created_by=str(user_id) if user_id else None,
            )

            # Update unmatched record
            cur.execute("""
                UPDATE unmatched_instruments
                SET status = 'decomposed',
                    reviewed_by = %s,
                    reviewed_at = NOW(),
                    resolution_notes = %s,
                    resolved_composition_id = %s
                WHERE id = %s
            """, (
                str(user_id) if user_id else None,
                request.notes or f"Decomposed into {len(request.components)} components",
                composition_id,
                str(unmatched_id),
            ))

            # Apply to existing positions if requested
            positions_updated = 0
            if request.apply_to_existing:
                positions_updated = composition_service.apply_to_positions_by_security_name(
                    composition_id=composition_id,
                    security_name_pattern=unmatched['input_value'],
                    applied_by=str(user_id) if user_id else None,
                )

            conn.commit()

            return {
                "status": "decomposed",
                "unmatched_id": str(unmatched_id),
                "composition_id": composition_id,
                "component_count": len(request.components),
                "positions_updated": positions_updated,
            }

        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Cache Management
# =============================================================================

@router.delete("/cache")
def clear_cache(
    tenant_id: Optional[UUID] = Query(None),
):
    """
    Clear expired entries from the normalization cache.

    Called automatically by maintenance job, but can be triggered manually.
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT cleanup_normalization_cache()")
            result = cur.fetchone()
            conn.commit()
            deleted = result[0] if result else 0
            return {"status": "cleared", "deleted_count": deleted}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
