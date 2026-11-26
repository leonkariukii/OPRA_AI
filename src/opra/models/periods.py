"""Immutable reporting-period domain model."""

from dataclasses import dataclass
from datetime import datetime, timezone

from opra.core.exceptions import ModelValidationError


def _normalize_utc(value: datetime, field_name: str) -> datetime:
    """Validate an aware datetime and normalize it to UTC."""
    if not isinstance(value, datetime):
        raise ModelValidationError(f"{field_name} must be a datetime.")
    if value.tzinfo is None:
        raise ModelValidationError(f"{field_name} must be timezone-aware.")

    try:
        offset = value.utcoffset()
    except (OverflowError, TypeError, ValueError) as error:
        raise ModelValidationError(f"{field_name} must have a valid UTC offset.") from error
    if offset is None:
        raise ModelValidationError(f"{field_name} must have a valid UTC offset.")

    try:
        return value.astimezone(timezone.utc)
    except (OverflowError, TypeError, ValueError) as error:
        raise ModelValidationError(f"{field_name} could not be normalized to UTC.") from error


@dataclass(frozen=True, slots=True)
class ReportingPeriod:
    """A half-open reporting interval with UTC-normalized boundaries."""

    start_utc: datetime
    end_utc: datetime

    def __post_init__(self) -> None:
        start_utc = _normalize_utc(self.start_utc, "start_utc")
        end_utc = _normalize_utc(self.end_utc, "end_utc")
        if start_utc >= end_utc:
            raise ModelValidationError("start_utc must be earlier than end_utc.")

        object.__setattr__(self, "start_utc", start_utc)
        object.__setattr__(self, "end_utc", end_utc)

    def contains(self, timestamp: datetime) -> bool:
        """Return whether timestamp is in the half-open interval [start_utc, end_utc)."""
        timestamp_utc = _normalize_utc(timestamp, "timestamp")
        return self.start_utc <= timestamp_utc < self.end_utc
