"""Tests for immutable UTC reporting periods."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone, tzinfo

import pytest

from opra.core.exceptions import ModelValidationError
from opra.models.periods import ReportingPeriod


class RaisingOffset(tzinfo):
    """Timezone whose offset lookup raises a configured validation exception."""

    def __init__(self, error: type[Exception]) -> None:
        self.error = error

    def utcoffset(self, dt: datetime | None) -> timedelta:
        raise self.error("invalid offset")


class MissingOffset(tzinfo):
    """Timezone without a usable UTC offset."""

    def utcoffset(self, dt: datetime | None) -> None:
        return None


class InvalidOffset(tzinfo):
    """Timezone with an offset outside datetime's valid range."""

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=24)


class OffsetFailsDuringConversion(tzinfo):
    """Timezone that fails when astimezone requests its offset."""

    def __init__(self, error: type[Exception]) -> None:
        self.calls = 0
        self.error = error

    def utcoffset(self, dt: datetime | None) -> timedelta:
        self.calls += 1
        if self.calls > 1:
            raise self.error("offset failed during conversion")
        return timedelta(0)


def timezone_with_offset(hours: int) -> tzinfo:
    """Create a fixed-offset timezone for deterministic tests."""
    return timezone(timedelta(hours=hours))


def test_period_normalizes_boundaries_to_utc() -> None:
    period = ReportingPeriod(
        datetime(2026, 1, 1, 3, tzinfo=UTC),
        datetime(2026, 1, 1, 5, tzinfo=UTC),
    )
    assert period.start_utc.tzinfo is UTC
    assert period.end_utc.tzinfo is UTC

    offset_period = ReportingPeriod(
        datetime(2026, 1, 1, 10, tzinfo=timezone_with_offset(2)),
        datetime(2026, 1, 1, 12, tzinfo=timezone_with_offset(2)),
    )
    assert offset_period.start_utc == datetime(2026, 1, 1, 8, tzinfo=UTC)
    assert offset_period.end_utc == datetime(2026, 1, 1, 10, tzinfo=UTC)


def test_period_uses_half_open_interval_semantics() -> None:
    period = ReportingPeriod(
        datetime(2026, 1, 1, 8, tzinfo=UTC),
        datetime(2026, 1, 1, 10, tzinfo=UTC),
    )
    assert period.contains(datetime(2026, 1, 1, 8, tzinfo=UTC))
    assert period.contains(datetime(2026, 1, 1, 9, tzinfo=UTC))
    assert not period.contains(datetime(2026, 1, 1, 10, tzinfo=UTC))
    assert not period.contains(datetime(2026, 1, 1, 7, tzinfo=UTC))
    assert not period.contains(datetime(2026, 1, 1, 11, tzinfo=UTC))


def test_utc_order_is_used_when_local_clock_order_is_inverted() -> None:
    period = ReportingPeriod(
        datetime(2026, 1, 1, 10, tzinfo=timezone_with_offset(2)),
        datetime(2026, 1, 1, 9, tzinfo=UTC),
    )
    assert period.start_utc == datetime(2026, 1, 1, 8, tzinfo=UTC)
    assert period.end_utc == datetime(2026, 1, 1, 9, tzinfo=UTC)


def test_local_order_does_not_allow_inverted_utc_interval() -> None:
    with pytest.raises(ModelValidationError, match="earlier"):
        ReportingPeriod(
            datetime(2026, 1, 1, 10, tzinfo=UTC),
            datetime(2026, 1, 1, 11, tzinfo=timezone_with_offset(2)),
        )


def test_equal_utc_boundaries_are_rejected_even_with_different_local_times() -> None:
    with pytest.raises(ModelValidationError, match="earlier"):
        ReportingPeriod(
            datetime(2026, 1, 1, 10, tzinfo=timezone_with_offset(2)),
            datetime(2026, 1, 1, 8, tzinfo=UTC),
        )


@pytest.mark.parametrize("value", ["not a datetime", None, 1])
def test_non_datetime_boundaries_and_timestamps_are_rejected(value: object) -> None:
    with pytest.raises(ModelValidationError, match="datetime"):
        ReportingPeriod(value, datetime(2026, 1, 1, 10, tzinfo=UTC))  # type: ignore[arg-type]

    period = ReportingPeriod(
        datetime(2026, 1, 1, 8, tzinfo=UTC),
        datetime(2026, 1, 1, 10, tzinfo=UTC),
    )
    with pytest.raises(ModelValidationError, match="datetime"):
        period.contains(value)  # type: ignore[arg-type]


def test_naive_boundaries_and_timestamps_are_rejected() -> None:
    naive = datetime(2026, 1, 1, 8)
    with pytest.raises(ModelValidationError, match="timezone-aware"):
        ReportingPeriod(naive, datetime(2026, 1, 1, 10, tzinfo=UTC))

    period = ReportingPeriod(
        datetime(2026, 1, 1, 8, tzinfo=UTC),
        datetime(2026, 1, 1, 10, tzinfo=UTC),
    )
    with pytest.raises(ModelValidationError, match="timezone-aware"):
        period.contains(naive)


@pytest.mark.parametrize("error", [ValueError, OverflowError])
def test_offset_lookup_exceptions_are_wrapped(error: type[Exception]) -> None:
    bad_timezone = RaisingOffset(error)
    with pytest.raises(ModelValidationError, match="valid UTC offset"):
        ReportingPeriod(
            datetime(2026, 1, 1, 8, tzinfo=bad_timezone),
            datetime(2026, 1, 1, 10, tzinfo=UTC),
        )


def test_missing_or_invalid_offsets_are_rejected() -> None:
    with pytest.raises(ModelValidationError, match="valid UTC offset"):
        ReportingPeriod(
            datetime(2026, 1, 1, 8, tzinfo=MissingOffset()),
            datetime(2026, 1, 1, 10, tzinfo=UTC),
        )
    with pytest.raises(ModelValidationError, match="valid UTC offset"):
        ReportingPeriod(
            datetime(2026, 1, 1, 8, tzinfo=InvalidOffset()),
            datetime(2026, 1, 1, 10, tzinfo=UTC),
        )


@pytest.mark.parametrize("error", [ValueError, OverflowError])
def test_utc_conversion_exceptions_are_wrapped(error: type[Exception]) -> None:
    with pytest.raises(ModelValidationError, match="normalized to UTC"):
        ReportingPeriod(
            datetime(2026, 1, 1, 8, tzinfo=OffsetFailsDuringConversion(error)),
            datetime(2026, 1, 1, 10, tzinfo=UTC),
        )


def test_period_is_frozen_and_has_slots() -> None:
    period = ReportingPeriod(
        datetime(2026, 1, 1, 8, tzinfo=UTC),
        datetime(2026, 1, 1, 10, tzinfo=UTC),
    )
    with pytest.raises(FrozenInstanceError):
        period.start_utc = datetime(2026, 1, 1, 9, tzinfo=UTC)  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        period.extra = True  # type: ignore[attr-defined]
