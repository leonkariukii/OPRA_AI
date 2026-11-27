"""Immutable report document for generic metric results."""

from dataclasses import dataclass
from datetime import UTC, datetime

from opra.core.config import ConfigSnapshot
from opra.core.exceptions import ModelValidationError
from opra.models.analytics import AnalysisLimitation, MetricResult
from opra.models.comparisons import ComparisonResult
from opra.models.intelligence import Finding, Recommendation
from opra.models.kpis import KPIResult
from opra.models.periods import ReportingPeriod

REPORT_SCHEMA_VERSION = "1.0.0"
INTEGRATED_REPORT_SCHEMA_VERSION = "1.1.0"


@dataclass(frozen=True, slots=True)
class ReportDocument:
    """Caller-timestamped report input; contains no KPI or recommendation logic."""

    generated_at_utc: datetime
    engine_version: str
    config: ConfigSnapshot
    metrics: tuple[MetricResult, ...]
    schema_version: str = REPORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at_utc, datetime):
            raise ModelValidationError("generated_at_utc must be a datetime.")
        try:
            offset = self.generated_at_utc.utcoffset()
            normalized = self.generated_at_utc.astimezone(UTC) if offset is not None else None
        except (OverflowError, ValueError):
            raise ModelValidationError("generated_at_utc cannot be normalized to UTC.") from None
        if normalized is None:
            raise ModelValidationError("generated_at_utc must have an explicit UTC offset.")
        object.__setattr__(self, "generated_at_utc", normalized)
        if not isinstance(self.engine_version, str) or not self.engine_version.strip():
            raise ModelValidationError("engine_version must be a non-empty string.")
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise ModelValidationError("schema_version must be a non-empty string.")
        if self.schema_version != REPORT_SCHEMA_VERSION:
            raise ModelValidationError(
                f"schema_version is unsupported; supported version is {REPORT_SCHEMA_VERSION}."
            )
        if not isinstance(self.config, ConfigSnapshot):
            raise ModelValidationError("config must be a ConfigSnapshot.")
        if not isinstance(self.metrics, tuple):
            raise ModelValidationError("metrics must be a tuple.")
        if any(not isinstance(metric, MetricResult) for metric in self.metrics):
            raise ModelValidationError("metrics must contain only MetricResult values.")


@dataclass(frozen=True, slots=True)
class IngestionSummary:
    """Privacy-safe record outcome counts for one CSV invocation."""

    dataset_status: str
    total_processed_record_count: int
    accepted_record_count: int
    rejected_record_count: int
    exact_duplicate_count: int
    conflicting_duplicate_count: int
    quarantined_record_count: int

    def __post_init__(self) -> None:
        if self.dataset_status not in {"success", "failure"}:
            raise ModelValidationError("dataset_status must be success or failure.")
        values = (
            self.total_processed_record_count,
            self.accepted_record_count,
            self.rejected_record_count,
            self.exact_duplicate_count,
            self.conflicting_duplicate_count,
            self.quarantined_record_count,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values
        ):
            raise ModelValidationError("ingestion summary counts must be non-negative integers.")
        if (
            self.accepted_record_count + self.rejected_record_count
            != self.total_processed_record_count
        ):
            raise ModelValidationError(
                "accepted and rejected counts must reconcile to total processed."
            )


@dataclass(frozen=True, slots=True)
class IntegratedReportDocument:
    """Immutable v1.1 integrated output for an analytics execution."""

    generated_at_utc: datetime
    reference_utc_timestamp: datetime
    engine_version: str
    config: ConfigSnapshot
    ingestion: IngestionSummary
    current_period: ReportingPeriod
    baseline_period: ReportingPeriod | None
    metrics: tuple[KPIResult, ...]
    comparisons: tuple[ComparisonResult, ...]
    findings: tuple[Finding, ...]
    recommendations: tuple[Recommendation, ...]
    limitations: tuple[AnalysisLimitation, ...] = ()
    schema_version: str = INTEGRATED_REPORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("generated_at_utc", "reference_utc_timestamp"):
            value = getattr(self, name)
            if not isinstance(value, datetime) or value.utcoffset() is None:
                raise ModelValidationError(f"{name} must be timezone-aware.")
            object.__setattr__(self, name, value.astimezone(UTC))
        if not isinstance(self.engine_version, str) or not self.engine_version.strip():
            raise ModelValidationError("engine_version must be a non-empty string.")
        if self.schema_version != INTEGRATED_REPORT_SCHEMA_VERSION:
            raise ModelValidationError("schema_version is unsupported; supported version is 1.1.0.")
        if not isinstance(self.config, ConfigSnapshot) or not isinstance(
            self.ingestion, IngestionSummary
        ):
            raise ModelValidationError("config and ingestion must use their report contracts.")
        if not isinstance(self.current_period, ReportingPeriod) or (
            self.baseline_period is not None
            and not isinstance(self.baseline_period, ReportingPeriod)
        ):
            raise ModelValidationError("periods must use ReportingPeriod.")
        expected = (
            ("metrics", KPIResult),
            ("comparisons", ComparisonResult),
            ("findings", Finding),
            ("recommendations", Recommendation),
        )
        for name, item_type in expected:
            values = getattr(self, name)
            if not isinstance(values, tuple) or any(
                not isinstance(value, item_type) for value in values
            ):
                raise ModelValidationError(
                    f"{name} must be a tuple of {item_type.__name__} values."
                )
        if not isinstance(self.limitations, tuple) or any(
            not isinstance(item, AnalysisLimitation) for item in self.limitations
        ):
            raise ModelValidationError("limitations must be a tuple of AnalysisLimitation values.")
