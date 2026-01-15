"""
Compositions API Endpoints

REST API for managing structured instrument compositions.
Used for pricing and risk attribution of structured notes and complex instruments.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from ..database import get_db_connection
from ..services.composition_service import CompositionService

router = APIRouter(prefix="/compositions", tags=["Compositions"])


# =============================================================================
# Request/Response Models
# =============================================================================

class ComponentInput(BaseModel):
    """Component input for creating/adding components."""
    name: str = Field(..., description="Component name", min_length=1, max_length=200)
    type_code: str = Field(..., description="Instrument type code (e.g., 'FUTURE', 'EQO', 'CORPBOND')")
    allocation: float = Field(..., description="Allocation value", gt=0)
    allocation_type: str = Field(
        default="percentage",
        description="Allocation type: 'percentage' or 'notional'"
    )
    security_id: Optional[str] = Field(None, description="Optional linked security UUID")
    delta: Optional[float] = Field(None, description="Delta Greek")
    gamma: Optional[float] = Field(None, description="Gamma Greek")
    vega: Optional[float] = Field(None, description="Vega Greek")
    theta: Optional[float] = Field(None, description="Theta Greek")
    rho: Optional[float] = Field(None, description="Rho Greek")
    duration: Optional[float] = Field(None, description="Duration")
    convexity: Optional[float] = Field(None, description="Convexity")
    dv01: Optional[float] = Field(None, description="DV01")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "S&P 500 Future Mar 2025",
                "type_code": "FUTURE",
                "allocation": 33.33,
                "allocation_type": "percentage"
            }
        }


class CreateCompositionRequest(BaseModel):
    """Request to create a new composition."""
    name: str = Field(..., description="Composition name", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Optional description")
    is_template: bool = Field(default=True, description="Save as reusable template")
    components: List[ComponentInput] = Field(..., description="List of components", min_items=1)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ABC Structured Note",
                "description": "Multi-asset structured note with equity and credit exposure",
                "is_template": True,
                "components": [
                    {"name": "S&P 500 Future Mar 2025", "type_code": "FUTURE", "allocation": 33.33},
                    {"name": "NVIDIA Put Strike 800", "type_code": "EQO", "allocation": 33.33},
                    {"name": "NVIDIA Bond 5.5% 2032", "type_code": "CORPBOND", "allocation": 33.34}
                ]
            }
        }


class UpdateCompositionRequest(BaseModel):
    """Request to update composition metadata."""
    name: Optional[str] = Field(None, description="New name")
    description: Optional[str] = Field(None, description="New description")
    is_template: Optional[bool] = Field(None, description="Template flag")
    is_active: Optional[bool] = Field(None, description="Active flag")


class ComponentResponse(BaseModel):
    """Component details response."""
    id: str
    component_name: str
    instrument_type_id: Optional[str]
    instrument_type_code: Optional[str]
    riskpod: Optional[str]
    allocation_type: str
    allocation_value: float
    security_id: Optional[str]
    delta: Optional[float]
    gamma: Optional[float]
    vega: Optional[float]
    theta: Optional[float]
    rho: Optional[float]
    duration: Optional[float]
    convexity: Optional[float]
    dv01: Optional[float]
    order_num: int


class CompositionResponse(BaseModel):
    """Full composition response with components."""
    id: str
    tenant_id: Optional[str]
    name: str
    description: Optional[str]
    is_template: bool
    is_active: bool
    components: List[ComponentResponse]
    component_count: int
    total_allocation: float
    created_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class CompositionListItem(BaseModel):
    """Composition summary for list view."""
    id: str
    name: str
    description: Optional[str]
    is_template: bool
    is_active: bool
    component_count: int
    total_allocation: float
    created_at: Optional[str]
    updated_at: Optional[str]


class RiskAttributionResponse(BaseModel):
    """Risk attribution breakdown by RiskPod."""
    position_id: str
    total_value: float
    attribution: Dict[str, float]
    components: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "position_id": "uuid-here",
                "total_value": 30000000,
                "attribution": {
                    "equity": 20000000,
                    "credit": 10000000,
                    "rates": 0,
                    "fx": 0,
                    "other": 0
                },
                "components": [
                    {"name": "S&P Future", "value": 10000000, "riskpod": "equity"},
                    {"name": "NVIDIA Put", "value": 10000000, "riskpod": "equity"},
                    {"name": "NVIDIA Bond", "value": 10000000, "riskpod": "credit"}
                ]
            }
        }


# =============================================================================
# Composition CRUD Endpoints
# =============================================================================

@router.get("", response_model=List[CompositionListItem])
def list_compositions(
    is_template: Optional[bool] = Query(None, description="Filter by template status"),
    is_active: bool = Query(True, description="Only show active compositions"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    tenant_id: Optional[UUID] = Query(None, description="Tenant UUID"),
):
    """
    List composition templates.

    Returns a paginated list of composition templates available
    for the tenant. Templates can be applied to positions for
    risk attribution.
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        offset = (page - 1) * page_size
        compositions = service.list_compositions(
            is_template=is_template,
            is_active=is_active,
            limit=page_size,
            offset=offset,
        )
        return [CompositionListItem(**c) for c in compositions]


