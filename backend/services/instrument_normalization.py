"""
Instrument Name Normalization Service

Normalizes varied client instrument names to canonical forms for correct
RiskPod assignment. Handles synonyms, abbreviations, tenor variations,
and inconsistent naming styles.

Example usage:
    service = InstrumentNormalizationService(conn, tenant_id)
    result = service.normalize("CDS 5Y")

    result.asset_class     # 'cds'
    result.riskpod         # 'credit'
    result.extracted_tenor # '5Y'
    result.confidence      # 1.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from enum import Enum
from decimal import Decimal
import re
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class MatchMethod(str, Enum):
    """Method used to match instrument name."""
    EXACT = "exact"
    PREFIX = "prefix"
    FUZZY = "fuzzy"
    PATTERN = "pattern"
    UNMATCHED = "unmatched"
    CACHED = "cached"


@dataclass
class NormalizationResult:
    """Result of instrument name normalization."""
    success: bool
    input_value: str
    instrument_type_code: Optional[str] = None      # 'CDS', 'IRS', etc.
    canonical_name: Optional[str] = None            # 'Credit Default Swap'
    asset_class: Optional[str] = None               # 'cds', 'swap', etc.
    riskpod: Optional[str] = None                   # 'credit', 'rates', etc.
    extracted_tenor: Optional[str] = None           # '5Y', '3M', etc.
    confidence: float = 0.0                         # 0.0 to 1.0
    match_method: MatchMethod = MatchMethod.UNMATCHED
    matched_alias: Optional[str] = None             # What alias matched
    instrument_type_id: Optional[str] = None        # UUID of matched type
    is_cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'success': self.success,
            'input_value': self.input_value,
            'instrument_type_code': self.instrument_type_code,
            'canonical_name': self.canonical_name,
            'asset_class': self.asset_class,
            'riskpod': self.riskpod,
            'extracted_tenor': self.extracted_tenor,
            'confidence': self.confidence,
            'match_method': self.match_method.value,
            'matched_alias': self.matched_alias,
            'is_cached': self.is_cached,
        }


@dataclass
class AliasRecord:
    """Internal representation of an alias mapping."""
    id: str
    instrument_type_id: str
    alias: str
    alias_normalized: str
    match_type: str
    priority: int
    code: str
    canonical_name: str
    asset_class: str
    riskpod: str
    tenant_id: Optional[str] = None


@dataclass
class TenorPattern:
    """Internal representation of a tenor extraction pattern."""
    pattern: str
    tenor_group: int
    unit_group: Optional[int]
    priority: int
    compiled: Any = field(default=None, repr=False)


# Written numbers to numeric mapping
WRITTEN_TO_NUMERIC = {
    'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
    'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
    'eleven': '11', 'twelve': '12', 'fifteen': '15', 'twenty': '20',
    'thirty': '30'
}


class InstrumentNormalizationService:
    """
    Service for normalizing instrument type names to canonical forms.

    Matching priority:
    1. Cache check (if enabled)
    2. Exact match (confidence: 1.0)
    3. Prefix match (confidence: 0.95)
    4. Fuzzy match via Levenshtein (confidence: varies, min 0.85)
    5. Pattern/regex match (confidence: 0.80)
    6. Unmatched → queued for review

    Args:
        conn: psycopg2 database connection
        tenant_id: Optional tenant UUID for tenant-specific overrides
        use_cache: Whether to use normalization cache (default: True)
        min_fuzzy_confidence: Minimum confidence for fuzzy matches (default: 0.85)
        cache_ttl_days: Cache TTL in days (default: 7)
    """

    def __init__(
        self,
        conn: psycopg2.extensions.connection,
        tenant_id: Optional[UUID] = None,
        use_cache: bool = True,
        min_fuzzy_confidence: float = 0.85,
        cache_ttl_days: int = 7,
    ):
        self.conn = conn
        self.tenant_id = str(tenant_id) if tenant_id else None
        self.use_cache = use_cache
        self.min_fuzzy_confidence = min_fuzzy_confidence
        self.cache_ttl_days = cache_ttl_days

        # In-memory data structures for performance
        self._aliases_by_normalized: Dict[str, List[AliasRecord]] = {}
        self._aliases_prefix: List[AliasRecord] = []
        self._aliases_regex: List[AliasRecord] = []
        self._all_aliases: List[AliasRecord] = []
        self._tenor_patterns: List[TenorPattern] = []
        self._instrument_types: Dict[str, Dict] = {}
        self._loaded = False

    def _ensure_loaded(self):
        """Lazy load data from database."""
        if not self._loaded:
            self._load_data()
            self._loaded = True

    def _load_data(self):
        """Load aliases, patterns, and instrument types into memory."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Load instrument types
        try:
            cur.execute("""
                SELECT id, code, canonical_name, asset_class, riskpod,
                       has_tenor, default_tenor
                FROM instrument_types
                WHERE is_active = TRUE
            """)
            for row in cur.fetchall():
                self._instrument_types[str(row['id'])] = dict(row)
        except psycopg2.Error as e:
            logger.warning(f"Could not load instrument_types: {e}")

        # Load aliases (global first, then tenant-specific for override)
        try:
            cur.execute("""
                SELECT ia.id, ia.instrument_type_id, ia.alias, ia.alias_normalized,
                       ia.match_type, ia.priority, ia.tenant_id,
                       it.code, it.canonical_name, it.asset_class, it.riskpod
                FROM instrument_aliases ia
                JOIN instrument_types it ON ia.instrument_type_id = it.id
                WHERE ia.is_active = TRUE AND it.is_active = TRUE
                  AND (ia.tenant_id IS NULL OR ia.tenant_id = %s)
                ORDER BY ia.tenant_id NULLS FIRST, ia.priority DESC
            """, (self.tenant_id,))

            for row in cur.fetchall():
                record = AliasRecord(
                    id=str(row['id']),
                    instrument_type_id=str(row['instrument_type_id']),
                    alias=row['alias'],
                    alias_normalized=row['alias_normalized'],
                    match_type=row['match_type'],
                    priority=row['priority'],
                    code=row['code'],
                    canonical_name=row['canonical_name'],
                    asset_class=row['asset_class'],
                    riskpod=row['riskpod'],
                    tenant_id=str(row['tenant_id']) if row['tenant_id'] else None,
                )

                self._all_aliases.append(record)

                # Index by match type
                if record.match_type == 'exact':
                    if record.alias_normalized not in self._aliases_by_normalized:
                        self._aliases_by_normalized[record.alias_normalized] = []
                    self._aliases_by_normalized[record.alias_normalized].append(record)
                elif record.match_type == 'prefix':
                    self._aliases_prefix.append(record)
                elif record.match_type == 'regex':
                    self._aliases_regex.append(record)
                elif record.match_type == 'contains':
                    # Treat contains as exact for now (can enhance later)
                    if record.alias_normalized not in self._aliases_by_normalized:
                        self._aliases_by_normalized[record.alias_normalized] = []
                    self._aliases_by_normalized[record.alias_normalized].append(record)

            # Sort prefix aliases by length (longest first for best match)
            self._aliases_prefix.sort(key=lambda x: len(x.alias_normalized), reverse=True)

        except psycopg2.Error as e:
            logger.warning(f"Could not load instrument_aliases: {e}")

        # Load tenor patterns
        try:
            cur.execute("""
                SELECT pattern, tenor_group, unit_group, priority
                FROM tenor_patterns
                WHERE is_active = TRUE
                ORDER BY priority DESC
            """)
            for row in cur.fetchall():
                try:
                    compiled = re.compile(row['pattern'], re.IGNORECASE)
                    self._tenor_patterns.append(TenorPattern(
                        pattern=row['pattern'],
                        tenor_group=row['tenor_group'],
                        unit_group=row['unit_group'],
                        priority=row['priority'],
                        compiled=compiled,
                    ))
                except re.error as e:
                    logger.warning(f"Invalid tenor pattern '{row['pattern']}': {e}")
        except psycopg2.Error as e:
            logger.warning(f"Could not load tenor_patterns: {e}")

        logger.info(
            f"Loaded {len(self._instrument_types)} types, "
            f"{len(self._all_aliases)} aliases, "
            f"{len(self._tenor_patterns)} tenor patterns"
        )

    def normalize(self, input_value: str) -> NormalizationResult:
        """
        Normalize an instrument name to canonical form.

        Args:
            input_value: Raw instrument name (e.g., "CDS 5Y", "Interest Rate Swap")

        Returns:
            NormalizationResult with canonical form and metadata
        """
        self._ensure_loaded()

        # Handle empty/null input
        if not input_value or not input_value.strip():
            return NormalizationResult(
                success=False,
                input_value=input_value or "",
                asset_class='other',
                riskpod='other',
                match_method=MatchMethod.UNMATCHED,
            )

        original_input = input_value.strip()
        normalized_input = self._normalize_string(original_input)

        # Step 1: Check cache
        if self.use_cache:
            cached = self._check_cache(normalized_input)
            if cached:
                return cached

        # Step 2: Extract tenor before matching (won't affect match)
        extracted_tenor = self._extract_tenor(original_input)

        # Step 3: Try exact match
        result = self._try_exact_match(original_input, normalized_input)
        if result:
            result.extracted_tenor = extracted_tenor
            self._save_to_cache(normalized_input, result)
            return result

        # Step 4: Try prefix match
        result = self._try_prefix_match(original_input, normalized_input)
        if result:
            result.extracted_tenor = extracted_tenor
            self._save_to_cache(normalized_input, result)
            return result

        # Step 5: Try fuzzy match
        result = self._try_fuzzy_match(original_input, normalized_input)
        if result and result.confidence >= self.min_fuzzy_confidence:
            result.extracted_tenor = extracted_tenor
            self._save_to_cache(normalized_input, result)
            return result

        # Step 6: Try pattern/regex match
        result = self._try_pattern_match(original_input)
        if result:
            result.extracted_tenor = extracted_tenor
            self._save_to_cache(normalized_input, result)
            return result

        # Step 7: No match - queue for review
        self._queue_unmatched(original_input, normalized_input)

        return NormalizationResult(
            success=False,
            input_value=original_input,
            asset_class='other',
            riskpod='other',
            extracted_tenor=extracted_tenor,
            confidence=0.0,
            match_method=MatchMethod.UNMATCHED,
        )

    def normalize_batch(self, values: List[str]) -> List[NormalizationResult]:
        """
        Normalize multiple instrument names.

        Args:
            values: List of raw instrument names

        Returns:
            List of NormalizationResult objects
        """
        return [self.normalize(v) for v in values]

    def _normalize_string(self, s: str) -> str:
        """Normalize string for matching (lowercase, collapse whitespace)."""
        # Lowercase
        normalized = s.lower()
        # Collapse multiple whitespace to single space
        normalized = re.sub(r'\s+', ' ', normalized)
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        return normalized

    def _try_exact_match(
        self, original: str, normalized: str
    ) -> Optional[NormalizationResult]:
        """Try exact match against aliases."""
        if normalized in self._aliases_by_normalized:
            # Get highest priority match (tenant-specific beats global)
            aliases = self._aliases_by_normalized[normalized]
            # Prefer tenant-specific
            for alias in aliases:
                if alias.tenant_id == self.tenant_id:
                    return self._create_result(original, alias, 1.0, MatchMethod.EXACT)
            # Fall back to global
            alias = aliases[0]
            return self._create_result(original, alias, 1.0, MatchMethod.EXACT)
        return None

    def _try_prefix_match(
        self, original: str, normalized: str
    ) -> Optional[NormalizationResult]:
        """Try prefix match against aliases."""
        for alias in self._aliases_prefix:
            if normalized.startswith(alias.alias_normalized):
                # Check tenant specificity
                if alias.tenant_id and alias.tenant_id != self.tenant_id:
                    continue
                return self._create_result(original, alias, 0.95, MatchMethod.PREFIX)
        return None

    def _try_fuzzy_match(
        self, original: str, normalized: str
    ) -> Optional[NormalizationResult]:
        """Try fuzzy match using Levenshtein distance."""
        best_match: Optional[AliasRecord] = None
        best_confidence = 0.0

        # Only check exact-type aliases for fuzzy matching
        for alias_key, alias_list in self._aliases_by_normalized.items():
            distance = self._levenshtein_distance(normalized, alias_key)
            max_len = max(len(normalized), len(alias_key))
            if max_len == 0:
                continue

            # Calculate confidence: 1 - (distance / max_length)
            confidence = 1.0 - (distance / max_len)

            if confidence > best_confidence:
                # Check tenant preference
                alias = alias_list[0]
                for a in alias_list:
                    if a.tenant_id == self.tenant_id:
                        alias = a
                        break
                best_confidence = confidence
                best_match = alias

        if best_match and best_confidence >= self.min_fuzzy_confidence:
            return self._create_result(
                original, best_match, round(best_confidence, 4), MatchMethod.FUZZY
            )
        return None

    def _try_pattern_match(self, original: str) -> Optional[NormalizationResult]:
        """Try regex pattern match against aliases."""
        for alias in self._aliases_regex:
            if alias.tenant_id and alias.tenant_id != self.tenant_id:
                continue
            try:
                if re.search(alias.alias_normalized, original, re.IGNORECASE):
                    return self._create_result(original, alias, 0.80, MatchMethod.PATTERN)
            except re.error:
                continue
        return None

    def _create_result(
        self,
        original: str,
        alias: AliasRecord,
        confidence: float,
        method: MatchMethod
    ) -> NormalizationResult:
        """Create a NormalizationResult from an alias match."""
        return NormalizationResult(
            success=True,
            input_value=original,
            instrument_type_code=alias.code,
            canonical_name=alias.canonical_name,
            asset_class=alias.asset_class,
            riskpod=alias.riskpod,
            confidence=confidence,
            match_method=method,
            matched_alias=alias.alias,
            instrument_type_id=alias.instrument_type_id,
        )

    def _extract_tenor(self, input_value: str) -> Optional[str]:
        """
        Extract tenor from instrument name.

        Examples:
            "CDS 5Y" -> "5Y"
            "IRS 10 Year" -> "10Y"
            "CDS five-year tenor" -> "5Y"
            "FRA 3M" -> "3M"
        """
        for pattern in self._tenor_patterns:
            if pattern.compiled is None:
                continue
            try:
                match = pattern.compiled.search(input_value)
                if match:
                    tenor_raw = match.group(pattern.tenor_group)

                    # Convert written numbers to numeric
                    tenor_lower = tenor_raw.lower()
                    if tenor_lower in WRITTEN_TO_NUMERIC:
                        tenor_raw = WRITTEN_TO_NUMERIC[tenor_lower]

                    # Get unit if separate capture group
                    unit = None
                    if pattern.unit_group:
                        try:
                            unit = match.group(pattern.unit_group).upper()
                        except (IndexError, AttributeError):
                            pass

                    return self._normalize_tenor(tenor_raw, unit)
            except (re.error, IndexError, AttributeError):
                continue

        return None

    def _normalize_tenor(self, tenor: str, unit: Optional[str] = None) -> str:
        """
        Normalize tenor to standard format (e.g., '5Y', '3M').

        Args:
            tenor: Raw tenor value (e.g., '5', 'five')
            unit: Optional unit (Y, M, D, W)

        Returns:
            Normalized tenor string
        """
        tenor = str(tenor).strip().upper()

        # Already in good format (e.g., "5Y", "3M")
        if re.match(r'^\d+[YMDW]$', tenor):
            return tenor

        # Try to parse number + unit from single string
        match = re.match(r'^(\d+)\s*([YMDW])', tenor, re.IGNORECASE)
        if match:
            return f"{match.group(1)}{match.group(2).upper()}"

        # If we have separate unit
        if unit and re.match(r'^\d+$', tenor):
            return f"{tenor}{unit}"

        # Try extracting just the number if it looks like "5-year" etc
        match = re.match(r'^(\d+)', tenor)
        if match:
            num = match.group(1)
            # Guess unit based on common conventions
            if 'Y' in tenor.upper() or 'YEAR' in tenor.upper():
                return f"{num}Y"
            elif 'M' in tenor.upper() or 'MONTH' in tenor.upper():
                return f"{num}M"
            elif 'D' in tenor.upper() or 'DAY' in tenor.upper():
                return f"{num}D"
            elif 'W' in tenor.upper() or 'WEEK' in tenor.upper():
                return f"{num}W"
            # Default to years for finance conventions
            return f"{num}Y"

        return tenor

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein (edit) distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _check_cache(self, normalized_input: str) -> Optional[NormalizationResult]:
        """Check normalization cache for previous result."""
        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT input_value, instrument_type_id, asset_class, riskpod,
                       extracted_tenor, confidence_score, match_method
                FROM instrument_normalization_cache
                WHERE input_normalized = %s
                  AND (tenant_id IS NULL OR tenant_id = %s)
                  AND expires_at > NOW()
                ORDER BY tenant_id NULLS LAST
                LIMIT 1
            """, (normalized_input, self.tenant_id))

            row = cur.fetchone()
            if row:
                # Look up instrument type details
                type_info = self._instrument_types.get(str(row['instrument_type_id']))

                return NormalizationResult(
                    success=True,
                    input_value=row['input_value'],
                    instrument_type_code=type_info['code'] if type_info else None,
                    canonical_name=type_info['canonical_name'] if type_info else None,
                    asset_class=row['asset_class'],
                    riskpod=row['riskpod'],
                    extracted_tenor=row['extracted_tenor'],
                    confidence=float(row['confidence_score']) if row['confidence_score'] else 0.0,
                    match_method=MatchMethod.CACHED,
                    is_cached=True,
                    instrument_type_id=str(row['instrument_type_id']) if row['instrument_type_id'] else None,
                )
        except psycopg2.Error as e:
            logger.debug(f"Cache check failed: {e}")

        return None

    def _save_to_cache(self, normalized_input: str, result: NormalizationResult):
        """Save normalization result to cache."""
        if not result.success:
            return

        try:
            cur = self.conn.cursor()
            cur.execute(f"""
                INSERT INTO instrument_normalization_cache (
                    tenant_id, input_value, input_normalized, instrument_type_id,
                    asset_class, riskpod, extracted_tenor, confidence_score, match_method,
                    expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() + INTERVAL '{self.cache_ttl_days} days')
                ON CONFLICT (tenant_id, input_normalized) DO UPDATE SET
                    instrument_type_id = EXCLUDED.instrument_type_id,
                    asset_class = EXCLUDED.asset_class,
                    riskpod = EXCLUDED.riskpod,
                    extracted_tenor = EXCLUDED.extracted_tenor,
                    confidence_score = EXCLUDED.confidence_score,
                    match_method = EXCLUDED.match_method,
                    expires_at = NOW() + INTERVAL '{self.cache_ttl_days} days'
            """, (
                self.tenant_id,
                result.input_value,
                normalized_input,
                result.instrument_type_id,
                result.asset_class,
                result.riskpod,
                result.extracted_tenor,
                result.confidence,
                result.match_method.value,
            ))
            self.conn.commit()
        except psycopg2.Error as e:
            logger.debug(f"Cache save failed: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass

    def _queue_unmatched(self, original: str, normalized: str):
        """Queue unmatched instrument for manual review."""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO unmatched_instruments (tenant_id, input_value, input_normalized, status)
                VALUES (%s, %s, %s, 'pending')
                ON CONFLICT (tenant_id, input_value) DO UPDATE SET
                    occurrence_count = unmatched_instruments.occurrence_count + 1,
                    updated_at = NOW()
            """, (self.tenant_id, original, normalized))
            self.conn.commit()
        except psycopg2.Error as e:
            logger.debug(f"Queue unmatched failed: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass

    # =========================================================================
    # Alias Management Methods
    # =========================================================================

    def add_alias(
        self,
        instrument_type_code: str,
        alias: str,
        match_type: str = 'exact',
        priority: int = 100,
        tenant_specific: bool = False,
        created_by: Optional[str] = None,
    ) -> bool:
        """
        Add a new alias mapping.

        Args:
            instrument_type_code: Code of the instrument type (e.g., 'CDS')
            alias: The alias to add
            match_type: 'exact', 'prefix', 'contains', or 'regex'
            priority: Priority (higher = preferred)
            tenant_specific: If True, alias is tenant-specific
            created_by: UUID of user creating the alias

        Returns:
            True if alias was added successfully
        """
        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # Get instrument type ID
            cur.execute(
                "SELECT id FROM instrument_types WHERE code = %s AND is_active = TRUE",
                (instrument_type_code,)
            )
            row = cur.fetchone()
            if not row:
                logger.error(f"Unknown instrument type: {instrument_type_code}")
                return False

            type_id = row['id']
            normalized = self._normalize_string(alias)
            tenant_id = self.tenant_id if tenant_specific else None

            cur.execute("""
                INSERT INTO instrument_aliases (
                    instrument_type_id, alias, alias_normalized, match_type,
                    priority, tenant_id, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (alias_normalized, tenant_id) DO UPDATE SET
                    instrument_type_id = EXCLUDED.instrument_type_id,
                    match_type = EXCLUDED.match_type,
                    priority = EXCLUDED.priority
            """, (type_id, alias, normalized, match_type, priority, tenant_id, created_by))

            self.conn.commit()

            # Reload data to include new alias
            self._loaded = False

            return True

        except psycopg2.Error as e:
            logger.error(f"Failed to add alias: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return False

    def resolve_unmatched(
        self,
        unmatched_id: str,
        instrument_type_code: str,
        create_alias: bool = True,
        reviewed_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Resolve an unmatched instrument by assigning a type.

        Args:
            unmatched_id: UUID of the unmatched instrument
            instrument_type_code: Code to assign (e.g., 'CDS')
            create_alias: If True, create an alias for future matching
            reviewed_by: UUID of reviewing user
            notes: Resolution notes

        Returns:
            True if resolved successfully
        """
        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # Get unmatched record
            cur.execute(
                "SELECT input_value FROM unmatched_instruments WHERE id = %s",
                (unmatched_id,)
            )
            row = cur.fetchone()
            if not row:
                logger.error(f"Unmatched record not found: {unmatched_id}")
                return False

            input_value = row['input_value']

            # Create alias if requested
            if create_alias:
                self.add_alias(
                    instrument_type_code=instrument_type_code,
                    alias=input_value,
                    match_type='exact',
                    priority=90,  # Slightly lower than seed data
                    tenant_specific=True,
                    created_by=reviewed_by,
                )

            # Update unmatched record
            cur.execute("""
                UPDATE unmatched_instruments
                SET status = 'mapped',
                    reviewed_by = %s,
                    reviewed_at = NOW(),
                    resolution_notes = %s
                WHERE id = %s
            """, (reviewed_by, notes, unmatched_id))

            self.conn.commit()
            return True

        except psycopg2.Error as e:
            logger.error(f"Failed to resolve unmatched: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return False

    def get_unmatched(
        self,
        status: str = 'pending',
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """
        Get list of unmatched instruments.

        Args:
            status: Filter by status ('pending', 'mapped', 'ignored', 'escalated')
            limit: Maximum records to return
            offset: Offset for pagination

        Returns:
            List of unmatched instrument records
        """
        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT id, input_value, occurrence_count, status,
                       created_at, updated_at
                FROM unmatched_instruments
                WHERE (tenant_id IS NULL OR tenant_id = %s)
                  AND status = %s
                ORDER BY occurrence_count DESC, created_at DESC
                LIMIT %s OFFSET %s
            """, (self.tenant_id, status, limit, offset))

            return [dict(row) for row in cur.fetchall()]

        except psycopg2.Error as e:
            logger.error(f"Failed to get unmatched: {e}")
            return []

    def get_instrument_types(self) -> List[Dict]:
        """Get all canonical instrument types."""
        self._ensure_loaded()
        return list(self._instrument_types.values())

    def get_aliases(
        self,
        instrument_type_code: Optional[str] = None,
        include_global: bool = True,
    ) -> List[Dict]:
        """
        Get aliases, optionally filtered by instrument type.

        Args:
            instrument_type_code: Filter by type code
            include_global: Include global (non-tenant-specific) aliases

        Returns:
            List of alias records
        """
        self._ensure_loaded()

        results = []
        for alias in self._all_aliases:
            # Filter by type
            if instrument_type_code and alias.code != instrument_type_code:
                continue

            # Filter by scope
            if not include_global and alias.tenant_id is None:
                continue

            results.append({
                'id': alias.id,
                'alias': alias.alias,
                'match_type': alias.match_type,
                'priority': alias.priority,
                'instrument_type_code': alias.code,
                'canonical_name': alias.canonical_name,
                'asset_class': alias.asset_class,
                'riskpod': alias.riskpod,
                'is_global': alias.tenant_id is None,
            })

        return results
