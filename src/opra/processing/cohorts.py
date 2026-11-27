"""Deterministic period cohort assignment for canonical job records."""

from dataclasses import dataclass

from opra.core.exceptions import ModelValidationError
from opra.models.periods import ReportingPeriod
from opra.models.records import JobRecord, JobStatus


@dataclass(frozen=True, slots=True)
class ProcessingCohorts:
    """Input-order-preserving populations for one reporting period."""

    intake: tuple[JobRecord, ...]
    completion: tuple[JobRecord, ...]
    turnaround: tuple[JobRecord, ...]

    def __post_init__(self) -> None:
        for name, values in (
            ("intake", self.intake),
            ("completion", self.completion),
            ("turnaround", self.turnaround),
        ):
            if not isinstance(values, tuple):
                raise ModelValidationError(f"{name} must be a tuple.")
            if any(not isinstance(record, JobRecord) for record in values):
                raise ModelValidationError(f"{name} must contain only JobRecord values.")


def assign_cohorts(records: tuple[JobRecord, ...], period: ReportingPeriod) -> ProcessingCohorts:
    """Assign records using approved event timestamps and half-open UTC bounds.

    Intake uses ``opened_at`` for every status. Completion and turnaround populations use
    ``completed_at`` only for completed records with a supplied completion timestamp.
    This function does not apply a maturity buffer or calculate KPIs/durations.
    """
    if not isinstance(records, tuple):
        raise ModelValidationError("records must be a tuple.")
    if any(not isinstance(record, JobRecord) for record in records):
        raise ModelValidationError("records must contain only JobRecord values.")
    if not isinstance(period, ReportingPeriod):
        raise ModelValidationError("period must be a ReportingPeriod.")

    intake = tuple(record for record in records if period.contains(record.opened_at))
    completed = tuple(
        record
        for record in records
        if record.status is JobStatus.COMPLETED
        and record.completed_at is not None
        and period.contains(record.completed_at)
    )
    return ProcessingCohorts(intake=intake, completion=completed, turnaround=completed)
