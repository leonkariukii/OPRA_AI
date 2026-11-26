"""Unit tests for ``opra.models.periods`` (decisions D-02 and D-11)."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, date, datetime, timedelta, timezone, tzinfo

import pytest

from opra.core.exceptions import ModelValidationError, OpraError
from opra.models.periods import ReportingPeriod

PLUS_3 = timezone(timedelta(hours=3))
MINUS_5 = timezone(timedelta(hours=-5))
PLUS_14 = timezone(timedelta(hours=14))
MINUS_12 = timezone(timedelta(hours=-12))

START = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
END = datetime(2026, 2, 1, 0, 0, tzinfo=UTC)
MICROSECOND = timedelta(microseconds=1)


class _NoOffset(tzinfo):
    """A tzinfo that reports no UTC offset, so datetimes using it are naive."""

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    def dst(self, dt: datetime | None) -> timedelta | None:
        return None

    def tzname(self, dt: datetime | None) -> str | None:
        return None


class _InvalidOffset(tzinfo):
    """A tzinfo whose offset is outside the range Python accepts (24 hours or more)."""

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return timedelta(hours=25)

    def dst(self, dt: datetime | None) -> timedelta | None:
        return None

    def tzname(self, dt: datetime | None) -> str | None:
        return None


@pytest.fixture
def period() -> ReportingPeriod:
    return ReportingPeriod(start_utc=START, end_utc=END)


# --- valid construction ------------------------------------------------------------------


def test_valid_utc_construction_keeps_values(period: ReportingPeriod) -> None:
    assert period.start_utc == START
    assert period.end_utc == END
    assert period.start_utc.utcoffset() == timedelta(0)
    assert period.end_utc.utcoffset() == timedelta(0)


def test_fields_are_exactly_start_and_end_in_order() -> None:
    assert [f.name for f in fields(ReportingPeriod)] == ["start_utc", "end_utc"]


def test_both_bounds_are_required() -> None:
    with pytest.raises(TypeError):
        ReportingPeriod()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        ReportingPeriod(start_utc=START)  # type: ignore[call-arg]


def test_positional_construction_matches_keyword_construction(period: ReportingPeriod) -> None:
    assert ReportingPeriod(START, END) == period


def test_one_microsecond_period_is_valid() -> None:
    assert ReportingPeriod(START, START + MICROSECOND).end_utc == START + MICROSECOND


@pytest.mark.parametrize(
    ("start", "end", "expected_start", "expected_end"),
    [
        (
            datetime(2026, 1, 1, 3, 0, tzinfo=PLUS_3),
            datetime(2026, 1, 1, 12, 0, tzinfo=PLUS_3),
            datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
            datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
        ),
        (
            datetime(2026, 1, 1, 0, 0, tzinfo=MINUS_5),
            datetime(2026, 1, 1, 10, 0, tzinfo=MINUS_5),
            datetime(2026, 1, 1, 5, 0, tzinfo=UTC),
            datetime(2026, 1, 1, 15, 0, tzinfo=UTC),
        ),
        (
            datetime(2026, 1, 1, 1, 0, tzinfo=PLUS_3),
            datetime(2026, 1, 1, 1, 0, tzinfo=MINUS_5),
            datetime(2025, 12, 31, 22, 0, tzinfo=UTC),
            datetime(2026, 1, 1, 6, 0, tzinfo=UTC),
        ),
    ],
)
def test_aware_non_utc_bounds_are_normalized_to_utc(
    start: datetime, end: datetime, expected_start: datetime, expected_end: datetime
) -> None:
    period = ReportingPeriod(start, end)
    assert period.start_utc == expected_start
    assert period.end_utc == expected_end
    assert period.start_utc.utcoffset() == timedelta(0)
    assert period.end_utc.utcoffset() == timedelta(0)
    assert period.start_utc.tzinfo is UTC
    assert period.end_utc.tzinfo is UTC


def test_normalization_preserves_microseconds() -> None:
    start = datetime(2026, 1, 1, 3, 0, 0, 123456, tzinfo=PLUS_3)
    period = ReportingPeriod(start, start + timedelta(hours=1))
    assert period.start_utc == datetime(2026, 1, 1, 0, 0, 0, 123456, tzinfo=UTC)


def test_normalization_crosses_date_boundaries() -> None:
    start = datetime(2026, 1, 1, 1, 0, tzinfo=PLUS_3)  # 2025-12-31T22:00Z
    period = ReportingPeriod(start, datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
    assert period.start_utc == datetime(2025, 12, 31, 22, 0, tzinfo=UTC)


def test_wall_clock_inverted_but_instants_ordered_is_accepted() -> None:
    # Wall clocks read 10:00 then 09:00, but the instants are 2025-12-31T20:00Z < 21:00Z.
    start = datetime(2026, 1, 1, 10, 0, tzinfo=PLUS_14)
    end = datetime(2026, 1, 1, 9, 0, tzinfo=MINUS_12)
    period = ReportingPeriod(start, end)
    assert period.start_utc == datetime(2025, 12, 31, 20, 0, tzinfo=UTC)
    assert period.end_utc == datetime(2026, 1, 1, 21, 0, tzinfo=UTC)


# --- ordering rejection ------------------------------------------------------------------


def test_equal_bounds_are_rejected() -> None:
    with pytest.raises(ModelValidationError, match="end_utc must be later than start_utc"):
        ReportingPeriod(START, START)


def test_inverted_bounds_are_rejected() -> None:
    with pytest.raises(ModelValidationError, match="end_utc must be later than start_utc"):
        ReportingPeriod(END, START)


def test_end_one_microsecond_before_start_is_rejected() -> None:
    with pytest.raises(ModelValidationError, match="end_utc must be later than start_utc"):
        ReportingPeriod(START, START - MICROSECOND)


def test_bounds_equal_after_utc_normalization_are_rejected() -> None:
    # Wall clocks read 01:00 then 09:00 (locally ordered), but both are 2026-01-01T06:00Z.
    start = datetime(2026, 1, 1, 1, 0, tzinfo=MINUS_5)
    end = datetime(2026, 1, 1, 9, 0, tzinfo=PLUS_3)
    assert start.replace(tzinfo=None) < end.replace(tzinfo=None)
    with pytest.raises(ModelValidationError, match="after UTC normalization"):
        ReportingPeriod(start, end)


def test_bounds_inverted_after_utc_normalization_are_rejected() -> None:
    # Wall clocks read 09:00 then 10:00 (locally ordered), but the instants are
    # 2026-01-01T14:00Z and 2026-01-01T07:00Z.
    start = datetime(2026, 1, 1, 9, 0, tzinfo=MINUS_5)
    end = datetime(2026, 1, 1, 10, 0, tzinfo=PLUS_3)
    assert start.replace(tzinfo=None) < end.replace(tzinfo=None)
    with pytest.raises(ModelValidationError, match="after UTC normalization"):
        ReportingPeriod(start, end)


# --- strict datetime validation ----------------------------------------------------------


def test_naive_start_is_rejected() -> None:
    with pytest.raises(ModelValidationError, match="start_utc must be timezone-aware"):
        ReportingPeriod(datetime(2026, 1, 1), END)


def test_naive_end_is_rejected() -> None:
    with pytest.raises(ModelValidationError, match="end_utc must be timezone-aware"):
        ReportingPeriod(START, datetime(2026, 2, 1))


def test_naive_bounds_are_rejected_even_when_ordered() -> None:
    with pytest.raises(ModelValidationError, match="timezone-aware"):
        ReportingPeriod(datetime(2026, 1, 1), datetime(2026, 2, 1))


def test_tzinfo_without_offset_is_treated_as_naive() -> None:
    naive_like = datetime(2026, 1, 1, tzinfo=_NoOffset())
    with pytest.raises(ModelValidationError, match="start_utc must be timezone-aware"):
        ReportingPeriod(naive_like, END)


@pytest.mark.parametrize(
    "bad",
    [None, "2026-01-01T00:00:00+00:00", 1_767_225_600, 1.5, date(2026, 1, 1), b"x", (START,)],
)
def test_non_datetime_bounds_are_rejected(bad: object) -> None:
    with pytest.raises(
        ModelValidationError, match=f"start_utc must be a datetime, got {type(bad).__name__}"
    ):
        ReportingPeriod(bad, END)  # type: ignore[arg-type]
    with pytest.raises(
        ModelValidationError, match=f"end_utc must be a datetime, got {type(bad).__name__}"
    ):
        ReportingPeriod(START, bad)  # type: ignore[arg-type]


def test_non_datetime_error_does_not_echo_value() -> None:
    with pytest.raises(ModelValidationError) as info:
        ReportingPeriod("secret-looking-value", END)  # type: ignore[arg-type]
    assert "secret-looking-value" not in str(info.value)


def test_start_validation_precedes_end_validation() -> None:
    with pytest.raises(ModelValidationError, match="start_utc must be a datetime"):
        ReportingPeriod(None, None)  # type: ignore[arg-type]


def test_lower_extreme_cannot_be_normalized() -> None:
    # 0001-01-01T00:00+01:00 is before year 1 in UTC.
    too_early = datetime(1, 1, 1, 0, 0, tzinfo=timezone(timedelta(hours=1)))
    with pytest.raises(ModelValidationError, match="start_utc cannot be normalized to UTC"):
        ReportingPeriod(too_early, END)


def test_upper_extreme_cannot_be_normalized() -> None:
    too_late = datetime.max.replace(tzinfo=timezone(timedelta(hours=-1)))
    with pytest.raises(ModelValidationError, match="end_utc cannot be normalized to UTC"):
        ReportingPeriod(START, too_late)


def test_invalid_tzinfo_offset_is_rejected_as_validation_error() -> None:
    with pytest.raises(ModelValidationError, match="start_utc cannot be normalized to UTC"):
        ReportingPeriod(datetime(2026, 1, 1, tzinfo=_InvalidOffset()), END)


def test_validation_errors_are_domain_errors() -> None:
    with pytest.raises(OpraError):
        ReportingPeriod(START, START)


# --- half-open membership ----------------------------------------------------------------


def test_contains_is_inclusive_of_start(period: ReportingPeriod) -> None:
    assert period.contains(START) is True


def test_contains_is_exclusive_of_end(period: ReportingPeriod) -> None:
    assert period.contains(END) is False


def test_contains_one_microsecond_either_side_of_each_bound(period: ReportingPeriod) -> None:
    assert period.contains(START - MICROSECOND) is False
    assert period.contains(START + MICROSECOND) is True
    assert period.contains(END - MICROSECOND) is True
    assert period.contains(END + MICROSECOND) is False


def test_contains_interior_and_exterior(period: ReportingPeriod) -> None:
    assert period.contains(datetime(2026, 1, 15, 12, 0, tzinfo=UTC)) is True
    assert period.contains(datetime(2025, 12, 31, 23, 59, tzinfo=UTC)) is False
    assert period.contains(datetime(2026, 3, 1, tzinfo=UTC)) is False


def test_contains_normalizes_offsets_before_comparing(period: ReportingPeriod) -> None:
    start_in_plus_3 = datetime(2026, 1, 1, 3, 0, tzinfo=PLUS_3)  # == START
    end_in_minus_5 = datetime(2026, 1, 31, 19, 0, tzinfo=MINUS_5)  # == END
    assert period.contains(start_in_plus_3) is True
    assert period.contains(end_in_minus_5) is False
    assert period.contains(end_in_minus_5 - MICROSECOND) is True


def test_contains_uses_instants_not_wall_clock_for_offset_period() -> None:
    offset_period = ReportingPeriod(
        datetime(2026, 1, 1, 3, 0, tzinfo=PLUS_3), datetime(2026, 1, 1, 12, 0, tzinfo=PLUS_3)
    )
    assert offset_period.contains(datetime(2026, 1, 1, 0, 0, tzinfo=UTC)) is True
    assert offset_period.contains(datetime(2026, 1, 1, 9, 0, tzinfo=UTC)) is False
    assert offset_period.contains(datetime(2026, 1, 1, 3, 0, tzinfo=UTC)) is True


def test_contains_rejects_naive_timestamp(period: ReportingPeriod) -> None:
    with pytest.raises(ModelValidationError, match="timestamp must be timezone-aware"):
        period.contains(datetime(2026, 1, 15))


def test_contains_rejects_tzinfo_without_offset(period: ReportingPeriod) -> None:
    with pytest.raises(ModelValidationError, match="timestamp must be timezone-aware"):
        period.contains(datetime(2026, 1, 15, tzinfo=_NoOffset()))


@pytest.mark.parametrize("bad", [None, "2026-01-15T00:00:00+00:00", 5, 1.5, date(2026, 1, 15)])
def test_contains_rejects_non_datetime(period: ReportingPeriod, bad: object) -> None:
    with pytest.raises(ModelValidationError, match="timestamp must be a datetime"):
        period.contains(bad)  # type: ignore[arg-type]


def test_contains_rejects_unconvertible_timestamp(period: ReportingPeriod) -> None:
    with pytest.raises(ModelValidationError, match="timestamp cannot be normalized to UTC"):
        period.contains(datetime(1, 1, 1, 0, 0, tzinfo=timezone(timedelta(hours=1))))


def test_contains_does_not_change_the_period(period: ReportingPeriod) -> None:
    before = (period.start_utc, period.end_utc)
    period.contains(datetime(2026, 1, 15, 3, 0, tzinfo=PLUS_3))
    assert (period.start_utc, period.end_utc) == before


# --- equality and hashing ----------------------------------------------------------------


def test_equal_periods_are_equal_and_hash_equal(period: ReportingPeriod) -> None:
    other = ReportingPeriod(START, END)
    assert period == other
    assert hash(period) == hash(other)


def test_same_instants_in_different_offsets_are_equal_and_hash_equal(
    period: ReportingPeriod,
) -> None:
    other = ReportingPeriod(
        datetime(2026, 1, 1, 3, 0, tzinfo=PLUS_3), datetime(2026, 1, 31, 19, 0, tzinfo=MINUS_5)
    )
    assert other == period
    assert hash(other) == hash(period)
    assert other.start_utc.tzinfo is UTC


def test_different_periods_are_not_equal(period: ReportingPeriod) -> None:
    assert period != ReportingPeriod(START, END + MICROSECOND)
    assert period != ReportingPeriod(START + MICROSECOND, END)


def test_period_is_not_equal_to_other_types(period: ReportingPeriod) -> None:
    assert period != (START, END)
    assert period != object()


def test_periods_are_usable_in_sets_and_as_dict_keys(period: ReportingPeriod) -> None:
    other = ReportingPeriod(START, END)
    assert len({period, other}) == 1
    assert {period: "x"}[other] == "x"


# --- immutability ------------------------------------------------------------------------


def test_period_is_frozen(period: ReportingPeriod) -> None:
    with pytest.raises(FrozenInstanceError):
        period.start_utc = END  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        period.end_utc = START  # type: ignore[misc]
    assert (period.start_utc, period.end_utc) == (START, END)


def test_period_rejects_new_attributes_and_has_no_instance_dict(period: ReportingPeriod) -> None:
    # Python 3.11 raises TypeError and later versions AttributeError for unknown names on
    # frozen slotted dataclasses; both reject the assignment.
    with pytest.raises((AttributeError, TypeError)):
        period.extra = 1  # type: ignore[attr-defined]
    assert not hasattr(period, "__dict__")


def test_replace_revalidates_and_returns_a_new_period(period: ReportingPeriod) -> None:
    moved = replace(period, end_utc=datetime(2026, 3, 1, tzinfo=UTC))
    assert moved.end_utc == datetime(2026, 3, 1, tzinfo=UTC)
    assert period.end_utc == END
    with pytest.raises(ModelValidationError):
        replace(period, end_utc=START)
    with pytest.raises(ModelValidationError):
        replace(period, start_utc=datetime(2026, 1, 1))


def test_stored_bounds_are_immutable_datetimes(period: ReportingPeriod) -> None:
    assert isinstance(period.start_utc, datetime)
    with pytest.raises(AttributeError):
        period.start_utc.year = 2000  # type: ignore[misc]
