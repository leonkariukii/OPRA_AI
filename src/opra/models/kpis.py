"""Immutable KPI result contracts."""

from dataclasses import dataclass
from decimal import Decimal

from opra.core.exceptions import ModelValidationError
from opra.models.analytics import MetricValue
from opra.models.periods import ReportingPeriod


@dataclass(frozen=True, slots=True)
class KPIResult:
    """One KPI value with units, period, denominator, sample and safe limitations."""

    kpi_id: str
    name: str
    unit: str
    metric_value: MetricValue
    period: ReportingPeriod
    numerator: Decimal | None
    denominator: Decimal | None
    sample_size: int
    eligible_count: int
    limitation_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (("kpi_id", self.kpi_id), ("name", self.name), ("unit", self.unit)):
            if not isinstance(value, str) or not value.strip():
                raise ModelValidationError(f"{name} must be a non-empty string.")
        if not isinstance(self.metric_value, MetricValue):
            raise ModelValidationError("metric_value must be a MetricValue.")
        if not isinstance(self.period, ReportingPeriod):
            raise ModelValidationError("period must be a ReportingPeriod.")
        for decimal_name, decimal_value in (
            ("numerator", self.numerator),
            ("denominator", self.denominator),
        ):
            if decimal_value is not None and (
                not isinstance(decimal_value, Decimal) or not decimal_value.is_finite()
            ):
                raise ModelValidationError(f"{decimal_name} must be None or a finite Decimal.")
        count_name: str
        count_value: int
        for count_name, count_value in (
            ("sample_size", self.sample_size),
            ("eligible_count", self.eligible_count),
        ):
            if isinstance(count_value, bool) or not isinstance(count_value, int) or count_value < 0:
                raise ModelValidationError(f"{count_name} must be a non-negative integer.")
        if not isinstance(self.limitation_codes, tuple):
            raise ModelValidationError("limitation_codes must be a tuple.")
        if any(not isinstance(code, str) or not code for code in self.limitation_codes):
            raise ModelValidationError("limitation_codes must contain non-empty strings.")
        if tuple(sorted(set(self.limitation_codes))) != self.limitation_codes:
            raise ModelValidationError("limitation_codes must be unique and sorted.")

    @property
    def coverage_percent(self) -> Decimal | None:
        """Return observed sample coverage without rounding, when a denominator exists."""
        if self.eligible_count == 0:
            return None
        return Decimal(self.sample_size) * Decimal(100) / Decimal(self.eligible_count)

    @property
    def result_id(self) -> str:
        """Return a deterministic identity, including currency for currency-specific KPIs."""
        if self.kpi_id == "KPI-05":
            return f"{self.kpi_id}:{self.unit}"
        return self.kpi_id
