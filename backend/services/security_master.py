"""
Security Master Service for RISKCORE
=====================================
Resolves, creates, and enriches securities using OpenFIGI and the database.

Key responsibilities:
1. Identifier resolution: Given any identifier type, find the canonical security
2. Security creation: Create new securities from OpenFIGI data
3. Enrichment: Update existing securities with additional identifiers
4. Deduplication: Ensure no duplicate securities are created

Author: RISKCORE Team
Date: 2026-01-11
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid

import psycopg2
from psycopg2.extras import RealDictCursor

from .openfigi import (
    OpenFIGIClient,
    FIGIResult,
    MappingResult,
    MappingJob,
    get_client as get_openfigi_client,
)

# Lazy import to avoid circular dependency
InstrumentNormalizationService = None

def _get_normalization_service(conn, tenant_id=None):
    """Lazy load the normalization service."""
    global InstrumentNormalizationService
    if InstrumentNormalizationService is None:
        from .instrument_normalization import InstrumentNormalizationService
    return InstrumentNormalizationService(conn, tenant_id)

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

# Map OpenFIGI security types to our asset_class enum
SECURITY_TYPE_MAP = {
    "Common Stock": "equity",
    "Preferred Stock": "equity",
    "Depositary Receipt": "equity",
    "ETP": "fund",  # ETF/ETN
    "REIT": "equity",
    "Bond": "fixed_income",
    "Option": "option",
    "Future": "future",
    "Warrant": "equity",
    "Index": "other",
    "Mutual Fund": "fund",
    "Unit": "fund",
}

# Map OpenFIGI market sectors to our asset_class
MARKET_SECTOR_MAP = {
    "Equity": "equity",
    "Corp": "fixed_income",
    "Govt": "fixed_income",
    "Mtge": "fixed_income",
    "Muni": "fixed_income",
    "Pfd": "equity",
    "M-Mkt": "fixed_income",
    "Comdty": "commodity",
    "Curncy": "fx",
    "Index": "other",
}

# Identifier type mapping from user input to database enum
IDENTIFIER_TYPE_NORMALIZE = {
    "ticker": "ticker",
    "TICKER": "ticker",
    "cusip": "cusip",
    "CUSIP": "cusip",
    "ID_CUSIP": "cusip",
    "isin": "isin",
    "ISIN": "isin",
    "ID_ISIN": "isin",
    "sedol": "sedol",
    "SEDOL": "sedol",
    "ID_SEDOL": "sedol",
    "figi": "figi",
    "FIGI": "figi",
    "ID_BB_GLOBAL": "figi",
    "composite_figi": "composite_figi",
    "COMPOSITE_FIGI": "composite_figi",
}

# Map user-friendly identifier types to OpenFIGI API types
IDENTIFIER_TO_OPENFIGI = {
    "ticker": "TICKER",
    "cusip": "ID_CUSIP",
    "isin": "ID_ISIN",
    "sedol": "ID_SEDOL",
    "figi": "ID_BB_GLOBAL",
    "composite_figi": "COMPOSITE_FIGI",
}


@dataclass
class ResolvedSecurity:
    """Result of security resolution."""
    security_id: str
    figi: Optional[str]
    name: str
    ticker: Optional[str]
    asset_class: str
    currency: str
    riskpod: Optional[str] = None
    is_new: bool = False
    enriched: bool = False


class SecurityMasterService:
    """
    Service for managing the security master.

    Usage:
        service = SecurityMasterService(db_conn)

        # Resolve an identifier to a security
        security = service.resolve_identifier("ticker", "AAPL", exchange="US")

        # Batch resolve
        securities = service.resolve_identifiers([
            {"type": "ticker", "value": "AAPL", "exchange": "US"},
            {"type": "cusip", "value": "037833100"},
            {"type": "isin", "value": "US0378331005"},
        ])
    """

    def __init__(self, db_connection, openfigi_client: Optional[OpenFIGIClient] = None):
        """
        Initialize the security master service.

        Args:
            db_connection: psycopg2 database connection
            openfigi_client: Optional OpenFIGI client (uses global if not provided)
        """
        self.conn = db_connection
        self.figi_client = openfigi_client or get_openfigi_client()

    def resolve_identifier(
        self,
        id_type: str,
        id_value: str,
        exchange: Optional[str] = None,
        currency: Optional[str] = None,
        create_if_missing: bool = True,
        instrument_type_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Optional[ResolvedSecurity]:
        """
        Resolve an identifier to a canonical security.

        Process:
        1. Check if identifier exists in security_identifiers table
        2. If found, return the linked security
        3. If not found, query OpenFIGI
        4. If OpenFIGI returns result, check if FIGI exists in our DB
        5. If FIGI exists, add the new identifier mapping
        6. If FIGI doesn't exist, create new security

        Args:
            id_type: Identifier type (ticker, cusip, isin, sedol, figi)
            id_value: The identifier value
            exchange: Exchange code (required for ticker)
            currency: Currency filter
            create_if_missing: Whether to create security if not found
            instrument_type_name: Client-provided instrument type name for normalization
            tenant_id: Tenant UUID for tenant-specific mappings

        Returns:
            ResolvedSecurity or None if not found and create_if_missing=False
        """
        # Normalize identifier type
        id_type_normalized = IDENTIFIER_TYPE_NORMALIZE.get(id_type, id_type.lower())

        logger.info(f"Resolving {id_type_normalized}: {id_value}")

        # Step 1: Check local database
        security = self._find_by_identifier(id_type_normalized, id_value, exchange)
        if security:
            logger.info(f"Found in local DB: {security['name']} (ID: {security['id']})")
            # Infer RiskPod from existing asset class
            riskpod = self._infer_riskpod(security["asset_class"])
            return ResolvedSecurity(
                security_id=security["id"],
                figi=security.get("figi"),
                name=security["name"],
                ticker=self._get_ticker(security["id"]),
                asset_class=security["asset_class"],
                currency=security["currency"],
                riskpod=riskpod,
                is_new=False,
                enriched=False,
            )

        # Step 2: Query OpenFIGI
        openfigi_type = IDENTIFIER_TO_OPENFIGI.get(id_type_normalized, id_type_normalized.upper())
        figi_result = self.figi_client.map_identifier(
            openfigi_type,
            id_value,
            exch_code=exchange,
            currency=currency,
        )

        if not figi_result.success or not figi_result.results:
            logger.warning(f"OpenFIGI lookup failed for {id_type}: {id_value} - {figi_result.error}")
            if not create_if_missing:
                return None
            # Create placeholder security without FIGI
            return self._create_placeholder_security(
                id_type_normalized, id_value, exchange, currency,
                instrument_type_name=instrument_type_name,
                tenant_id=tenant_id,
            )

        # Use first result
        figi_data = figi_result.results[0]
        logger.info(f"OpenFIGI found: {figi_data.name} (FIGI: {figi_data.figi})")

        # Step 3: Check if this FIGI already exists
        security = self._find_by_figi(figi_data.figi)
        if security:
            # Add the new identifier mapping
            self._add_identifier(security["id"], id_type_normalized, id_value, exchange)
            logger.info(f"Added identifier to existing security: {security['name']}")
            riskpod = self._infer_riskpod(security["asset_class"])
            return ResolvedSecurity(
                security_id=security["id"],
                figi=security["figi"],
                name=security["name"],
                ticker=figi_data.ticker or self._get_ticker(security["id"]),
                asset_class=security["asset_class"],
                currency=security["currency"],
                riskpod=riskpod,
                is_new=False,
                enriched=True,
            )

        # Step 4: Create new security
        if not create_if_missing:
            return None

        new_security = self._create_security_from_figi(
            figi_data, id_type_normalized, id_value, exchange,
            instrument_type_name=instrument_type_name,
            tenant_id=tenant_id,
        )
        return new_security

    def resolve_identifiers(
        self,
        identifiers: List[Dict[str, Any]],
        create_if_missing: bool = True,
        tenant_id: Optional[str] = None,
    ) -> List[Optional[ResolvedSecurity]]:
        """
        Resolve multiple identifiers in batch.

        Args:
            identifiers: List of dicts with keys: type, value, exchange,
                        instrument_type_name (all optional except type/value)
            create_if_missing: Whether to create securities if not found
            tenant_id: Default tenant UUID (can be overridden per identifier)

        Returns:
            List of ResolvedSecurity (same order as input, None for failures)
        """
        results = []
        for id_info in identifiers:
            try:
                result = self.resolve_identifier(
                    id_type=id_info.get("type", id_info.get("idType", "")),
                    id_value=id_info.get("value", id_info.get("idValue", "")),
                    exchange=id_info.get("exchange", id_info.get("exchCode")),
                    currency=id_info.get("currency"),
                    create_if_missing=create_if_missing,
                    instrument_type_name=id_info.get("instrument_type_name", id_info.get("instrumentType")),
                    tenant_id=id_info.get("tenant_id", tenant_id),
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error resolving {id_info}: {e}")
                results.append(None)
        return results

    def enrich_security(self, security_id: str) -> bool:
        """
        Enrich an existing security with OpenFIGI data.

        Looks up the security's identifiers in OpenFIGI and adds any missing data.

        Args:
            security_id: UUID of the security to enrich

        Returns:
            True if enrichment added new data, False otherwise
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get security
        cur.execute("SELECT * FROM securities WHERE id = %s", (security_id,))
        security = cur.fetchone()
        if not security:
            logger.warning(f"Security not found: {security_id}")
            return False

        # If already has FIGI and was recently enriched, skip
        if security.get("figi") and security.get("last_enriched_at"):
            # Check if enriched in last 7 days
            from datetime import timedelta
            if security["last_enriched_at"] > datetime.now() - timedelta(days=7):
                logger.info(f"Security {security_id} recently enriched, skipping")
                return False

        # Get existing identifiers
        cur.execute("""
            SELECT identifier_type, identifier_value, exchange_code
            FROM security_identifiers
            WHERE security_id = %s
        """, (security_id,))
        identifiers = cur.fetchall()

        # Try to get FIGI data using any identifier
        figi_data = None
        for ident in identifiers:
            openfigi_type = IDENTIFIER_TO_OPENFIGI.get(ident["identifier_type"])
            if not openfigi_type:
                continue

            result = self.figi_client.map_identifier(
                openfigi_type,
                ident["identifier_value"],
                exch_code=ident.get("exchange_code"),
            )
            if result.success and result.results:
                figi_data = result.results[0]
                break

        if not figi_data:
            logger.warning(f"Could not enrich security {security_id} - no OpenFIGI match")
            return False

        # Update security with FIGI data
        enriched = False

        if not security.get("figi") and figi_data.figi:
            cur.execute("""
                UPDATE securities SET figi = %s, last_enriched_at = NOW()
                WHERE id = %s AND figi IS NULL
            """, (figi_data.figi, security_id))
            enriched = True

        # Add any new identifiers
        if figi_data.ticker:
            self._add_identifier(security_id, "ticker", figi_data.ticker, figi_data.exch_code)
            enriched = True

        if figi_data.composite_figi:
            self._add_identifier(security_id, "composite_figi", figi_data.composite_figi, None)
            enriched = True

        if enriched:
            cur.execute("""
                UPDATE securities SET last_enriched_at = NOW(), is_verified = TRUE
                WHERE id = %s
            """, (security_id,))
            self.conn.commit()

        return enriched

    def _find_by_identifier(
        self,
        id_type: str,
        id_value: str,
        exchange: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find a security by identifier in the database."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if exchange:
            cur.execute("""
                SELECT s.* FROM securities s
                JOIN security_identifiers si ON si.security_id = s.id
                WHERE si.identifier_type = %s
                AND si.identifier_value = %s
                AND (si.exchange_code = %s OR si.exchange_code IS NULL)
                AND s.is_active = TRUE
                LIMIT 1
            """, (id_type, id_value, exchange))
        else:
            cur.execute("""
                SELECT s.* FROM securities s
                JOIN security_identifiers si ON si.security_id = s.id
                WHERE si.identifier_type = %s
                AND si.identifier_value = %s
                AND s.is_active = TRUE
                LIMIT 1
            """, (id_type, id_value))

        return cur.fetchone()

    def _find_by_figi(self, figi: str) -> Optional[Dict[str, Any]]:
        """Find a security by FIGI."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM securities WHERE figi = %s AND is_active = TRUE
        """, (figi,))
        return cur.fetchone()

    def _get_ticker(self, security_id: str) -> Optional[str]:
        """Get the primary ticker for a security."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT identifier_value FROM security_identifiers
            WHERE security_id = %s AND identifier_type = 'ticker'
            ORDER BY is_primary DESC
            LIMIT 1
        """, (security_id,))
        result = cur.fetchone()
        return result[0] if result else None

    def _determine_asset_class(
        self,
        security_type: Optional[str],
        market_sector: Optional[str],
        instrument_type_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Tuple[str, Optional[str]]:
        """
        Determine asset class and RiskPod for a security.

        Priority:
        1. Instrument type name (via normalization service)
        2. OpenFIGI security type mapping
        3. OpenFIGI market sector mapping
        4. Default to 'other'

        Args:
            security_type: OpenFIGI security type (e.g., "Common Stock")
            market_sector: OpenFIGI market sector (e.g., "Equity")
            instrument_type_name: Client-provided instrument type name
            tenant_id: Tenant UUID for tenant-specific mappings

        Returns:
            Tuple of (asset_class, riskpod)
        """
        # Priority 1: Use instrument normalization if name provided
        if instrument_type_name:
            try:
                normalizer = _get_normalization_service(self.conn, tenant_id)
                result = normalizer.normalize(instrument_type_name)
                if result.success and result.asset_class:
                    logger.info(
                        f"Normalized '{instrument_type_name}' -> "
                        f"asset_class={result.asset_class}, riskpod={result.riskpod}"
                    )
                    return (result.asset_class, result.riskpod)
            except Exception as e:
                logger.warning(f"Instrument normalization failed: {e}")

        # Priority 2: OpenFIGI security type mapping
        if security_type:
            asset_class = SECURITY_TYPE_MAP.get(security_type)
            if asset_class:
                # Infer RiskPod from asset class
                riskpod = self._infer_riskpod(asset_class)
                return (asset_class, riskpod)

        # Priority 3: OpenFIGI market sector mapping
        if market_sector:
            asset_class = MARKET_SECTOR_MAP.get(market_sector)
            if asset_class:
                riskpod = self._infer_riskpod(asset_class)
                return (asset_class, riskpod)

        # Default
        return ("other", "other")

    def _infer_riskpod(self, asset_class: str) -> str:
        """Infer RiskPod from asset class."""
        ASSET_CLASS_TO_RISKPOD = {
            "equity": "equity",
            "fixed_income": "rates",
            "fx": "fx",
            "option": "equity",  # Default, but options can span all RiskPods
            "future": "equity",  # Default, futures can span all RiskPods
            "swap": "rates",
            "cds": "credit",
            "commodity": "other",
            "crypto": "other",
            "fund": "equity",
            "other": "other",
        }
        return ASSET_CLASS_TO_RISKPOD.get(asset_class, "other")

    def _add_identifier(
        self,
        security_id: str,
        id_type: str,
        id_value: str,
        exchange: Optional[str],
    ) -> bool:
        """Add an identifier to a security (if not exists)."""
        cur = self.conn.cursor()
        try:
            cur.execute("""
                INSERT INTO security_identifiers (security_id, identifier_type, identifier_value, exchange_code)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (identifier_type, identifier_value, exchange_code) DO NOTHING
            """, (security_id, id_type, id_value, exchange))
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error adding identifier: {e}")
            self.conn.rollback()
            return False

    def _create_security_from_figi(
        self,
        figi_data: FIGIResult,
        original_id_type: str,
        original_id_value: str,
        exchange: Optional[str],
        instrument_type_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> ResolvedSecurity:
        """Create a new security from OpenFIGI data."""
        cur = self.conn.cursor()

        security_id = str(uuid.uuid4())

        # Determine asset class and RiskPod using normalization
        asset_class, riskpod = self._determine_asset_class(
            security_type=figi_data.security_type,
            market_sector=figi_data.market_sector,
            instrument_type_name=instrument_type_name,
            tenant_id=tenant_id,
        )

        currency = figi_data.currency or "USD"

        # Insert security
        cur.execute("""
            INSERT INTO securities (
                id, figi, name, asset_class, security_type,
                currency, exchange_code, exchange_name,
                data_source, is_active, is_verified, last_enriched_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
        """, (
            security_id,
            figi_data.figi,
            figi_data.name,
            asset_class,
            figi_data.security_type,
            currency,
            figi_data.exch_code or exchange,
            None,  # exchange_name
            "openfigi",
            True,
            True,
        ))

        # Add identifiers
        identifiers_to_add = [
            ("figi", figi_data.figi, figi_data.exch_code, True),
        ]
        if figi_data.ticker:
            identifiers_to_add.append(("ticker", figi_data.ticker, figi_data.exch_code, False))
        if figi_data.composite_figi:
            identifiers_to_add.append(("composite_figi", figi_data.composite_figi, None, False))
        # Add the original identifier that was queried
        identifiers_to_add.append((original_id_type, original_id_value, exchange, False))

        # Commit the security first to ensure it's saved
        self.conn.commit()

        # Now add identifiers (failures here won't lose the security)
        for id_type, id_value, exch, is_primary in identifiers_to_add:
            if id_value:
                try:
                    # Check if identifier already exists
                    cur.execute("""
                        SELECT 1 FROM security_identifiers
                        WHERE identifier_type = %s AND identifier_value = %s
                        AND (exchange_code = %s OR (exchange_code IS NULL AND %s IS NULL))
                    """, (id_type, id_value, exch, exch))

                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO security_identifiers (security_id, identifier_type, identifier_value, exchange_code, is_primary)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (security_id, id_type, id_value, exch, is_primary))
                        self.conn.commit()
                except Exception as e:
                    logger.warning(f"Could not add identifier {id_type}={id_value}: {e}")
                    self.conn.rollback()
        logger.info(f"Created new security: {figi_data.name} (ID: {security_id})")

        return ResolvedSecurity(
            security_id=security_id,
            figi=figi_data.figi,
            name=figi_data.name,
            ticker=figi_data.ticker,
            asset_class=asset_class,
            currency=currency,
            riskpod=riskpod,
            is_new=True,
            enriched=True,
        )

    def _create_placeholder_security(
        self,
        id_type: str,
        id_value: str,
        exchange: Optional[str],
        currency: Optional[str],
        instrument_type_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> ResolvedSecurity:
        """Create a placeholder security when OpenFIGI lookup fails."""
        cur = self.conn.cursor()

        security_id = str(uuid.uuid4())
        name = f"Unknown ({id_type.upper()}: {id_value})"

        # Try normalization if instrument type name provided
        asset_class, riskpod = self._determine_asset_class(
            security_type=None,
            market_sector=None,
            instrument_type_name=instrument_type_name,
            tenant_id=tenant_id,
        )

        cur.execute("""
            INSERT INTO securities (
                id, name, asset_class, currency, exchange_code,
                data_source, is_active, is_verified
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            security_id,
            name,
            asset_class,
            currency or "USD",
            exchange,
            "manual",
            True,
            False,  # Not verified since no FIGI
        ))

        cur.execute("""
            INSERT INTO security_identifiers (security_id, identifier_type, identifier_value, exchange_code, is_primary)
            VALUES (%s, %s, %s, %s, %s)
        """, (security_id, id_type, id_value, exchange, True))

        self.conn.commit()
        logger.warning(f"Created placeholder security: {name}")

        return ResolvedSecurity(
            security_id=security_id,
            figi=None,
            name=name,
            ticker=id_value if id_type == "ticker" else None,
            asset_class=asset_class,
            currency=currency or "USD",
            riskpod=riskpod,
            is_new=True,
            enriched=False,
        )


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def resolve_security(
    db_connection,
    id_type: str,
    id_value: str,
    exchange: Optional[str] = None,
    instrument_type_name: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Optional[ResolvedSecurity]:
    """
    Convenience function to resolve a single security.

    Args:
        db_connection: Database connection
        id_type: Identifier type (ticker, cusip, isin, sedol, figi)
        id_value: The identifier value
        exchange: Exchange code (required for ticker)
        instrument_type_name: Client-provided instrument type for normalization
        tenant_id: Tenant UUID for tenant-specific mappings

    Returns:
        ResolvedSecurity or None
    """
    service = SecurityMasterService(db_connection)
    return service.resolve_identifier(
        id_type, id_value, exchange,
        instrument_type_name=instrument_type_name,
        tenant_id=tenant_id,
    )


# ============================================
# MAIN (for testing)
# ============================================

if __name__ == "__main__":
    import psycopg2

    logging.basicConfig(level=logging.INFO)

    # Connect to local database
    conn = psycopg2.connect("postgresql://postgres:postgres@127.0.0.1:54322/postgres")

    service = SecurityMasterService(conn)

    print("Testing Security Master Service...")
    print()

    # Test 1: Resolve a ticker
    print("1. Resolving AAPL ticker:")
    result = service.resolve_identifier("ticker", "AAPL", exchange="US")
    if result:
        print(f"   Security ID: {result.security_id}")
        print(f"   Name: {result.name}")
        print(f"   FIGI: {result.figi}")
        print(f"   Asset Class: {result.asset_class}")
        print(f"   Is New: {result.is_new}")
    print()

    # Test 2: Resolve MSFT CUSIP
    print("2. Resolving Microsoft by CUSIP (594918104):")
    result = service.resolve_identifier("cusip", "594918104")
    if result:
        print(f"   Security ID: {result.security_id}")
        print(f"   Name: {result.name}")
        print(f"   FIGI: {result.figi}")
        print(f"   Is New: {result.is_new}")
    print()

    # Test 3: Resolve same security by different identifier (should find existing)
    print("3. Resolving Microsoft by ISIN (should find existing):")
    result = service.resolve_identifier("isin", "US5949181045")
    if result:
        print(f"   Security ID: {result.security_id}")
        print(f"   Name: {result.name}")
        print(f"   Is New: {result.is_new}")
        print(f"   Enriched: {result.enriched}")
    print()

    conn.close()
    print("Done!")