@router.post("", response_model=Dict[str, str], status_code=201)
def create_composition(
    request: CreateCompositionRequest,
    tenant_id: Optional[UUID] = Query(None, description="Tenant UUID"),
    user_id: Optional[UUID] = Query(None, description="User creating the composition"),
):
    """
    Create a new composition template.

    A composition defines the components of a structured note or complex
    instrument. Components can be linked to instrument types for risk
    attribution across RiskPods.

    **Example Use Case:**
    A $30M structured note contains:
    - $10M S&P 500 Future (Equity RiskPod)
    - $10M NVIDIA Put option (Equity RiskPod)
    - $10M NVIDIA Bond (Credit RiskPod)

    The position stays in "Other" RiskPod, but risk is attributed as:
    - Equity: $20M
    - Credit: $10M
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)

        components = [
            {
                "name": c.name,
                "type_code": c.type_code,
                "allocation": c.allocation,
                "allocation_type": c.allocation_type,
                "security_id": c.security_id,
                "delta": c.delta,
                "gamma": c.gamma,
                "vega": c.vega,
                "theta": c.theta,
                "rho": c.rho,
                "duration": c.duration,
                "convexity": c.convexity,
                "dv01": c.dv01,
            }
            for c in request.components
        ]

        try:
            composition_id = service.create_composition(
                name=request.name,
                components=components,
                description=request.description,
                is_template=request.is_template,
                created_by=str(user_id) if user_id else None,
            )
            return {"id": composition_id, "status": "created"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/{composition_id}", response_model=CompositionResponse)
def get_composition(
    composition_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
):
    """
    Get composition details with all components.

    Returns the full composition including all component details,
    instrument types, and RiskPod assignments.
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        composition = service.get_composition(str(composition_id))

        if not composition:
            raise HTTPException(status_code=404, detail="Composition not found")

        data = composition.to_dict()
        # Convert components to response model format
        data['components'] = [
            ComponentResponse(
                id=c['id'],
                component_name=c['component_name'],
                instrument_type_id=c['instrument_type_id'],
                instrument_type_code=c['instrument_type_code'],
                riskpod=c['riskpod'],
                allocation_type=c['allocation_type'],
                allocation_value=c['allocation_value'] or 0,
                security_id=c['security_id'],
                delta=c['delta'],
                gamma=c['gamma'],
                vega=c['vega'],
                theta=c['theta'],
                rho=c['rho'],
                duration=c['duration'],
                convexity=c['convexity'],
                dv01=c['dv01'],
                order_num=c['order_num'],
            )
            for c in data['components']
        ]
        return CompositionResponse(**data)


