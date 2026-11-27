"""Deterministic comparison calculations for adjacent periods."""

from decimal import ROUND_HALF_UP, Decimal, localcontext

from opra.core.exceptions import ModelValidationError
from opra.models.analytics import MetricStatus, MetricValue
from opra.models.comparisons import ComparisonResult
from opra.models.kpis import KPIResult


def _change(
    current: KPIResult, baseline: KPIResult | None
) -> tuple[MetricValue, MetricValue, tuple[str, ...]]:
    if baseline is None:
        unavailable = MetricValue(MetricStatus.UNAVAILABLE)
        return unavailable, unavailable, ("MISSING_BASELINE",)
    if (
        current.metric_value.status is MetricStatus.NOT_APPLICABLE
        or baseline.metric_value.status is MetricStatus.NOT_APPLICABLE
    ):
        not_applicable = MetricValue(MetricStatus.NOT_APPLICABLE)
        return not_applicable, not_applicable, ()
    if (
        current.metric_value.status is not MetricStatus.AVAILABLE
        or baseline.metric_value.status is not MetricStatus.AVAILABLE
    ):
        unavailable = MetricValue(MetricStatus.UNAVAILABLE)
        return unavailable, unavailable, ()
    assert current.metric_value.value is not None and baseline.metric_value.value is not None
    absolute = current.metric_value.value - baseline.metric_value.value
    absolute_metric = MetricValue(MetricStatus.AVAILABLE, absolute)
    if baseline.metric_value.value == 0:
        return absolute_metric, MetricValue(MetricStatus.UNAVAILABLE), ("ZERO_BASELINE",)
    with localcontext() as context:
        context.prec = 50
        relative = (Decimal(100) * absolute / abs(baseline.metric_value.value)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    return absolute_metric, MetricValue(MetricStatus.AVAILABLE, relative), ()


def compare_kpis(
    current_metrics: tuple[KPIResult, ...], baseline_metrics: tuple[KPIResult, ...] | None
) -> tuple[ComparisonResult, ...]:
    """Compare matching KPI/unit results; `None` means no baseline invocation."""
    if not isinstance(current_metrics, tuple) or any(
        not isinstance(item, KPIResult) for item in current_metrics
    ):
        raise ModelValidationError("current_metrics must be a tuple of KPIResult values.")
    if baseline_metrics is not None and (
        not isinstance(baseline_metrics, tuple)
        or any(not isinstance(item, KPIResult) for item in baseline_metrics)
    ):
        raise ModelValidationError("baseline_metrics must be None or a tuple of KPIResult values.")
    baseline_by_identity = (
        {} if baseline_metrics is None else {item.result_id: item for item in baseline_metrics}
    )
    if baseline_metrics is not None and len(baseline_by_identity) != len(baseline_metrics):
        raise ModelValidationError("baseline_metrics must have unique KPI identities.")
    if len({item.result_id for item in current_metrics}) != len(current_metrics):
        raise ModelValidationError("current_metrics must have unique KPI identities.")
    comparisons: list[ComparisonResult] = []
    for current in sorted(current_metrics, key=lambda item: (item.kpi_id, item.unit)):
        baseline = baseline_by_identity.get(current.result_id)
        absolute, relative, codes = _change(current, baseline)
        sample = min(current.sample_size, baseline.sample_size) if baseline else current.sample_size
        coverage_values = [
            value
            for value in (current.coverage_percent, baseline.coverage_percent if baseline else None)
            if value is not None
        ]
        coverage = min(coverage_values) if coverage_values else None
        comparisons.append(
            ComparisonResult(current, baseline, absolute, relative, sample, coverage, codes)
        )
    return tuple(comparisons)
