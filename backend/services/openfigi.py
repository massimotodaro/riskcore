"""
OpenFIGI API Client for RISKCORE
================================
Direct integration with Bloomberg's OpenFIGI API for security identifier mapping.

OpenFIGI API Documentation: https://www.openfigi.com/api

Supported identifier types:
- TICKER: Stock ticker symbol (requires exchCode or micCode)
- CUSIP: 9-character CUSIP
- ISIN: 12-character ISIN
- SEDOL: 7-character SEDOL
- FIGI: 12-character FIGI (for reverse lookup)
- COMPOSITE_FIGI: Composite FIGI
- ID_BB_GLOBAL: Bloomberg Global ID

Rate limits:
- Without API key: 25 requests/minute, 5 jobs/request
- With API key: 250 requests/minute, 100 jobs/request

Author: RISKCORE Team
Date: 2026-01-11
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import requests
from functools import lru_cache

# Configure logging
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

OPENFIGI_API_URL = "https://api.openfigi.com/v3/mapping"
OPENFIGI_SEARCH_URL = "https://api.openfigi.com/v3/search"

# Rate limiting
DEFAULT_RATE_LIMIT = 25  # requests per minute without API key
API_KEY_RATE_LIMIT = 250  # requests per minute with API key
MAX_JOBS_PER_REQUEST_FREE = 5
MAX_JOBS_PER_REQUEST_API_KEY = 100


class IdType(str, Enum):
    """Supported identifier types for OpenFIGI mapping.

    Note: These must match the exact API values from OpenFIGI.
    See: https://www.openfigi.com/api#post-v3-mapping
    """
    TICKER = "TICKER"
    ID_CUSIP = "ID_CUSIP"
    ID_ISIN = "ID_ISIN"
    ID_SEDOL = "ID_SEDOL"
    ID_WERTPAPIER = "ID_WERTPAPIER"
    ID_BB_UNIQUE = "ID_BB_UNIQUE"
    ID_BB_GLOBAL = "ID_BB_GLOBAL"
    COMPOSITE_FIGI = "COMPOSITE_FIGI"
    SHARE_CLASS_FIGI = "ID_BB_GLOBAL_SHARE_CLASS_LEVEL"

    # Aliases for convenience
    CUSIP = "ID_CUSIP"
    ISIN = "ID_ISIN"
    SEDOL = "ID_SEDOL"
    FIGI = "ID_BB_GLOBAL"


class SecurityType(str, Enum):
    """Security types returned by OpenFIGI."""
    COMMON_STOCK = "Common Stock"
    PREFERRED_STOCK = "Preferred Stock"
    DEPOSITARY_RECEIPT = "Depositary Receipt"
    ETF = "ETP"
    REIT = "REIT"
    BOND = "Bond"
    OPTION = "Option"
    FUTURE = "Future"
    WARRANT = "Warrant"
    INDEX = "Index"


@dataclass
class MappingJob:
    """A single identifier mapping request."""
    id_type: str
    id_value: str
    exch_code: Optional[str] = None
    mic_code: Optional[str] = None
    currency: Optional[str] = None
    market_sector: Optional[str] = None  # 'Equity', 'Corp', 'Govt', etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API request format."""
        job = {
            "idType": self.id_type,
            "idValue": self.id_value,
        }
        if self.exch_code:
            job["exchCode"] = self.exch_code
        if self.mic_code:
            job["micCode"] = self.mic_code
        if self.currency:
            job["currency"] = self.currency
        if self.market_sector:
            job["marketSecDes"] = self.market_sector
        return job


@dataclass
class FIGIResult:
    """Result from OpenFIGI mapping."""
    figi: str
    name: str
    ticker: Optional[str] = None
    exch_code: Optional[str] = None
    composite_figi: Optional[str] = None
    share_class_figi: Optional[str] = None
    security_type: Optional[str] = None
    market_sector: Optional[str] = None
    security_type2: Optional[str] = None
    currency: Optional[str] = None
    mic_code: Optional[str] = None

    # Original query that produced this result
    query_id_type: Optional[str] = None
    query_id_value: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any], query: Optional[MappingJob] = None) -> "FIGIResult":
        """Create from API response data."""
        return cls(
            figi=data.get("figi", ""),
            name=data.get("name", ""),
            ticker=data.get("ticker"),
            exch_code=data.get("exchCode"),
            composite_figi=data.get("compositeFIGI"),
            share_class_figi=data.get("shareClassFIGI"),
            security_type=data.get("securityType"),
            market_sector=data.get("marketSector"),
            security_type2=data.get("securityType2"),
            currency=data.get("currency"),
            mic_code=data.get("micCode"),
            query_id_type=query.id_type if query else None,
            query_id_value=query.id_value if query else None,
        )


@dataclass
class MappingResult:
    """Result container for a mapping request."""
    success: bool
    results: List[FIGIResult] = field(default_factory=list)
    error: Optional[str] = None
    query: Optional[MappingJob] = None


