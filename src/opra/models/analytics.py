"""Generic analytics result contracts.

These structures describe the *shape* of an analytics result only. They define no KPI
identifiers, formulas, denominators, units, rounding, confidence rules or business
interpretation; those belong to the KPI catalogue and the analytics specification.

Rules (decisions D-05, D-06 and D-11):

* A metric value is a :class:`MetricStatus` plus ``value: Decimal | None``.
* ``AVAILABLE`` requires a finite ``Decimal`` (``Decimal("0")`` is a valid measurement).
  ``UNAVAILABLE`` and ``NOT_APPLICABLE`` require ``None``. Inconsistent combinations raise.
* Decimal values must be real ``Decimal`` instances. ``bool``, ``int``, ``float`` and ``str``
  are rejected and never converted, and non-finite values (``NaN``, ``Infinity``) are
  rejected. The stored object is the one supplied: no quantization, rounding or conversion.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import re

from opra.core.exceptions import ModelValidationError
from opra.models.periods import ReportingPeriod


class MetricStatus(Enum):
    """Availability of a metric value."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class MetricValue:
    """Immutable metric value with an explicit status.

    Attributes:
        status: Whether the value is available, unavailable, or not applicable.
        value: A finite ``Decimal`` when ``status`` is ``AVAILABLE``; otherwise ``None``.

    Raises:
        ModelValidationError: If ``status`` is not a ``MetricStatus``, ``value`` is neither
            ``None`` nor a finite ``Decimal`` instance, or the status and value are
            inconsistent.
    """

    status: MetricStatus
    value: Decimal | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, MetricStatus):
            raise ModelValidationError(
                f"status must be a MetricStatus, got {type(self.status).__name__}."
            )
        if self.value is not None:
            if not isinstance(self.value, Decimal):
                raise ModelValidationError(
                    f"value must be a Decimal or None, got {type(self.value).__name__}."
                )
            if not self.value.is_finite():
                raise ModelValidationError("value must be finite.")
        if self.status is MetricStatus.AVAILABLE:
            if self.value is None:
                raise ModelValidationError("value is required when status is AVAILABLE.")
        elif self.value is not None:
            raise ModelValidationError(f"value must be None when status is {self.status.name}.")


@dataclass(frozen=True, slots=True)
class MetricResult:
    """Immutable generic analytics result for one metric over one reporting period.

    Attributes:
        metric_id: Opaque, non-empty identifier. It is kept exactly as given: whitespace is
            preserved and never stripped or normalized. It carries no catalogue semantics.
        metric_value: The metric's status and value.
        period: The reporting period the result refers to.

    Raises:
        ModelValidationError: If ``metric_id`` is not a non-empty, non-whitespace-only
            ``str``, ``metric_value`` is not a ``MetricValue``, or ``period`` is not a
            ``ReportingPeriod``.
    """

    metric_id: str
    metric_value: MetricValue
    period: ReportingPeriod

    def __post_init__(self) -> None:
        if not isinstance(self.metric_id, str):
            raise ModelValidationError(
                f"metric_id must be a string, got {type(self.metric_id).__name__}."
            )
        if not self.metric_id.strip():
            raise ModelValidationError("metric_id must not be empty or whitespace-only.")
        if not isinstance(self.metric_value, MetricValue):
            raise ModelValidationError(
                f"metric_value must be a MetricValue, got {type(self.metric_value).__name__}."
            )
        if not isinstance(self.period, ReportingPeriod):
            raise ModelValidationError(
                f"period must be a ReportingPeriod, got {type(self.period).__name__}."
            )


@dataclass(frozen=True, slots=True)
class AnalysisLimitation:
    """Privacy-safe counted limitation associated with a metric or run."""

    code: str
    count: int
    metric_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or re.fullmatch(r"[A-Z][A-Z0-9_]*", self.code) is None:
            raise ModelValidationError("limitation code must use controlled uppercase characters.")
        if isinstance(self.count, bool) or not isinstance(self.count, int) or self.count < 0:
            raise ModelValidationError("limitation count must be a non-negative integer.")
        if self.metric_id is not None and (
            not isinstance(self.metric_id, str) or not self.metric_id.strip()
        ):
            raise ModelValidationError("metric_id must be None or a non-empty string.")
