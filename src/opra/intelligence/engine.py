"""Approved deterministic threshold findings and evidence tiers."""

from dataclasses import dataclass
from decimal import Decimal

from opra.core.config import ConfigSnapshot
from opra.models.analytics import AnalysisLimitation, MetricStatus
from opra.models.comparisons import ComparisonResult
from opra.models.intelligence import EvidenceTier, Finding


@dataclass(frozen=True, slots=True)
class IntelligenceResult:
    findings: tuple[Finding, ...]
    limitations: tuple[AnalysisLimitation, ...]


RULES = {
    "KPI-03": ("F-001", "Completion Rate Declined", 1, "absolute", Decimal("-10.00")),
    "KPI-04": ("F-002", "Cancellation Rate Increased", 2, "absolute", Decimal("5.00")),
    "KPI-07": ("F-003", "Turnaround Increased", 3, "turnaround", Decimal("20.00")),
    "KPI-05": ("F-004", "Observed Billed Amount Declined", 4, "relative", Decimal("-15.00")),
}


def evaluate_findings(
    comparisons: tuple[ComparisonResult, ...], config: ConfigSnapshot
) -> IntelligenceResult:
    findings: list[Finding] = []
    limitations: list[AnalysisLimitation] = []
    for comparison in comparisons:
        current, baseline = comparison.current, comparison.baseline
        rule = RULES.get(current.kpi_id)
        if rule is None:
            continue
        if (
            baseline is None
            or current.metric_value.status is not MetricStatus.AVAILABLE
            or baseline.metric_value.status is not MetricStatus.AVAILABLE
        ):
            continue
        n = min(current.sample_size, baseline.sample_size)
        coverage_values = [
            v for v in (current.coverage_percent, baseline.coverage_percent) if v is not None
        ]
        coverage = min(coverage_values) if coverage_values else Decimal(100)
        if n < config.min_sample_size:
            limitations.append(AnalysisLimitation("INSUFFICIENT_SAMPLE", n, current.result_id))
            continue
        if coverage < Decimal(80):
            limitations.append(
                AnalysisLimitation(
                    "INSUFFICIENT_DATA_COVERAGE",
                    current.eligible_count - current.sample_size,
                    current.result_id,
                )
            )
            continue
        finding_id, title, priority, condition, threshold = rule
        absolute = comparison.absolute_change.value
        relative = comparison.relative_change.value
        triggered = (
            absolute is not None and absolute <= threshold
            if condition == "absolute" and current.kpi_id == "KPI-03"
            else absolute is not None and absolute >= threshold
            if condition == "absolute"
            else relative is not None and relative <= threshold
            if condition == "relative"
            else relative is not None
            and absolute is not None
            and relative >= threshold
            and absolute >= Decimal("2.00")
        )
        if not triggered:
            continue
        tier = (
            EvidenceTier.LIMITED
            if n < 20
            else EvidenceTier.MODERATE
            if n < 50
            else EvidenceTier.STRONG
        )
        if coverage < Decimal(90):
            tier = (
                EvidenceTier.LIMITED
                if tier is EvidenceTier.MODERATE
                else EvidenceTier.MODERATE
                if tier is EvidenceTier.STRONG
                else EvidenceTier.LIMITED
            )
        findings.append(Finding(finding_id, title, priority, comparison, tier))
    ordered = tuple(
        sorted(
            findings,
            key=lambda f: (
                f.priority_rank,
                f.finding_id,
                f.comparison.current.period.start_utc,
                f.comparison.current.kpi_id,
            ),
        )
    )
    return IntelligenceResult(
        ordered, tuple(sorted(set(limitations), key=lambda x: (x.code, x.metric_id or "", x.count)))
    )
