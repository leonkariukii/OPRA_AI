"""Acceptance tests for owner-approved analytics v1 behavior."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from opra.analytics.comparisons import compare_kpis
from opra.analytics.kpi_engine import calculate_kpis
from opra.core.config import OpraConfig
from opra.intelligence.engine import evaluate_findings
from opra.models.analytics import MetricStatus
from opra.models.periods import ReportingPeriod
from opra.models.records import JobRecord, JobStatus
from opra.pipeline.runner import run_analytics
from opra.reporting.json_export import integrated_report_to_json
from opra.reporting.markdown_export import integrated_report_to_markdown

PERIOD = ReportingPeriod(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 2, 1, tzinfo=UTC))
REF = datetime(2026, 3, 1, tzinfo=UTC)
CONFIG = OpraConfig(maturity_buffer_days=3, min_sample_size=1).snapshot()


def _record(
    key: str,
    status: JobStatus,
    opened: datetime,
    completed: datetime | None = None,
    billed: str | None = None,
) -> JobRecord:
    return JobRecord(
        key,
        status,
        opened,
        completed,
        Decimal(billed) if billed is not None else None,
        "KES" if billed is not None else None,
    )


def test_kpi_maturity_cutoff_and_status_denominators() -> None:
    records = (
        _record(
            "done",
            JobStatus.COMPLETED,
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 5, tzinfo=UTC),
        ),
        _record("cancel", JobStatus.CANCELLED, datetime(2026, 1, 2, tzinfo=UTC)),
        _record("active", JobStatus.IN_PROGRESS, datetime(2026, 1, 3, tzinfo=UTC)),
        _record("immature", JobStatus.IN_PROGRESS, datetime(2026, 1, 30, tzinfo=UTC)),
    )
    result = calculate_kpis(records, PERIOD, datetime(2026, 2, 1, tzinfo=UTC), CONFIG)
    values = {metric.kpi_id: metric for metric in result.metrics}
    assert values["KPI-01"].metric_value.value == Decimal(4)
    assert values["KPI-03"].numerator == Decimal(1)
    assert values["KPI-03"].denominator == Decimal(3)
    assert values["KPI-03"].metric_value.value == Decimal("33.33")
    assert values["KPI-04"].metric_value.value == Decimal("33.33")
    assert values["KPI-06"].metric_value.value == Decimal(3)
    assert "IMMATURE_INTAKE_EXCLUDED" in values["KPI-06"].limitation_codes


def test_financial_aggregation_preserves_decimal_scale_and_currency() -> None:
    records = (
        _record(
            "a",
            JobStatus.COMPLETED,
            datetime(2026, 1, 2, tzinfo=UTC),
            datetime(2026, 1, 4, tzinfo=UTC),
            "12.340",
        ),
        _record(
            "b",
            JobStatus.COMPLETED,
            datetime(2026, 1, 3, tzinfo=UTC),
            datetime(2026, 1, 5, tzinfo=UTC),
            "-2.00",
        ),
    )
    result = calculate_kpis(records, PERIOD, REF, CONFIG)
    billed = next(metric for metric in result.metrics if metric.kpi_id == "KPI-05")
    assert billed.unit == "KES"
    assert billed.metric_value.value == Decimal("10.340")


def test_turnaround_mean_and_zero_duration() -> None:
    records = (
        _record(
            "zero",
            JobStatus.COMPLETED,
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 1, tzinfo=UTC),
        ),
        _record(
            "two",
            JobStatus.COMPLETED,
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 1, 2, tzinfo=UTC),
        ),
    )
    result = calculate_kpis(records, PERIOD, REF, CONFIG)
    metric = next(item for item in result.metrics if item.kpi_id == "KPI-07")
    assert metric.metric_value.value == Decimal("1.00")


def test_comparison_zero_baseline_and_missing_baseline() -> None:
    baseline_period = ReportingPeriod(datetime(2025, 12, 1, tzinfo=UTC), PERIOD.start_utc)
    current = calculate_kpis((), PERIOD, REF, CONFIG).metrics
    baseline = calculate_kpis((), baseline_period, REF, CONFIG).metrics
    zero = compare_kpis(current, baseline)
    kpi01 = next(item for item in zero if item.current.kpi_id == "KPI-01")
    assert kpi01.absolute_change.value == Decimal(0)
    assert kpi01.relative_change.status is MetricStatus.UNAVAILABLE
    missing = compare_kpis(current, None)
    assert all(item.relative_change.status is MetricStatus.UNAVAILABLE for item in missing)
    assert all("MISSING_BASELINE" in item.limitation_codes for item in missing)


def test_decline_trigger_is_deterministic_and_small_sample_is_enforced() -> None:
    baseline_period = ReportingPeriod(PERIOD.start_utc - timedelta(days=31), PERIOD.start_utc)
    records = tuple(
        _record(
            f"b{i}",
            JobStatus.COMPLETED,
            datetime(2025, 12, 2, tzinfo=UTC),
            datetime(2025, 12, 8, tzinfo=UTC),
        )
        for i in range(10)
    ) + tuple(
        _record(f"c{i}", JobStatus.IN_PROGRESS, datetime(2026, 1, 2, tzinfo=UTC)) for i in range(10)
    )
    baseline = calculate_kpis(records, baseline_period, REF, CONFIG).metrics
    current = calculate_kpis(records, PERIOD, REF, CONFIG).metrics
    comparisons = compare_kpis(current, baseline)
    result = evaluate_findings(comparisons, CONFIG)
    assert [finding.finding_id for finding in result.findings] == ["F-001"]


def test_csv_pipeline_produces_deterministic_privacy_safe_integrated_exports() -> None:
    payload = (
        b"job_id,status,opened_at,completed_at,billed_amount,billed_currency\n"
        b"private-job-id,completed,2026-01-02T00:00:00Z,2026-01-03T00:00:00Z,10.00,KES\n"
        b"bad-job-id,unknown,2026-01-04T00:00:00Z,,,\n"
    )
    report = run_analytics(
        payload,
        OpraConfig(maturity_buffer_days=0, min_sample_size=1),
        PERIOD,
        REF,
        REF,
        "test-engine",
        ReportingPeriod(datetime(2025, 12, 1, tzinfo=UTC), PERIOD.start_utc),
    )
    output = integrated_report_to_json(report)
    assert output == integrated_report_to_json(report)
    assert "private-job-id" not in output
    assert "bad-job-id" not in output
    assert '"schema_version":"1.1.0"' in output
    assert report.ingestion.accepted_record_count == 1
    assert report.ingestion.rejected_record_count == 1
    assert report.ingestion.quarantined_record_count == 1
    markdown = integrated_report_to_markdown(report)
    assert "## KPIs" in markdown
    assert "## Findings and recommendations" in markdown