@router.put("/{composition_id}")
def update_composition(
    composition_id: UUID,
    request: UpdateCompositionRequest,
    tenant_id: Optional[UUID] = Query(None),
):
    """
    Update composition metadata.

    Updates the composition's name, description, or status flags.
    Does not modify components - use component endpoints for that.
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        success = service.update_composition(
            composition_id=str(composition_id),
            name=request.name,
            description=request.description,
            is_template=request.is_template,
            is_active=request.is_active,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Composition not found or no changes made")
        return {"status": "updated", "id": str(composition_id)}


@router.delete("/{composition_id}")
def delete_composition(
    composition_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
):
    """
    Delete a composition.

    Cascades to delete all components. Position links are removed.
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        success = service.delete_composition(str(composition_id))
        if not success:
            raise HTTPException(status_code=404, detail="Composition not found")
        return {"status": "deleted", "id": str(composition_id)}


# =============================================================================
# Component Endpoints
# =============================================================================

@router.get("/{composition_id}/components", response_model=List[ComponentResponse])
def list_components(
    composition_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
):
    """
    List all components of a composition.

    Returns components ordered by their order_num field.
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        composition = service.get_composition(str(composition_id))

        if not composition:
            raise HTTPException(status_code=404, detail="Composition not found")

        return [
            ComponentResponse(
                id=c.id,
                component_name=c.component_name,
                instrument_type_id=c.instrument_type_id,
                instrument_type_code=c.instrument_type_code,
                riskpod=c.riskpod,
                allocation_type=c.allocation_type,
                allocation_value=float(c.allocation_value) if c.allocation_value else 0,
                security_id=c.security_id,
                delta=float(c.delta) if c.delta else None,
                gamma=float(c.gamma) if c.gamma else None,
                vega=float(c.vega) if c.vega else None,
                theta=float(c.theta) if c.theta else None,
                rho=float(c.rho) if c.rho else None,
                duration=float(c.duration) if c.duration else None,
                convexity=float(c.convexity) if c.convexity else None,
                dv01=float(c.dv01) if c.dv01 else None,
                order_num=c.order_num,
            )
            for c in composition.components
        ]


@router.post("/{composition_id}/components", status_code=201)
def add_component(
    composition_id: UUID,
    request: ComponentInput,
    tenant_id: Optional[UUID] = Query(None),
):
    """
    Add a component to an existing composition.

    The component is added at the end of the component list.
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)

        component = {
            "name": request.name,
            "type_code": request.type_code,
            "allocation": request.allocation,
            "allocation_type": request.allocation_type,
            "security_id": request.security_id,
            "delta": request.delta,
            "gamma": request.gamma,
            "vega": request.vega,
            "theta": request.theta,
            "rho": request.rho,
            "duration": request.duration,
            "convexity": request.convexity,
            "dv01": request.dv01,
        }

        component_id = service.add_component(str(composition_id), component)
        if not component_id:
            raise HTTPException(status_code=400, detail="Failed to add component")
        return {"id": component_id, "status": "created"}


@router.delete("/{composition_id}/components/{component_id}")
def remove_component(
    composition_id: UUID,
    component_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
):
    """Remove a component from a composition."""
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        success = service.remove_component(str(component_id))
        if not success:
            raise HTTPException(status_code=404, detail="Component not found")
        return {"status": "deleted", "id": str(component_id)}


# =============================================================================
# Position Composition Endpoints
# =============================================================================

