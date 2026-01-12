# RISKCORE Backend Services

from .openfigi import (
    OpenFIGIClient,
    FIGIResult,
    MappingResult,
    get_client,
    map_ticker,
    map_cusip,
    map_isin,
    map_sedol,
)

from .security_master import (
    SecurityMasterService,
    ResolvedSecurity,
    resolve_security,
)

from .validation import (
    DataValidator,
    ValidationResult,
    ValidationSummary,
    ValidationRule,
    Severity,
    RuleType,
    create_validator,
)

from .risk_engine import (
    RiskEngine,
    VaRMethod,
    RiskMetricType,
    MetricLevel,
)

from .exposures import (
    ExposureService,
    ExposureDimension,
)

from .greeks import (
    GreeksService,
    OptionType,
)

from .netting import (
    NettingService,
    NetPosition,
)

from .overlap import (
    OverlapDetectionService,
    PositionOverlap,
    OverlapType,
    OverlapSeverity,
)

from .aggregation import (
    AggregationService,
    HierarchyNode,
)

from .riskpod import (
    RiskPodService,
    RiskPod,
    RiskPodSummary,
    get_riskpod,
    get_pod_metrics,
    ASSET_CLASS_TO_POD,
    POD_RISK_METRICS,
)

from .correlation import (
    CorrelationService,
    FirmVaRResult,
    get_correlation,
    build_correlation_matrix,
    DEFAULT_CORRELATIONS,
    CRISIS_CORRELATIONS,
)

from .returns import (
    ReturnsService,
    ReturnWindow,
    DailyReturn,
    ReturnSeries,
)

from .realized_correlation import (
    RealizedCorrelationService,
    CorrelationEntityType,
    CorrelationType,
    CorrelationResult,
    PMCorrelationMatrix,
    calculate_pearson_correlation,
)

from .google_sheets import (
    GoogleSheetsService,
    get_sheets_service,
)

__all__ = [
    # OpenFIGI
    "OpenFIGIClient",
    "FIGIResult",
    "MappingResult",
    "get_client",
    "map_ticker",
    "map_cusip",
    "map_isin",
    "map_sedol",
    # Security Master
    "SecurityMasterService",
    "ResolvedSecurity",
    "resolve_security",
    # Validation
    "DataValidator",
    "ValidationResult",
    "ValidationSummary",
    "ValidationRule",
    "Severity",
    "RuleType",
    "create_validator",
    # Risk Engine
    "RiskEngine",
    "VaRMethod",
    "RiskMetricType",
    "MetricLevel",
    # Exposures
    "ExposureService",
    "ExposureDimension",
    # Greeks
    "GreeksService",
    "OptionType",
    # Netting
    "NettingService",
    "NetPosition",
    # Overlap Detection
    "OverlapDetectionService",
    "PositionOverlap",
    "OverlapType",
    "OverlapSeverity",
    # Aggregation
    "AggregationService",
    "HierarchyNode",
    # RiskPod
    "RiskPodService",
    "RiskPod",
    "RiskPodSummary",
    "get_riskpod",
    "get_pod_metrics",
    "ASSET_CLASS_TO_POD",
    "POD_RISK_METRICS",
    # Correlation (Pod-level)
    "CorrelationService",
    "FirmVaRResult",
    "get_correlation",
    "build_correlation_matrix",
    "DEFAULT_CORRELATIONS",
    "CRISIS_CORRELATIONS",
    # Returns
    "ReturnsService",
    "ReturnWindow",
    "DailyReturn",
    "ReturnSeries",
    # Realized Correlation
    "RealizedCorrelationService",
    "CorrelationEntityType",
    "CorrelationType",
    "CorrelationResult",
    "PMCorrelationMatrix",
    "calculate_pearson_correlation",
    # Google Sheets
    "GoogleSheetsService",
    "get_sheets_service",
]