class OpenFIGIError(Exception):
    """Base exception for OpenFIGI errors."""
    pass


class RateLimitError(OpenFIGIError):
    """Rate limit exceeded."""
    pass


class OpenFIGIClient:
    """
    Client for Bloomberg OpenFIGI API.

    Usage:
        client = OpenFIGIClient()

        # Single lookup
        result = client.map_identifier("TICKER", "AAPL", exch_code="US")

        # Batch lookup
        results = client.map_identifiers([
            {"idType": "TICKER", "idValue": "AAPL", "exchCode": "US"},
            {"idType": "CUSIP", "idValue": "037833100"},
            {"idType": "ISIN", "idValue": "US0378331005"},
        ])
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenFIGI client.

        Args:
            api_key: Optional OpenFIGI API key for higher rate limits.
                     Get one free at https://www.openfigi.com/api
        """
        self.api_key = api_key or os.getenv("OPENFIGI_API_KEY")
        self.session = requests.Session()

        # Set up headers
        self.session.headers.update({
            "Content-Type": "application/json",
        })
        if self.api_key:
            self.session.headers["X-OPENFIGI-APIKEY"] = self.api_key

        # Rate limiting
        self._last_request_time = 0.0
        self._request_count = 0
        self._rate_limit = API_KEY_RATE_LIMIT if self.api_key else DEFAULT_RATE_LIMIT
        self._max_jobs = MAX_JOBS_PER_REQUEST_API_KEY if self.api_key else MAX_JOBS_PER_REQUEST_FREE

        logger.info(f"OpenFIGI client initialized (API key: {'Yes' if self.api_key else 'No'}, "
                    f"rate limit: {self._rate_limit}/min, max jobs: {self._max_jobs})")

    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        # Reset counter every minute
        if elapsed >= 60:
            self._request_count = 0
            self._last_request_time = current_time
            return

        # If at limit, wait until minute resets
        if self._request_count >= self._rate_limit:
            wait_time = 60 - elapsed
            logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
            time.sleep(wait_time)
            self._request_count = 0
            self._last_request_time = time.time()

    def _make_request(self, jobs: List[Dict[str, Any]], retries: int = 3) -> List[Dict[str, Any]]:
        """
        Make API request with retry logic.

        Args:
            jobs: List of mapping job dictionaries
            retries: Number of retries on failure

        Returns:
            List of result dictionaries from API
        """
        self._wait_for_rate_limit()

        for attempt in range(retries):
            try:
                response = self.session.post(
                    OPENFIGI_API_URL,
                    json=jobs,
                    timeout=30,
                )

                self._request_count += 1

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited
                    wait_time = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 400:
                    error_msg = response.text
                    logger.error(f"Bad request: {error_msg}")
                    raise OpenFIGIError(f"Bad request: {error_msg}")
                else:
                    logger.warning(f"API error {response.status_code}: {response.text}")
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise OpenFIGIError(f"API error {response.status_code}: {response.text}")

            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise OpenFIGIError(f"Request failed: {e}")

        raise OpenFIGIError("Max retries exceeded")

    def map_identifier(
        self,
        id_type: str,
        id_value: str,
        exch_code: Optional[str] = None,
        mic_code: Optional[str] = None,
        currency: Optional[str] = None,
        market_sector: Optional[str] = None,
    ) -> MappingResult:
        """
        Map a single identifier to FIGI.

        Args:
            id_type: Identifier type (TICKER, CUSIP, ISIN, SEDOL, etc.)
            id_value: The identifier value
            exch_code: Exchange code (required for TICKER)
            mic_code: MIC code (alternative to exch_code)
            currency: Currency filter
            market_sector: Market sector filter (Equity, Corp, Govt, etc.)

        Returns:
            MappingResult with matched securities
        """
        job = MappingJob(
            id_type=id_type,
            id_value=id_value,
            exch_code=exch_code,
            mic_code=mic_code,
            currency=currency,
            market_sector=market_sector,
        )

        results = self.map_jobs([job])
        return results[0] if results else MappingResult(success=False, error="No results")

    def map_jobs(self, jobs: List[MappingJob]) -> List[MappingResult]:
        """
        Map multiple identifiers in batch.

        Args:
            jobs: List of MappingJob objects

        Returns:
            List of MappingResult objects (same order as input)
        """
        if not jobs:
            return []

        all_results = []

        # Process in batches
        for i in range(0, len(jobs), self._max_jobs):
            batch = jobs[i:i + self._max_jobs]
            batch_dicts = [job.to_dict() for job in batch]

            try:
                api_results = self._make_request(batch_dicts)

                # Process results
                for j, result_data in enumerate(api_results):
                    query = batch[j] if j < len(batch) else None

                    if "error" in result_data:
                        all_results.append(MappingResult(
                            success=False,
                            error=result_data["error"],
                            query=query,
                        ))
                    elif "data" in result_data and result_data["data"]:
                        figi_results = [
                            FIGIResult.from_api_response(item, query)
                            for item in result_data["data"]
                        ]
                        all_results.append(MappingResult(
                            success=True,
                            results=figi_results,
                            query=query,
                        ))
                    else:
                        all_results.append(MappingResult(
                            success=False,
                            error="No match found",
                            query=query,
                        ))

            except OpenFIGIError as e:
                # If batch fails, mark all as failed
                for job in batch:
                    all_results.append(MappingResult(
                        success=False,
                        error=str(e),
                        query=job,
                    ))

        return all_results

    def map_identifiers(self, identifiers: List[Dict[str, str]]) -> List[MappingResult]:
        """
        Convenience method to map multiple identifiers from dictionaries.

        Args:
            identifiers: List of dicts with keys: idType, idValue, exchCode (optional), etc.

        Returns:
            List of MappingResult objects
        """
        jobs = [
            MappingJob(
                id_type=id_dict.get("idType", id_dict.get("id_type", "")),
                id_value=id_dict.get("idValue", id_dict.get("id_value", "")),
                exch_code=id_dict.get("exchCode", id_dict.get("exch_code")),
                mic_code=id_dict.get("micCode", id_dict.get("mic_code")),
                currency=id_dict.get("currency"),
                market_sector=id_dict.get("marketSecDes", id_dict.get("market_sector")),
            )
            for id_dict in identifiers
        ]
        return self.map_jobs(jobs)

    def search(self, query: str, limit: int = 10) -> List[FIGIResult]:
        """
        Search for securities by name/description.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of FIGIResult objects
        """
        self._wait_for_rate_limit()

        try:
            response = self.session.post(
                OPENFIGI_SEARCH_URL,
                json={"query": query},
                timeout=30,
            )
            self._request_count += 1

            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("data", [])[:limit]:
                    results.append(FIGIResult.from_api_response(item))
                return results
            else:
                logger.error(f"Search failed: {response.status_code}")
                return []

        except requests.RequestException as e:
            logger.error(f"Search request failed: {e}")
            return []


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

