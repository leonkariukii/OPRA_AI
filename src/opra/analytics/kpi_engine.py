"""Owner-approved deterministic automotive KPI calculations."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, localcontext

from opra.core.config import ConfigSnapshot
from opra.core.exceptions import ModelValidationError
from opra.models.analytics import AnalysisLimitation, MetricStatus, MetricValue
from opra.models.kpis import KPIResult
from opra.models.periods import ReportingPeriod
from opra.models.records import JobRecord, JobStatus
from opra.processing.cohorts import assign_cohorts

PERCENT_QUANTUM = Decimal("0.01")
HOUR_QUANTUM = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class KPIComputation:
    """Immutable KPI results and counted, privacy-safe limitations."""

    metrics: tuple[KPIResult, ...]
    limitations: tuple[AnalysisLimitation, ...]


def _normalize_utc(name: str, value: object) -> datetime:
    if not isinstance(value, datetime):
        raise ModelValidationError(f"{name} must be a datetime.")
    try:
        offset = value.utcoffset()
        normalized = value.astimezone(UTC) if offset is not None else None
    except (OverflowError, ValueError):
        raise ModelValidationError(f"{name} cannot be normalized to UTC.") from None
    if normalized is None:
        raise ModelValidationError(f"{name} must have an explicit UTC offset.")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value)


def _rate(numerator: int, denominator: int) -> Decimal:
    with localcontext() as context:
        context.prec = 50
        return (
            Decimal(numerator) * Decimal(100) / Decimal(denominator)
        ).quantize(PERCENT_QUANTUM, rounding=ROUND_HALF_UP)


def _exact_sum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return Decimal(0)
    max_adjusted = max(value.adjusted() for value in values if value != 0) if any(
        value != 0 for value in values
    ) else 0
    min_exponent = min(value.as_tuple().exponent for value in values)
    required_precision = max(1, max_adjusted - min_exponent + 1) + len(str(len(values))) + 1
    with localcontext() as context:
        context.prec = max(50, required_precision)
        total = sum(values, Decimal(0))
    return total


def _elapsed_microseconds(start: datetime, end: datetime) -> int:
    delta = end - start
    return (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds


def _limitations(codes: set[str]) -> tuple[str, ...]:
    return tuple(sorted(codes))


def calculate_kpis(
    records: tuple[JobRecord, ...],
    period: ReportingPeriod,
    reference_utc_timestamp: datetime,
    config: ConfigSnapshot,
) -> KPIComputation:
    """Calculate KPI-01 through KPI-07 for one period and snapshot time.

    The reference timestamp must describe the source snapshot as-of time. This function
    consumes canonical valid records only and never mutates them.
    """
    if not isinstance(config, ConfigSnapshot):
        raise ModelValidationError("config must be a ConfigSnapshot.")
    reference = _normalize_utc("reference_utc_timestamp", reference_utc_timestamp)
    if period.end_utc > reference:
        raise ModelValidationError("period.end_utc must not be later than reference_utc_timestamp.")
    cohorts = assign_cohorts(records, period)
    completed_missing_time = sum(
        record.status is JobStatus.COMPLETED and record.completed_at is None
        for record in records
    )

    intake = cohorts.intake
    matured = tuple(
        record
        for record in intake
        if record.opened_at + timedelta(days=config.maturity_buffer_days) <= reference
    )
    immature_count = len(intake) - len(matured)
    completed_matured = tuple(
        record
        for record in matured
        if record.status is JobStatus.COMPLETED
        and record.completed_at is not None
        and record.completed_at <= reference
    )
    cancelled_matured = tuple(
        record for record in matured if record.status is JobStatus.CANCELLED
    )
    completed = cohorts.completion
    turnaround_candidates = cohorts.turnaround
    valid_turnaround = tuple(
        record
        for record in turnaround_candidates
        if record.completed_at is not None and record.completed_at >= record.opened_at
    )
    negative_duration_count = len(turnaround_candidates) - len(valid_turnaround)

    result: list[KPIResult] = []
    result.append(
        KPIResult(
            "KPI-01",
            "Jobs Opened",
            "jobs",
            MetricValue(MetricStatus.AVAILABLE, _count(len(intake))),
            period,
            _count(len(intake)),
            None,
            len(intake),
            len(intake),
        )
    )
    kpi02_codes = {"COMPLETED_TIMESTAMP_MISSING"} if completed_missing_time else set()
    result.append(
        KPIResult(
            "KPI-02",
            "Jobs Completed",
            "jobs",
            MetricValue(MetricStatus.AVAILABLE, _count(len(completed))),
            period,
            _count(len(completed)),
            None,
            len(completed),
            len(completed),
            _limitations(kpi02_codes),
        )
    )
    matured_denominator = len(matured)
    kpi03_codes = {"COMPLETED_TIMESTAMP_MISSING"} if any(
        record.status is JobStatus.COMPLETED and record.completed_at is None
        for record in matured
    ) else set()
    if immature_count:
        kpi03_codes.add("IMMATURE_INTAKE_EXCLUDED")
    if matured_denominator:
        kpi03_value = MetricValue(
            MetricStatus.AVAILABLE,
            _rate(len(completed_matured), matured_denominator),
        )
    else:
        kpi03_value = MetricValue(MetricStatus.NOT_APPLICABLE)
    result.append(
        KPIResult(
            "KPI-03",
            "Matured Intake Completion Rate",
            "%",
            kpi03_value,
            period,
            _count(len(completed_matured)),
            _count(matured_denominator),
            matured_denominator,
            matured_denominator,
            _limitations(kpi03_codes),
        )
    )
    kpi04_codes = {"IMMATURE_INTAKE_EXCLUDED"} if immature_count else set()
    if matured_denominator:
        kpi04_value = MetricValue(
            MetricStatus.AVAILABLE,
            _rate(len(cancelled_matured), matured_denominator),
        )
    else:
        kpi04_value = MetricValue(MetricStatus.NOT_APPLICABLE)
    result.append(
        KPIResult(
            "KPI-04",
            "Matured Intake Cancellation Rate",
            "%",
            kpi04_value,
            period,
            _count(len(cancelled_matured)),
            _count(matured_denominator),
            matured_denominator,
            matured_denominator,
            _limitations(kpi04_codes),
        )
    )

    billed_records_by_currency: dict[str, list[Decimal]] = {}
    for record in completed:
        if record.billed_amount is not None and record.billed_currency is not None:
            billed_records_by_currency.setdefault(record.billed_currency, []).append(
                record.billed_amount
            )
    billed_missing_count = sum(record.billed_amount is None for record in completed)
    if not completed:
        result.append(
            KPIResult(
                "KPI-05",
                "Observed Billed Amount",
                "currency-unspecified",
                MetricValue(MetricStatus.NOT_APPLICABLE),
                period,
                None,
                None,
                0,
                0,
            )
        )
    elif not billed_records_by_currency:
        result.append(
            KPIResult(
                "KPI-05",
                "Observed Billed Amount",
                "currency-unspecified",
                MetricValue(MetricStatus.UNAVAILABLE),
                period,
                None,
                None,
                0,
                len(completed),
                ("BILLED_AMOUNT_MISSING",),
            )
        )
    for currency in sorted(billed_records_by_currency):
        amounts = tuple(billed_records_by_currency[currency])
        total = _exact_sum(amounts)
        codes = {"BILLED_AMOUNT_MISSING"} if billed_missing_count else set()
        result.append(
            KPIResult(
                "KPI-05",
                f"Observed Billed Amount ({currency})",
                currency,
                MetricValue(MetricStatus.AVAILABLE, total),
                period,
                total,
                None,
                len(amounts),
                len(completed),
                _limitations(codes),
            )
        )

    kpi06_codes = {"IMMATURE_INTAKE_EXCLUDED"} if immature_count else set()
    result.append(
        KPIResult(
            "KPI-06",
            "Matured Intake Cohort Count",
            "jobs",
            MetricValue(MetricStatus.AVAILABLE, _count(matured_denominator)),
            period,
            _count(matured_denominator),
            None,
            matured_denominator,
            matured_denominator,
            _limitations(kpi06_codes),
        )
    )

    turnaround_codes = {"NEGATIVE_TURNAROUND_DURATION"} if negative_duration_count else set()
    if not turnaround_candidates:
        turnaround_value = MetricValue(MetricStatus.NOT_APPLICABLE)
        numerator = None
        denominator = None
        turnaround_sample = 0
    elif not valid_turnaround:
        turnaround_value = MetricValue(MetricStatus.UNAVAILABLE)
        numerator = None
        denominator = _count(0)
        turnaround_sample = 0
        turnaround_codes.add("TURNAROUND_NO_VALID_DURATION")
    else:
        total_microseconds = sum(
            _elapsed_microseconds(record.opened_at, record.completed_at)
            for record in valid_turnaround
            if record.completed_at is not None
        )
        with localcontext() as context:
            context.prec = 50
            total_hours = Decimal(total_microseconds).scaleb(-6) / Decimal(3600)
            mean_hours = (total_hours / Decimal(len(valid_turnaround))).quantize(
                HOUR_QUANTUM, rounding=ROUND_HALF_UP
            )
        turnaround_value = MetricValue(MetricStatus.AVAILABLE, mean_hours)
        numerator = total_hours
        denominator = _count(len(valid_turnaround))
        turnaround_sample = len(valid_turnaround)
    result.append(
        KPIResult(
            "KPI-07",
            "Mean Completed Turnaround Hours",
            "hours",
            turnaround_value,
            period,
            numerator,
            denominator,
            turnaround_sample,
            len(turnaround_candidates),
            _limitations(turnaround_codes),
        )
    )

    limitations: list[AnalysisLimitation] = []
    if completed_missing_time:
        limitations.append(
            AnalysisLimitation("COMPLETED_TIMESTAMP_MISSING", completed_missing_time, "KPI-02")
        )
    if immature_count:
        limitations.append(AnalysisLimitation("IMMATURE_INTAKE_EXCLUDED", immature_count))
    if billed_missing_count:
        limitations.append(
            AnalysisLimitation("BILLED_AMOUNT_MISSING", billed_missing_count, "KPI-05")
        )
    if negative_duration_count:
        limitations.append(
            AnalysisLimitation(
                "NEGATIVE_TURNAROUND_DURATION", negative_duration_count, "KPI-07"
            )
        )
    return KPIComputation(tuple(result), tuple(sorted(limitations, key=lambda item: (item.code, item.metric_id or ""))))
