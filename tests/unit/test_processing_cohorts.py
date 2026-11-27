"""Tests for deterministic processing cohort assignment."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from opra.core.exceptions import ModelValidationError
from opra.models.periods import ReportingPeriod
from opra.models.records import JobRecord, JobStatus
from opra.processing.cohorts import ProcessingCohorts, assign_cohorts

PERIOD = ReportingPeriod(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 2, 1, tzinfo=UTC))


def _record(
    job_id: str,
    status: JobStatus,
    opened_at: datetime,
    completed_at: datetime | None = None,
) -> JobRecord:
    return JobRecord(job_id, status, opened_at, completed_at)


def test_intake_uses_opened_at_for_each_status() -> None:
    start = PERIOD.start_utc
    inside = datetime(2026, 1, 15, tzinfo=UTC)
    records = (
        _record("done", JobStatus.COMPLETED, inside, datetime(2026, 2, 2, tzinfo=UTC)),
        _record("cancel", JobStatus.CANCELLED, inside),
        _record("progress", JobStatus.IN_PROGRESS, inside),
        _record("before", JobStatus.COMPLETED, datetime(2025, 12, 31, tzinfo=UTC), inside),
        _record("start", JobStatus.IN_PROGRESS, start),
    )
    result = assign_cohorts(records, PERIOD)
    assert [record.job_id for record in result.intake] == ["done", "cancel", "progress", "start"]
    assert [record.job_id for record in result.completion] == ["before"]
    assert [record.job_id for record in result.turnaround] == ["before"]


def test_completion_and_turnaround_require_completed_status_and_timestamp() -> None:
    inside = datetime(2026, 1, 10, tzinfo=UTC)
    records = (
        _record("completed", JobStatus.COMPLETED, inside, inside),
        _record("no-time", JobStatus.COMPLETED, inside),
        _record("cancelled", JobStatus.CANCELLED, inside, inside),
        _record("in-progress", JobStatus.IN_PROGRESS, inside, inside),
    )
    result = assign_cohorts(records, PERIOD)
    assert [record.job_id for record in result.completion] == ["completed"]
    assert result.turnaround == result.completion


def test_turnaround_cohort_retains_negative_durations_without_reordering() -> None:
    opened = datetime(2026, 1, 10, tzinfo=UTC)
    records = (
        _record("negative", JobStatus.COMPLETED, opened, datetime(2026, 1, 9, tzinfo=UTC)),
        _record("positive", JobStatus.COMPLETED, opened, datetime(2026, 1, 11, tzinfo=UTC)),
        _record("zero", JobStatus.COMPLETED, opened, opened),
    )

    result = assign_cohorts(records, PERIOD)

    assert result.completion == records
    assert result.turnaround == records
    assert isinstance(result.turnaround, tuple)


def test_period_membership_is_start_inclusive_and_end_exclusive() -> None:
    start = PERIOD.start_utc
    end = PERIOD.end_utc
    records = (
        _record("at-start", JobStatus.COMPLETED, start, start),
        _record("at-end", JobStatus.COMPLETED, end, end),
    )
    result = assign_cohorts(records, PERIOD)
    assert [record.job_id for record in result.intake] == ["at-start"]
    assert [record.job_id for record in result.completion] == ["at-start"]


def test_period_cohorts_overlap_and_preserve_input_order() -> None:
    opened = datetime(2026, 1, 5, tzinfo=UTC)
    completed = datetime(2026, 1, 20, tzinfo=UTC)
    records = (
        _record("second", JobStatus.COMPLETED, opened, completed),
        _record("first", JobStatus.COMPLETED, opened, completed),
    )
    result = assign_cohorts(records, PERIOD)
    assert [item.job_id for item in result.intake] == ["second", "first"]
    assert [item.job_id for item in result.completion] == ["second", "first"]
    assert [item.job_id for item in result.turnaround] == ["second", "first"]


@pytest.mark.parametrize(
    ("records", "period", "message"),
    [
        ([], PERIOD, "records must be a tuple"),
        ((object(),), PERIOD, "records must contain only JobRecord"),
        ((), object(), "period must be a ReportingPeriod"),
    ],
)
def test_assignment_rejects_invalid_inputs(records: object, period: object, message: str) -> None:
    with pytest.raises(ModelValidationError, match=message):
        assign_cohorts(records, period)  # type: ignore[arg-type]


def test_cohort_result_requires_tuple_collections_and_records() -> None:
    record = _record("one", JobStatus.IN_PROGRESS, PERIOD.start_utc)
    with pytest.raises(ModelValidationError, match="intake must be a tuple"):
        ProcessingCohorts([], (), ())  # type: ignore[arg-type]
    with pytest.raises(ModelValidationError, match="completion must contain only JobRecord"):
        ProcessingCohorts((), (object(),), ())  # type: ignore[arg-type]
    result = ProcessingCohorts((record,), (), ())
    with pytest.raises(FrozenInstanceError):
        result.intake = ()  # type: ignore[misc]
    assert result.intake == (record,)


def test_assignment_is_repeatable_and_does_not_mutate_records() -> None:
    record = _record(
        "one",
        JobStatus.COMPLETED,
        datetime(2026, 1, 2, tzinfo=UTC),
        datetime(2026, 1, 3, tzinfo=UTC),
    )
    before = (record.job_id, record.status, record.opened_at, record.completed_at)
    first = assign_cohorts((record,), PERIOD)
    second = assign_cohorts((record,), PERIOD)
    assert first == second
    assert (record.job_id, record.status, record.opened_at, record.completed_at) == before


def test_assignments_do_not_use_maturity_buffer_or_financial_amounts() -> None:
    record = JobRecord(
        "one",
        JobStatus.COMPLETED,
        datetime(2026, 1, 2, tzinfo=UTC),
        datetime(2026, 1, 3, tzinfo=UTC),
        billed_amount=Decimal("10.00"),
        billed_currency="USD",
    )
    result = assign_cohorts((record,), PERIOD)
    assert result.completion == (record,)
    assert record.billed_amount == Decimal("10.00")