# Global client instance (lazy initialization)
_client: Optional[OpenFIGIClient] = None


def get_client() -> OpenFIGIClient:
    """Get or create the global OpenFIGI client."""
    global _client
    if _client is None:
        _client = OpenFIGIClient()
    return _client


def map_ticker(ticker: str, exchange: str = "US") -> Optional[FIGIResult]:
    """
    Map a ticker symbol to FIGI.

    Args:
        ticker: Stock ticker (e.g., "AAPL")
        exchange: Exchange code (default "US" for US equities)

    Returns:
        FIGIResult or None if not found
    """
    result = get_client().map_identifier("TICKER", ticker, exch_code=exchange)
    if result.success and result.results:
        return result.results[0]
    return None


def map_cusip(cusip: str) -> Optional[FIGIResult]:
    """Map a CUSIP to FIGI."""
    result = get_client().map_identifier("ID_CUSIP", cusip)
    if result.success and result.results:
        return result.results[0]
    return None


def map_isin(isin: str) -> Optional[FIGIResult]:
    """Map an ISIN to FIGI."""
    result = get_client().map_identifier("ID_ISIN", isin)
    if result.success and result.results:
        return result.results[0]
    return None


def map_sedol(sedol: str, exchange: Optional[str] = None) -> Optional[FIGIResult]:
    """Map a SEDOL to FIGI."""
    result = get_client().map_identifier("ID_SEDOL", sedol, exch_code=exchange)
    if result.success and result.results:
        return result.results[0]
    return None


# ============================================
# MAIN (for testing)
# ============================================

if __name__ == "__main__":
    # Test the client
    logging.basicConfig(level=logging.INFO)

    client = OpenFIGIClient()

    print("Testing OpenFIGI client...")
    print()

    # Test single mapping
    print("1. Mapping AAPL ticker:")
    result = client.map_identifier("TICKER", "AAPL", exch_code="US")
    if result.success:
        for r in result.results[:3]:
            print(f"   FIGI: {r.figi}")
            print(f"   Name: {r.name}")
            print(f"   Type: {r.security_type}")
            print()
    else:
        print(f"   Error: {result.error}")

    # Test batch mapping
    print("2. Batch mapping (MSFT ticker, Apple CUSIP, Google ISIN):")
    results = client.map_identifiers([
        {"idType": "TICKER", "idValue": "MSFT", "exchCode": "US"},
        {"idType": "ID_CUSIP", "idValue": "037833100"},  # Apple
        {"idType": "ID_ISIN", "idValue": "US02079K3059"},  # Google/Alphabet
    ])
    for i, result in enumerate(results):
        if result.success and result.results:
            r = result.results[0]
            print(f"   [{i+1}] {r.name}: {r.figi}")
        else:
            print(f"   [{i+1}] Error: {result.error}")

    print()
    print("Done!")
