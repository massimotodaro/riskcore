"""
Unit Tests for Instrument Normalization Service

Tests the matching algorithm, tenor extraction, and batch processing.
Most tests run without a database connection (mock-based).
"""

import pytest
import re
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.services.instrument_normalization import (
    InstrumentNormalizationService,
    NormalizationResult,
    MatchMethod,
)


# ============================================
# STANDALONE HELPER FUNCTIONS FOR TESTING
# These mirror the methods in the service class
# ============================================

def normalize_text(value: str) -> str:
    """Normalize text for comparison."""
    if not value:
        return ""
    # Lowercase, strip, collapse whitespace
    return " ".join(value.lower().strip().split())


def extract_tenor(input_value: str) -> str:
    """Extract tenor from instrument name."""
    if not input_value:
        return None

    text = input_value.upper()

    # Direct patterns: 5Y, 10Y, 3M, 30D, 13W
    match = re.search(r'\b(\d+)\s*([YMWD])\b', text)
    if match:
        return f"{match.group(1)}{match.group(2)}"

    # Hyphenated: 5-year, 10-year
    match = re.search(r'\b(\d+)-(?:YEAR|YR|MONTH|MO|DAY|WEEK)', text, re.IGNORECASE)
    if match:
        num = match.group(1)
        unit_match = re.search(r'-(\w+)', match.group(0))
        unit = unit_match.group(1).upper() if unit_match else 'Y'
        if unit.startswith('YEAR') or unit.startswith('YR'):
            return f"{num}Y"
        elif unit.startswith('MONTH') or unit.startswith('MO'):
            return f"{num}M"
        elif unit.startswith('DAY'):
            return f"{num}D"
        elif unit.startswith('WEEK'):
            return f"{num}W"

    # Word numbers: five-year, ten year
    word_to_num = {
        'ONE': '1', 'TWO': '2', 'THREE': '3', 'FOUR': '4', 'FIVE': '5',
        'SIX': '6', 'SEVEN': '7', 'EIGHT': '8', 'NINE': '9', 'TEN': '10',
        'FIFTEEN': '15', 'TWENTY': '20', 'THIRTY': '30',
    }
    for word, num in word_to_num.items():
        if re.search(rf'\b{word}[- ]?YEAR', text, re.IGNORECASE):
            return f"{num}Y"

    return None


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def similarity_ratio(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1.0 - (distance / max_len)


# ============================================
# HELPER FUNCTION TESTS (No DB needed)
# ============================================

class TestNormalizeText:
    """Test text normalization helper."""

    def test_lowercase(self):
        assert normalize_text("CDS") == "cds"

    def test_strips_whitespace(self):
        assert normalize_text("  CDS  ") == "cds"

    def test_collapses_spaces(self):
        assert normalize_text("Credit  Default   Swap") == "credit default swap"

    def test_handles_special_chars(self):
        assert normalize_text("CDS-5Y") == "cds-5y"

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_none_returns_empty(self):
        assert normalize_text(None) == ""


class TestExtractTenor:
    """Test tenor extraction from instrument names."""

    def test_year_format(self):
        assert extract_tenor("CDS 5Y") == "5Y"
        assert extract_tenor("CDS 10Y") == "10Y"
        assert extract_tenor("UST 30Y") == "30Y"

    def test_month_format(self):
        assert extract_tenor("FRA 3M") == "3M"
        assert extract_tenor("SOFR 6M") == "6M"

    def test_day_format(self):
        assert extract_tenor("SOFR 30D") == "30D"

    def test_week_format(self):
        assert extract_tenor("Bill 13W") == "13W"

    def test_year_spelled_out(self):
        assert extract_tenor("CDS five-year") == "5Y"
        assert extract_tenor("ten year treasury") == "10Y"

    def test_year_with_hyphen(self):
        assert extract_tenor("5-year CDS") == "5Y"
        assert extract_tenor("10-year swap") == "10Y"

    def test_no_tenor(self):
        assert extract_tenor("Common Stock") is None
        assert extract_tenor("AAPL") is None

    def test_case_insensitive(self):
        assert extract_tenor("cds 5y") == "5Y"
        assert extract_tenor("CDS 5Y") == "5Y"


class TestLevenshteinDistance:
    """Test Levenshtein distance calculation."""

    def test_identical_strings(self):
        assert levenshtein_distance("cds", "cds") == 0

    def test_single_substitution(self):
        assert levenshtein_distance("cds", "cbs") == 1

    def test_single_insertion(self):
        assert levenshtein_distance("cds", "cdss") == 1

    def test_single_deletion(self):
        assert levenshtein_distance("cdss", "cds") == 1

    def test_multiple_changes(self):
        assert levenshtein_distance("credit", "credti") == 2  # swap ti

    def test_empty_strings(self):
        assert levenshtein_distance("", "") == 0
        assert levenshtein_distance("abc", "") == 3
        assert levenshtein_distance("", "abc") == 3


class TestSimilarityRatio:
    """Test similarity ratio calculation."""

    def test_identical_strings(self):
        assert similarity_ratio("credit default swap", "credit default swap") == 1.0

    def test_completely_different(self):
        assert similarity_ratio("abc", "xyz") < 0.5

    def test_similar_strings(self):
        ratio = similarity_ratio("credit default swap", "credti default swap")
        assert ratio > 0.85  # Should be high despite typo

    def test_empty_strings(self):
        assert similarity_ratio("", "") == 1.0


# ============================================
# NORMALIZATION RESULT TESTS
# ============================================

class TestNormalizationResult:
    """Test NormalizationResult dataclass."""

    def test_success_result(self):
        result = NormalizationResult(
            success=True,
            input_value="CDS 5Y",
            instrument_type_code="CDS",
            canonical_name="Credit Default Swap",
            asset_class="cds",
            riskpod="credit",
            extracted_tenor="5Y",
            confidence=1.0,
            match_method=MatchMethod.EXACT,
        )
        assert result.success is True
        assert result.asset_class == "cds"
        assert result.riskpod == "credit"
        assert result.extracted_tenor == "5Y"

    def test_failed_result(self):
        result = NormalizationResult(
            success=False,
            input_value="Unknown XYZ",
            confidence=0.0,
            match_method=MatchMethod.UNMATCHED,
        )
        assert result.success is False
        assert result.instrument_type_code is None
        assert result.asset_class is None

    def test_to_dict(self):
        result = NormalizationResult(
            success=True,
            input_value="CDS",
            instrument_type_code="CDS",
            canonical_name="Credit Default Swap",
            asset_class="cds",
            riskpod="credit",
            confidence=1.0,
            match_method=MatchMethod.EXACT,
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["success"] is True
        assert d["input_value"] == "CDS"
        assert d["match_method"] == "exact"


# ============================================
# SERVICE TESTS (Require actual DB)
# ============================================

@pytest.mark.skipif(
    os.environ.get("RUN_DB_TESTS") != "1",
    reason="Database tests skipped. Set RUN_DB_TESTS=1 to run."
)
class TestInstrumentNormalizationService:
    """Test the normalization service against actual database."""

    @pytest.fixture
    def db_connection(self):
        """Create actual database connection."""
        import psycopg2
        conn = psycopg2.connect(
            "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        )
        yield conn
        conn.close()

    def test_exact_match_cds(self, db_connection):
        """Test exact match for CDS."""
        service = InstrumentNormalizationService(db_connection)
        result = service.normalize("CDS")
        assert result.success is True
        assert result.instrument_type_code == "CDS"
        assert result.asset_class == "cds"
        assert result.riskpod == "credit"
        assert result.confidence == 1.0
        assert result.match_method == MatchMethod.EXACT

    def test_exact_match_case_insensitive(self, db_connection):
        """Test that matching is case-insensitive."""
        service = InstrumentNormalizationService(db_connection)
        result = service.normalize("cds")
        assert result.success is True
        assert result.instrument_type_code == "CDS"

    def test_exact_match_with_tenor(self, db_connection):
        """Test exact match with tenor extraction."""
        service = InstrumentNormalizationService(db_connection)
        result = service.normalize("CDS 5Y")
        assert result.success is True
        assert result.instrument_type_code == "CDS"
        assert result.extracted_tenor == "5Y"

    def test_exact_match_full_name(self, db_connection):
        """Test exact match on full canonical name."""
        service = InstrumentNormalizationService(db_connection)
        result = service.normalize("Credit Default Swap")
        assert result.success is True
        assert result.instrument_type_code == "CDS"
        assert result.canonical_name == "Credit Default Swap"

    def test_fuzzy_match_typo(self, db_connection):
        """Test fuzzy match handles typos."""
        service = InstrumentNormalizationService(db_connection)
        # "Credti" is a typo for "Credit"
        result = service.normalize("Credti Default Swap")
        # Should match via fuzzy
        assert result.success is True
        assert result.match_method == MatchMethod.FUZZY
        assert result.confidence >= 0.85

    def test_unmatched_queued(self, db_connection):
        """Test that unmatched items are queued for review."""
        service = InstrumentNormalizationService(db_connection)
        result = service.normalize("Unknown XYZ Instrument 12345")
        assert result.success is False
        assert result.match_method == MatchMethod.UNMATCHED
        assert result.confidence == 0.0

    def test_batch_normalize(self, db_connection):
        """Test batch normalization."""
        service = InstrumentNormalizationService(db_connection)
        inputs = ["CDS", "IRS", "Common Stock", "Unknown XYZ"]
        results = service.normalize_batch(inputs)

        assert len(results) == 4
        assert results[0].success is True  # CDS
        assert results[0].instrument_type_code == "CDS"
        assert results[1].success is True  # IRS
        assert results[1].instrument_type_code == "IRS"
        assert results[2].success is True  # Common Stock
        assert results[2].instrument_type_code == "EQUITY"
        assert results[3].success is False  # Unknown


# ============================================
# FILE PARSER INTEGRATION TESTS
# ============================================

class TestFileParserInstrumentType:
    """Test that FileParser detects instrument_type columns."""

    def test_instrument_type_pattern_detection(self):
        """Test that instrument_type patterns are in COLUMN_PATTERNS."""
        from backend.services.file_parser import COLUMN_PATTERNS

        assert "instrument_type" in COLUMN_PATTERNS
        patterns = COLUMN_PATTERNS["instrument_type"]
        assert len(patterns) > 0

        # Test pattern matching
        import re
        test_columns = [
            "instrument_type", "product_type", "security_type",
            "type", "product", "asset_type", "asset_class"
        ]
        for col in test_columns:
            matched = False
            for pattern in patterns:
                if re.match(pattern, col, re.IGNORECASE):
                    matched = True
                    break
            assert matched, f"Column '{col}' should match instrument_type patterns"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
