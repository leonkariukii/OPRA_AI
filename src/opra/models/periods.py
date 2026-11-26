"""Reporting-period domain model.

A :class:`ReportingPeriod` is a half-open UTC interval ``[start_utc, end_utc)``: a timestamp
``t`` belongs to the period if and only if ``start_utc <= t < end_utc``.

Datetime rules (decisions D-02 and D-11):

* Values must be ``datetime`` instances; other types (including ``date``) are rejected.
* Naive datetimes are rejected; no local timezone is ever assumed.
* Timezone-aware datetimes are normalized to UTC *before* any comparison, so the ordering
  check and the membership check always compare UTC instants.

This module defines no period duration, cohort, comparison-pairing, granularity or
maturity rules.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from opra.core.exceptions import ModelValidationError


def _to_utc(name: str, value: object) -> datetime:
    """Return ``value`` normalized to UTC, or raise :class:`ModelValidationError`.

    Rejects non-``datetime`` values, naive datetimes (including datetimes whose ``tzinfo``
    reports no offset), and datetimes that cannot be represented or converted in UTC.
    """
    if not isinstance(value, datetime):
        raise ModelValidationError(f"{name} must be a datetime, got {type(value).__name__}.")
    try:
        offset = value.utcoffset()
        converted = value.astimezone(UTC) if offset is not None else None
    except (OverflowError, ValueError):
        raise ModelValidationError(f"{name} cannot be normalized to UTC.") from None
    if converted is None:
        raise ModelValidationError(f"{name} must be timezone-aware.")
    return converted


@dataclass(frozen=True, slots=True)
class ReportingPeriod:
    """Immutable half-open UTC reporting interval ``[start_utc, end_utc)``.

    Both bounds are normalized to UTC at construction, so equal instants expressed with
    different offsets produce equal periods. The original offset is not preserved.

    Attributes:
        start_utc: Inclusive lower bound, stored as a UTC-aware datetime.
        end_utc: Exclusive upper bound, stored as a UTC-aware datetime.

    Raises:
        ModelValidationError: If a bound is not a timezone-aware ``datetime``, cannot be
            normalized to UTC, or ``start_utc`` is not strictly earlier than ``end_utc``
            after normalization.
    """

    start_utc: datetime
    end_utc: datetime

    def __post_init__(self) -> None:
        start = _to_utc("start_utc", self.start_utc)
        end = _to_utc("end_utc", self.end_utc)
        if start >= end:
            raise ModelValidationError(
                "end_utc must be later than start_utc after UTC normalization."
            )
        object.__setattr__(self, "start_utc", start)
        object.__setattr__(self, "end_utc", end)

    def contains(self, timestamp: datetime) -> bool:
        """Return whether ``timestamp`` lies in ``[start_utc, end_utc)``.

        ``timestamp`` follows the same rules as the bounds: it must be a timezone-aware
        ``datetime`` and is normalized to UTC before comparison.

        Raises:
            ModelValidationError: If ``timestamp`` is not a timezone-aware ``datetime`` or
                cannot be normalized to UTC.
        """
        timestamp_utc = _to_utc("timestamp", timestamp)
        return self.start_utc <= timestamp_utc < self.end_utc