@router.get("/position/{position_id}", response_model=Optional[CompositionResponse])
def get_position_composition(
    position_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
):
    """
    Get the composition applied to a position.

    Returns null if no composition is applied.
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        composition = service.get_position_composition(str(position_id))

        if not composition:
            return None

        data = composition.to_dict()
        data['components'] = [
            ComponentResponse(
                id=c['id'],
                component_name=c['component_name'],
                instrument_type_id=c['instrument_type_id'],
                instrument_type_code=c['instrument_type_code'],
                riskpod=c['riskpod'],
                allocation_type=c['allocation_type'],
                allocation_value=c['allocation_value'] or 0,
                security_id=c['security_id'],
                delta=c['delta'],
                gamma=c['gamma'],
                vega=c['vega'],
                theta=c['theta'],
                rho=c['rho'],
                duration=c['duration'],
                convexity=c['convexity'],
                dv01=c['dv01'],
                order_num=c['order_num'],
            )
            for c in data['components']
        ]
        return CompositionResponse(**data)


@router.post("/position/{position_id}")
def apply_composition_to_position(
    position_id: UUID,
    composition_id: UUID = Query(..., description="Composition UUID to apply"),
    tenant_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
):
    """
    Apply a composition to a position for risk attribution.

    The position's value will be attributed across RiskPods based
    on the composition's component allocations.
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        success = service.apply_to_position(
            position_id=str(position_id),
            composition_id=str(composition_id),
            applied_by=str(user_id) if user_id else None,
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to apply composition")
        return {"status": "applied", "position_id": str(position_id)}


@router.delete("/position/{position_id}")
def remove_composition_from_position(
    position_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
):
    """Remove composition from a position."""
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        success = service.remove_from_position(str(position_id))
        if not success:
            raise HTTPException(status_code=404, detail="No composition found for position")
        return {"status": "removed", "position_id": str(position_id)}


@router.get("/position/{position_id}/risk-attribution", response_model=RiskAttributionResponse)
def get_position_risk_attribution(
    position_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
):
    """
    Get risk attribution for a position.

    Returns the position's value broken down by RiskPod based on
    its composition. If no composition is applied, the entire value
    is attributed to "other".

    **Example Response:**
    ```json
    {
        "position_id": "uuid",
        "total_value": 30000000,
        "attribution": {
            "equity": 20000000,
            "credit": 10000000,
            "rates": 0,
            "fx": 0,
            "other": 0
        },
        "components": [
            {"name": "S&P Future", "value": 10000000, "riskpod": "equity"},
            {"name": "NVIDIA Put", "value": 10000000, "riskpod": "equity"},
            {"name": "NVIDIA Bond", "value": 10000000, "riskpod": "credit"}
        ]
    }
    ```
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        attribution = service.get_risk_attribution(str(position_id))

        if not attribution:
            raise HTTPException(status_code=404, detail="Position not found")

        return RiskAttributionResponse(**attribution.to_dict())


# =============================================================================
# Lookup Endpoints
# =============================================================================

@router.get("/lookup/by-name")
def find_composition_by_name(
    name: str = Query(..., description="Composition name to search for"),
    tenant_id: Optional[UUID] = Query(None),
):
    """
    Find a composition template by name.

    Used during import to auto-match structured notes to existing
    composition templates.
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        composition = service.find_composition_by_name(name)

        if not composition:
            return {"found": False, "name": name}

        return {
            "found": True,
            "composition_id": composition.id,
            "name": composition.name,
            "component_count": len(composition.components),
        }


@router.post("/apply-by-pattern")
def apply_composition_by_pattern(
    composition_id: UUID = Query(..., description="Composition to apply"),
    security_name_pattern: str = Query(..., description="Security name pattern to match"),
    tenant_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
):
    """
    Apply composition to all positions matching a security name pattern.

    Useful for retroactively applying a composition template to
    existing positions after it's defined.

    **Example:**
    Apply composition to all positions where security name contains "Structured Note ABC"
    """
    with get_db_connection() as conn:
        service = CompositionService(conn, str(tenant_id) if tenant_id else None)
        count = service.apply_to_positions_by_security_name(
            composition_id=str(composition_id),
            security_name_pattern=security_name_pattern,
            applied_by=str(user_id) if user_id else None,
        )
        return {
            "status": "applied",
            "composition_id": str(composition_id),
            "positions_updated": count,
            "pattern": security_name_pattern,
        }
