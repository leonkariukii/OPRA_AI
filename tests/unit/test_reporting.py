"""Tests for deterministic generic metric report serialization."""

import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from opra.core.config import OpraConfig
from opra.core.exceptions import ModelValidationError
from opra.models.analytics import MetricResult, MetricStatus, MetricValue
from opra.models.periods import ReportingPeriod
from opra.models.reporting import ReportDocument
from opra.reporting.json_export import report_to_json
from opra.reporting.markdown_export import report_to_markdown

PERIOD = ReportingPeriod(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 2, 1, tzinfo=UTC))
CONFIG = OpraConfig().snapshot()
GENERATED = datetime(2026, 3, 1, tzinfo=UTC)


def _metric(metric_id: str, status: MetricStatus, value: Decimal | None = None) -> MetricResult:
    return MetricResult(metric_id, MetricValue(status, value), PERIOD)


def _report(metrics: tuple[MetricResult, ...] = ()) -> ReportDocument:
    return ReportDocument(GENERATED, "0.1.0", CONFIG, metrics)


def test_report_normalizes_explicit_timestamp_to_utc() -> None:
    plus_three = timezone(timedelta(hours=3))
    report = ReportDocument(datetime(2026, 3, 1, 3, tzinfo=plus_three), "0.1.0", CONFIG, ())
    assert report.generated_at_utc == GENERATED
    assert report.generated_at_utc.tzinfo is UTC


@pytest.mark.parametrize(
    ("timestamp", "engine", "config", "metrics", "message"),
    [
        (datetime(2026, 3, 1), "0.1.0", CONFIG, (), "explicit UTC offset"),
        (GENERATED, " ", CONFIG, (), "engine_version"),
        (GENERATED, "0.1.0", object(), (), "ConfigSnapshot"),
        (GENERATED, "0.1.0", CONFIG, [], "metrics must be a tuple"),
        (GENERATED, "0.1.0", CONFIG, (object(),), "only MetricResult"),
    ],
)
def test_report_rejects_invalid_fields(
    timestamp: datetime,
    engine: str,
    config: object,
    metrics: object,
    message: str,
) -> None:
    with pytest.raises(ModelValidationError, match=message):
        ReportDocument(timestamp, engine, config, metrics)  # type: ignore[arg-type]


def test_report_is_frozen_and_slotted() -> None:
    report = _report()
    with pytest.raises(FrozenInstanceError):
        report.engine_version = "next"  # type: ignore[misc]
    assert not hasattr(report, "__dict__")


def test_json_has_stable_schema_order_and_explicit_metadata() -> None:
    parsed = json.loads(report_to_json(_report()))
    assert list(parsed) == [
        "schema_version",
        "generated_at_utc",
        "engine_version",
        "config",
        "metrics",
    ]
    assert parsed["generated_at_utc"] == "2026-03-01T00:00:00.000000Z"
    assert parsed["config"] == {
        "max_upload_bytes": 10 * 1024 * 1024,
        "max_rows": 100_000,
        "maturity_buffer_days": 3,
        "min_sample_size": 10,
    }


def test_json_keeps_decimal_exact_as_string_and_preserves_status_distinctions() -> None:
    report = _report(
        (
            _metric("zero", MetricStatus.AVAILABLE, Decimal("0.00")),
            _metric("missing", MetricStatus.UNAVAILABLE),
            _metric("not-applicable", MetricStatus.NOT_APPLICABLE),
        )
    )
    metrics = json.loads(report_to_json(report))["metrics"]
    assert [metric["metric_id"] for metric in metrics] == [
        "missing",
        "not-applicable",
        "zero",
    ]
    assert [(item["status"], item["value"]) for item in metrics] == [
        ("unavailable", None),
        ("not_applicable", None),
        ("available", "0.00"),
    ]
    assert list(metrics[0]) == ["metric_id", "status", "value", "period"]
    assert list(metrics[0]["period"]) == ["start_utc", "end_utc"]


def test_json_serialization_is_deterministic_and_retains_duplicate_entries() -> None:
    first = _metric("b", MetricStatus.AVAILABLE, Decimal("1.2300"))
    second = _metric("a", MetricStatus.AVAILABLE, Decimal(2))
    report = _report((first, second, first))
    expected = report_to_json(report)
    assert report_to_json(report) == expected
    metrics = json.loads(expected)["metrics"]
    assert [item["metric_id"] for item in metrics] == ["a", "b", "b"]
    assert metrics[1]["value"] == "1.2300"


def test_json_escapes_strings_and_is_compact() -> None:
    value = _metric('quote"\n', MetricStatus.AVAILABLE, Decimal("1E+3"))
    serialized = report_to_json(_report((value,)))
    assert "\\n" in serialized
    assert ": " not in serialized
    assert "1E+3" in serialized
    assert json.loads(serialized)["metrics"][0]["metric_id"] == 'quote"\n'


def test_markdown_is_stable_and_escapes_table_structure() -> None:
    report = _report(
        (
            _metric("z|`\nsecond", MetricStatus.UNAVAILABLE),
            _metric("a", MetricStatus.AVAILABLE, Decimal("12.340")),
        )
    )
    rendered = report_to_markdown(report)
    assert rendered == report_to_markdown(report)
    assert "| a | available | 12.340 |" in rendered
    assert "| z\\|\\`<br>second | unavailable | — |" in rendered
    assert rendered.endswith("\n")
    assert rendered.count("\n") == 10
