"""Tests for immutable analytics result models."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

import pytest

from opra.core.exceptions import ModelValidationError
from opra.models.analytics import MetricResult, MetricStatus, MetricValue
from opra.models.periods import ReportingPeriod


@pytest.mark.parametrize(
    ("status", "value"),
    [
        (MetricStatus.AVAILABLE, Decimal("0")),
        (MetricStatus.UNAVAILABLE, None),
        (MetricStatus.NOT_APPLICABLE, None),
    ],
)
def test_metric_value_accepts_valid_status_value_pairs(
    status: MetricStatus, value: Decimal | None
) -> None:
    assert MetricValue(status, value).value is value


@pytest.mark.parametrize("value", [True, False, 0, 1, 1.5, "1.5", None])
def test_available_metric_requires_decimal(value: object) -> None:
    with pytest.raises(ModelValidationError, match="Decimal"):
        MetricValue(MetricStatus.AVAILABLE, value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_available_metric_rejects_non_finite_decimal(value: Decimal) -> None:
    with pytest.raises(ModelValidationError, match="finite"):
        MetricValue(MetricStatus.AVAILABLE, value)


@pytest.mark.parametrize("status", [MetricStatus.UNAVAILABLE, MetricStatus.NOT_APPLICABLE])
@pytest.mark.parametrize("value", [Decimal("0"), False, Decimal("NaN")])
def test_missing_metric_states_require_none(status: MetricStatus, value: object) -> None:
    with pytest.raises(ModelValidationError, match="value=None"):
        MetricValue(status, value)  # type: ignore[arg-type]


def test_metric_status_must_be_metric_status() -> None:
    with pytest.raises(ModelValidationError, match="MetricStatus"):
        MetricValue("available", Decimal("1"))  # type: ignore[arg-type]


def test_metric_status_is_a_plain_enum() -> None:
    assert MetricStatus.__bases__ == (Enum,)
    assert MetricStatus.AVAILABLE.value == "available"
    assert MetricStatus.UNAVAILABLE.value == "unavailable"
    assert MetricStatus.NOT_APPLICABLE.value == "not_applicable"


def test_decimal_instance_and_scale_are_preserved_exactly() -> None:
    original = Decimal("123.4500")
    metric = MetricValue(MetricStatus.AVAILABLE, original)
    assert metric.value is original
    assert metric.value is not None
    assert metric.value.as_tuple() == original.as_tuple()


def test_metric_value_is_frozen_and_has_slots() -> None:
    metric = MetricValue(MetricStatus.AVAILABLE, Decimal("1.00"))
    with pytest.raises(FrozenInstanceError):
        metric.value = Decimal("2.00")  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        metric.extra = True  # type: ignore[attr-defined]


def _period() -> ReportingPeriod:
    return ReportingPeriod(
        datetime(2026, 1, 1, 8, tzinfo=UTC),
        datetime(2026, 1, 1, 10, tzinfo=UTC),
    )


def test_metric_result_accepts_and_preserves_metric_id() -> None:
    metric_value = MetricValue(MetricStatus.AVAILABLE, Decimal("0.00"))
    period = _period()
    result = MetricResult("  KPI-X  ", metric_value, period)
    assert result.metric_id == "  KPI-X  "
    assert result.metric_value is metric_value
    assert result.period is period


@pytest.mark.parametrize("metric_id", ["", " ", "\t\n"])
def test_metric_result_rejects_empty_or_whitespace_metric_id(metric_id: str) -> None:
    with pytest.raises(ModelValidationError, match="non-empty"):
        MetricResult(metric_id, MetricValue(MetricStatus.UNAVAILABLE), _period())


@pytest.mark.parametrize("metric_id", [None, 1, b"id"])
def test_metric_result_rejects_non_string_metric_id(metric_id: object) -> None:
    with pytest.raises(ModelValidationError, match="non-empty"):
        MetricResult(metric_id, MetricValue(MetricStatus.UNAVAILABLE), _period())  # type: ignore[arg-type]


def test_metric_result_validates_member_types() -> None:
    with pytest.raises(ModelValidationError, match="metric_value"):
        MetricResult("KPI-X", None, _period())  # type: ignore[arg-type]
    with pytest.raises(ModelValidationError, match="period"):
        MetricResult(
            "KPI-X",
            MetricValue(MetricStatus.UNAVAILABLE),
            None,  # type: ignore[arg-type]
        )


def test_metric_result_is_frozen_and_has_slots() -> None:
    result = MetricResult("KPI-X", MetricValue(MetricStatus.UNAVAILABLE), _period())
    with pytest.raises(FrozenInstanceError):
        result.metric_id = "KPI-Y"  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        result.extra = True  # type: ignore[attr-defined]
