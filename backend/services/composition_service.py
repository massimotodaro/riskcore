"""
Composition Service for RISKCORE
=================================
Manages structured instrument compositions for pricing and risk attribution.

Structured notes and complex instruments stay in the "Other" RiskPod,
but their components are tracked for:
1. Pricing - aggregate component prices
2. Risk metrics - Greeks, duration from components
3. Risk attribution - exposure by RiskPod

Author: RISKCORE Team
Date: 2026-01-15
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
import uuid

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class ComponentData:
    """Component within a composition."""
    id: Optional[str]
    component_name: str
    instrument_type_id: Optional[str]
    instrument_type_code: Optional[str]
    riskpod: Optional[str]
    allocation_type: str  # 'percentage' or 'notional'
    allocation_value: Decimal
    security_id: Optional[str]
    delta: Optional[Decimal]
    gamma: Optional[Decimal]
    vega: Optional[Decimal]
    theta: Optional[Decimal]
    rho: Optional[Decimal]
    duration: Optional[Decimal]
    convexity: Optional[Decimal]
    dv01: Optional[Decimal]
    order_num: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "component_name": self.component_name,
            "instrument_type_id": self.instrument_type_id,
            "instrument_type_code": self.instrument_type_code,
            "riskpod": self.riskpod,
            "allocation_type": self.allocation_type,
            "allocation_value": float(self.allocation_value) if self.allocation_value else None,
            "security_id": self.security_id,
            "delta": float(self.delta) if self.delta else None,
            "gamma": float(self.gamma) if self.gamma else None,
            "vega": float(self.vega) if self.vega else None,
            "theta": float(self.theta) if self.theta else None,
            "rho": float(self.rho) if self.rho else None,
            "duration": float(self.duration) if self.duration else None,
            "convexity": float(self.convexity) if self.convexity else None,
            "dv01": float(self.dv01) if self.dv01 else None,
            "order_num": self.order_num,
        }


@dataclass
class CompositionData:
    """Structured instrument composition."""
    id: str
    tenant_id: Optional[str]
    name: str
    name_normalized: str
    description: Optional[str]
    is_template: bool
    is_active: bool
    components: List[ComponentData]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "is_template": self.is_template,
            "is_active": self.is_active,
            "components": [c.to_dict() for c in self.components],
            "component_count": len(self.components),
            "total_allocation": sum(c.allocation_value for c in self.components if c.allocation_type == 'percentage'),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class RiskAttribution:
    """Risk attribution across RiskPods."""
    position_id: str
    total_value: Decimal
    equity: Decimal
    rates: Decimal
    credit: Decimal
    fx: Decimal
    other: Decimal
    components: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position_id": self.position_id,
            "total_value": float(self.total_value) if self.total_value else 0,
            "attribution": {
                "equity": float(self.equity) if self.equity else 0,
                "rates": float(self.rates) if self.rates else 0,
                "credit": float(self.credit) if self.credit else 0,
                "fx": float(self.fx) if self.fx else 0,
                "other": float(self.other) if self.other else 0,
            },
            "components": self.components,
        }


# ============================================
# SERVICE CLASS
# ============================================

class CompositionService:
    """
    Manages structured instrument compositions for pricing and risk.

    Usage:
        service = CompositionService(conn, tenant_id)

        # Create composition template
        comp_id = service.create_composition(
            name="ABC Structured Note",
            components=[
                {"name": "S&P Future", "type_code": "FUTURE", "allocation": 33.33},
                {"name": "NVIDIA Put", "type_code": "EQO", "allocation": 33.33},
                {"name": "NVIDIA Bond", "type_code": "CORPBOND", "allocation": 33.34},
            ]
        )

        # Apply to position
        service.apply_to_position(position_id, comp_id)

        # Get risk attribution for a position
        attribution = service.get_risk_attribution(position_id)
    """

    def __init__(self, db_connection, tenant_id: Optional[str] = None):
        self.conn = db_connection
        self.tenant_id = tenant_id

    def create_composition(
        self,
        name: str,
        components: List[Dict[str, Any]],
        description: Optional[str] = None,
        is_template: bool = True,
        created_by: Optional[str] = None,
    ) -> str:
        """
        Create a new composition template.

        Args:
            name: Display name for the composition
            components: List of component dicts with keys:
                - name: Component name (required)
                - type_code: Instrument type code (e.g., 'FUTURE', 'EQO')
                - allocation: Percentage allocation (default type)
                - allocation_type: 'percentage' or 'notional'
                - security_id: Optional link to security
                - delta, gamma, vega, theta, duration, etc.: Optional risk params
            description: Optional description
            is_template: Whether this can be reused for future imports
            created_by: User UUID who created this

        Returns:
            UUID of the created composition
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        composition_id = str(uuid.uuid4())
        name_normalized = self._normalize_name(name)

        try:
            # Insert composition
            cur.execute("""
                INSERT INTO instrument_compositions
                (id, tenant_id, name, name_normalized, description, is_template, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                composition_id,
                self.tenant_id,
                name,
                name_normalized,
                description,
                is_template,
                created_by,
            ))

            # Insert components
            for idx, comp in enumerate(components):
                self._add_component(
                    cur,
                    composition_id,
                    comp,
                    order_num=idx,
                )

            self.conn.commit()
            logger.info(f"Created composition '{name}' with {len(components)} components")
            return composition_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating composition: {e}")
            raise

    def _add_component(
        self,
        cur,
        composition_id: str,
        comp: Dict[str, Any],
        order_num: int = 0,
    ) -> str:
        """Add a component to a composition."""
        component_id = str(uuid.uuid4())

        # Look up instrument type by code
        instrument_type_id = None
        type_code = comp.get("type_code") or comp.get("instrument_type_code")
        if type_code:
            cur.execute("""
                SELECT id FROM instrument_types WHERE code = %s AND is_active = TRUE
            """, (type_code.upper(),))
            row = cur.fetchone()
            if row:
                instrument_type_id = str(row['id'])

        cur.execute("""
            INSERT INTO composition_components
            (id, composition_id, instrument_type_id, component_name,
             allocation_type, allocation_value, security_id,
             delta, gamma, vega, theta, rho, duration, convexity, dv01, order_num)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            component_id,
            composition_id,
            instrument_type_id,
            comp.get("name") or comp.get("component_name"),
            comp.get("allocation_type", "percentage"),
            comp.get("allocation") or comp.get("allocation_value", 0),
            comp.get("security_id"),
            comp.get("delta"),
            comp.get("gamma"),
            comp.get("vega"),
            comp.get("theta"),
            comp.get("rho"),
            comp.get("duration"),
            comp.get("convexity"),
            comp.get("dv01"),
            order_num,
        ))

        return component_id

    def get_composition(self, composition_id: str) -> Optional[CompositionData]:
        """Get composition with all components."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, tenant_id, name, name_normalized, description,
                   is_template, is_active, created_by, created_at, updated_at
            FROM instrument_compositions
            WHERE id = %s
        """, (composition_id,))

        row = cur.fetchone()
        if not row:
            return None

        # Get components
        cur.execute("""
            SELECT cc.id, cc.component_name, cc.instrument_type_id,
                   it.code AS instrument_type_code, it.riskpod,
                   cc.allocation_type, cc.allocation_value, cc.security_id,
                   cc.delta, cc.gamma, cc.vega, cc.theta, cc.rho,
                   cc.duration, cc.convexity, cc.dv01, cc.order_num
            FROM composition_components cc
            LEFT JOIN instrument_types it ON cc.instrument_type_id = it.id
            WHERE cc.composition_id = %s
            ORDER BY cc.order_num
        """, (composition_id,))

        components = [
            ComponentData(
                id=str(c['id']),
                component_name=c['component_name'],
                instrument_type_id=str(c['instrument_type_id']) if c['instrument_type_id'] else None,
                instrument_type_code=c['instrument_type_code'],
                riskpod=c['riskpod'],
                allocation_type=c['allocation_type'],
                allocation_value=c['allocation_value'] or Decimal(0),
                security_id=str(c['security_id']) if c['security_id'] else None,
                delta=c['delta'],
                gamma=c['gamma'],
                vega=c['vega'],
                theta=c['theta'],
                rho=c['rho'],
                duration=c['duration'],
                convexity=c['convexity'],
                dv01=c['dv01'],
                order_num=c['order_num'] or 0,
            )
            for c in cur.fetchall()
        ]

        return CompositionData(
            id=str(row['id']),
            tenant_id=str(row['tenant_id']) if row['tenant_id'] else None,
            name=row['name'],
            name_normalized=row['name_normalized'],
            description=row['description'],
            is_template=row['is_template'],
            is_active=row['is_active'],
            components=components,
            created_by=str(row['created_by']) if row['created_by'] else None,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def list_compositions(
        self,
        is_template: Optional[bool] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List composition templates."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT ic.id, ic.name, ic.description, ic.is_template, ic.is_active,
                   ic.created_at, ic.updated_at,
                   COUNT(cc.id) AS component_count,
                   SUM(cc.allocation_value) AS total_allocation
            FROM instrument_compositions ic
            LEFT JOIN composition_components cc ON cc.composition_id = ic.id
            WHERE (ic.tenant_id = %s OR ic.tenant_id IS NULL)
        """
        params = [self.tenant_id]

        if is_template is not None:
            query += " AND ic.is_template = %s"
            params.append(is_template)

        if is_active:
            query += " AND ic.is_active = TRUE"

        query += """
            GROUP BY ic.id
            ORDER BY ic.updated_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        cur.execute(query, params)

        return [
            {
                "id": str(row['id']),
                "name": row['name'],
                "description": row['description'],
                "is_template": row['is_template'],
                "is_active": row['is_active'],
                "component_count": row['component_count'] or 0,
                "total_allocation": float(row['total_allocation']) if row['total_allocation'] else 0,
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
            }
            for row in cur.fetchall()
        ]

    def update_composition(
        self,
        composition_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_template: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        """Update composition metadata."""
        cur = self.conn.cursor()

        updates = []
        params = []

        if name is not None:
            updates.append("name = %s")
            params.append(name)
            updates.append("name_normalized = %s")
            params.append(self._normalize_name(name))

        if description is not None:
            updates.append("description = %s")
            params.append(description)

        if is_template is not None:
            updates.append("is_template = %s")
            params.append(is_template)

        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)

        if not updates:
            return False

        params.append(composition_id)

        try:
            cur.execute(f"""
                UPDATE instrument_compositions
                SET {", ".join(updates)}
                WHERE id = %s
            """, params)
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating composition: {e}")
            return False

    def delete_composition(self, composition_id: str) -> bool:
        """Delete a composition (cascades to components)."""
        cur = self.conn.cursor()

        try:
            cur.execute("""
                DELETE FROM instrument_compositions WHERE id = %s
            """, (composition_id,))
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error deleting composition: {e}")
            return False

    def add_component(
        self,
        composition_id: str,
        component: Dict[str, Any],
    ) -> Optional[str]:
        """Add a component to an existing composition."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get max order_num
        cur.execute("""
            SELECT COALESCE(MAX(order_num), -1) + 1 AS next_order
            FROM composition_components
            WHERE composition_id = %s
        """, (composition_id,))
        next_order = cur.fetchone()['next_order']

        try:
            component_id = self._add_component(cur, composition_id, component, next_order)
            self.conn.commit()
            return component_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error adding component: {e}")
            return None

    def remove_component(self, component_id: str) -> bool:
        """Remove a component from a composition."""
        cur = self.conn.cursor()

        try:
            cur.execute("""
                DELETE FROM composition_components WHERE id = %s
            """, (component_id,))
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error removing component: {e}")
            return False

    def apply_to_position(
        self,
        position_id: str,
        composition_id: str,
        applied_by: Optional[str] = None,
    ) -> bool:
        """Apply a composition to a position for risk attribution."""
        cur = self.conn.cursor()

        try:
            # Upsert position_compositions
            cur.execute("""
                INSERT INTO position_compositions (position_id, composition_id, applied_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (position_id)
                DO UPDATE SET
                    composition_id = EXCLUDED.composition_id,
                    applied_at = NOW(),
                    applied_by = EXCLUDED.applied_by
            """, (position_id, composition_id, applied_by))
            self.conn.commit()
            logger.info(f"Applied composition {composition_id} to position {position_id}")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error applying composition: {e}")
            return False

    def remove_from_position(self, position_id: str) -> bool:
        """Remove composition from a position."""
        cur = self.conn.cursor()

        try:
            cur.execute("""
                DELETE FROM position_compositions WHERE position_id = %s
            """, (position_id,))
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error removing composition from position: {e}")
            return False

    def get_position_composition(self, position_id: str) -> Optional[CompositionData]:
        """Get the composition applied to a position."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT composition_id FROM position_compositions WHERE position_id = %s
        """, (position_id,))

        row = cur.fetchone()
        if not row:
            return None

        return self.get_composition(str(row['composition_id']))

    def get_risk_attribution(self, position_id: str) -> Optional[RiskAttribution]:
        """
        Calculate risk attribution for a position based on its composition.

        Returns exposure broken down by RiskPod.
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get position value
        cur.execute("""
            SELECT p.id, p.quantity, p.price, p.market_value_base,
                   COALESCE(p.market_value_base, p.quantity * COALESCE(p.price, 0)) AS total_value
            FROM positions p
            WHERE p.id = %s
        """, (position_id,))

        pos_row = cur.fetchone()
        if not pos_row:
            return None

        total_value = pos_row['total_value'] or Decimal(0)

        # Get composition
        composition = self.get_position_composition(position_id)

        if not composition:
            # No composition - return all as 'other'
            return RiskAttribution(
                position_id=position_id,
                total_value=total_value,
                equity=Decimal(0),
                rates=Decimal(0),
                credit=Decimal(0),
                fx=Decimal(0),
                other=total_value,
                components=[],
            )

        # Calculate attribution by RiskPod
        equity = Decimal(0)
        rates = Decimal(0)
        credit = Decimal(0)
        fx = Decimal(0)
        other = Decimal(0)

        component_values = []

        for comp in composition.components:
            if comp.allocation_type == 'percentage':
                comp_value = total_value * (comp.allocation_value / Decimal(100))
            else:
                comp_value = comp.allocation_value

            riskpod = comp.riskpod or 'other'

            if riskpod == 'equity':
                equity += comp_value
            elif riskpod == 'rates':
                rates += comp_value
            elif riskpod == 'credit':
                credit += comp_value
            elif riskpod == 'fx':
                fx += comp_value
            else:
                other += comp_value

            component_values.append({
                "name": comp.component_name,
                "value": float(comp_value),
                "allocation": float(comp.allocation_value),
                "allocation_type": comp.allocation_type,
                "riskpod": riskpod,
                "instrument_type": comp.instrument_type_code,
            })

        return RiskAttribution(
            position_id=position_id,
            total_value=total_value,
            equity=equity,
            rates=rates,
            credit=credit,
            fx=fx,
            other=other,
            components=component_values,
        )

    def find_composition_by_name(self, name: str) -> Optional[CompositionData]:
        """Find a composition template by name (for auto-applying during import)."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        name_normalized = self._normalize_name(name)

        cur.execute("""
            SELECT id FROM instrument_compositions
            WHERE name_normalized = %s
              AND (tenant_id = %s OR tenant_id IS NULL)
              AND is_template = TRUE
              AND is_active = TRUE
            ORDER BY tenant_id NULLS LAST
            LIMIT 1
        """, (name_normalized, self.tenant_id))

        row = cur.fetchone()
        if not row:
            return None

        return self.get_composition(str(row['id']))

    def apply_to_positions_by_security_name(
        self,
        composition_id: str,
        security_name_pattern: str,
        applied_by: Optional[str] = None,
    ) -> int:
        """
        Apply composition to all existing positions matching a security name pattern.

        Returns count of positions updated.
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Find matching positions
        cur.execute("""
            SELECT p.id
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            WHERE LOWER(s.name) LIKE LOWER(%s)
              AND p.tenant_id = %s
              AND p.is_active = TRUE
              AND NOT EXISTS (
                  SELECT 1 FROM position_compositions pc WHERE pc.position_id = p.id
              )
        """, (f"%{security_name_pattern}%", self.tenant_id))

        positions = cur.fetchall()
        count = 0

        for pos in positions:
            if self.apply_to_position(str(pos['id']), composition_id, applied_by):
                count += 1

        logger.info(f"Applied composition {composition_id} to {count} positions matching '{security_name_pattern}'")
        return count

    def _normalize_name(self, name: str) -> str:
        """Normalize name for matching."""
        if not name:
            return ""
        return " ".join(name.lower().strip().split())


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def get_position_risk_attribution(
    db_connection,
    position_id: str,
    tenant_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Convenience function to get risk attribution for a position."""
    service = CompositionService(db_connection, tenant_id)
    result = service.get_risk_attribution(position_id)
    return result.to_dict() if result else None
