"""Immutable analytics result domain models."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from opra.core.exceptions import ModelValidationError
from opra.models.periods import ReportingPeriod


class MetricStatus(Enum):
    """Availability state for an analytics metric."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class MetricValue:
    """A metric's availability state and optional precision-preserving value."""

    status: MetricStatus
    value: Decimal | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, MetricStatus):
            raise ModelValidationError("status must be a MetricStatus.")

        if self.status is MetricStatus.AVAILABLE:
            if not isinstance(self.value, Decimal):
                raise ModelValidationError("available metrics require a Decimal value.")
            if not self.value.is_finite():
                raise ModelValidationError("available metric values must be finite.")
        elif self.value is not None:
            raise ModelValidationError("unavailable and not-applicable metrics require value=None.")


@dataclass(frozen=True, slots=True)
class MetricResult:
    """A metric value associated with an identifier and reporting period."""

    metric_id: str
    metric_value: MetricValue
    period: ReportingPeriod

    def __post_init__(self) -> None:
        if not isinstance(self.metric_id, str) or not self.metric_id.strip():
            raise ModelValidationError("metric_id must be a non-empty string.")
        if not isinstance(self.metric_value, MetricValue):
            raise ModelValidationError("metric_value must be a MetricValue.")
        if not isinstance(self.period, ReportingPeriod):
            raise ModelValidationError("period must be a ReportingPeriod.")
