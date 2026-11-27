"""Immutable period comparison result contract."""

from dataclasses import dataclass
from decimal import Decimal

from opra.core.exceptions import ModelValidationError
from opra.models.analytics import MetricValue
from opra.models.kpis import KPIResult


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Comparison of a KPI with its immediately preceding equal-duration period."""

    current: KPIResult
    baseline: KPIResult | None
    absolute_change: MetricValue
    relative_change: MetricValue
    sample_size: int
    coverage_percent: Decimal | None
    limitation_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.current, KPIResult):
            raise ModelValidationError("current must be a KPIResult.")
        if self.baseline is not None and not isinstance(self.baseline, KPIResult):
            raise ModelValidationError("baseline must be None or a KPIResult.")
        if self.baseline is not None:
            if (self.current.kpi_id, self.current.unit) != (
                self.baseline.kpi_id,
                self.baseline.unit,
            ):
                raise ModelValidationError("current and baseline KPI identity/unit must match.")
            current_period = self.current.period
            baseline_period = self.baseline.period
            current_duration = current_period.end_utc - current_period.start_utc
            baseline_duration = baseline_period.end_utc - baseline_period.start_utc
            if (
                current_duration != baseline_duration
                or baseline_period.end_utc != current_period.start_utc
            ):
                raise ModelValidationError(
                    "baseline must immediately precede current with equal duration."
                )
        if not isinstance(self.absolute_change, MetricValue):
            raise ModelValidationError("absolute_change must be a MetricValue.")
        if not isinstance(self.relative_change, MetricValue):
            raise ModelValidationError("relative_change must be a MetricValue.")
        if (
            isinstance(self.sample_size, bool)
            or not isinstance(self.sample_size, int)
            or self.sample_size < 0
        ):
            raise ModelValidationError("sample_size must be a non-negative integer.")
        if self.coverage_percent is not None and (
            not isinstance(self.coverage_percent, Decimal)
            or not self.coverage_percent.is_finite()
            or not Decimal(0) <= self.coverage_percent <= Decimal(100)
        ):
            raise ModelValidationError("coverage_percent must be None or a Decimal from 0 to 100.")
        if not isinstance(self.limitation_codes, tuple):
            raise ModelValidationError("limitation_codes must be a tuple.")
        if tuple(sorted(set(self.limitation_codes))) != self.limitation_codes:
            raise ModelValidationError("limitation_codes must be unique and sorted.")
