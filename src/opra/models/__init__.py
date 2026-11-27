"""Immutable domain models shared across pipeline stages."""

from opra.models.analytics import AnalysisLimitation, MetricResult, MetricStatus, MetricValue
from opra.models.comparisons import ComparisonResult
from opra.models.intelligence import EvidenceTier, Finding, Recommendation
from opra.models.kpis import KPIResult
from opra.models.records import (
    CanonicalStatus,
    JobRecord,
    JobStatus,
    RawJobRecord,
)
from opra.models.reporting import (
    INTEGRATED_REPORT_SCHEMA_VERSION,
    REPORT_SCHEMA_VERSION,
    IngestionSummary,
    IntegratedReportDocument,
    ReportDocument,
)

__all__ = [
    "INTEGRATED_REPORT_SCHEMA_VERSION",
    "REPORT_SCHEMA_VERSION",
    "AnalysisLimitation",
    "CanonicalStatus",
    "ComparisonResult",
    "EvidenceTier",
    "Finding",
    "IngestionSummary",
    "IntegratedReportDocument",
    "JobRecord",
    "JobStatus",
    "KPIResult",
    "MetricResult",
    "MetricStatus",
    "MetricValue",
    "RawJobRecord",
    "Recommendation",
    "ReportDocument",
]
