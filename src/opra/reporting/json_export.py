"""Deterministic JSON export for generic metric reports."""

import json
from datetime import datetime
from typing import Any

from opra.models.analytics import MetricValue
from opra.models.periods import ReportingPeriod
from opra.models.reporting import IntegratedReportDocument, ReportDocument


def _utc_iso(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def report_to_json(report: ReportDocument) -> str:
    """Serialize a report with stable ordering and exact Decimal strings."""
    metrics = sorted(
        report.metrics,
        key=lambda metric: (
            metric.metric_id,
            metric.period.start_utc,
            metric.period.end_utc,
        ),
    )
    payload = {
        "schema_version": report.schema_version,
        "generated_at_utc": _utc_iso(report.generated_at_utc),
        "engine_version": report.engine_version,
        "config": {
            "max_upload_bytes": report.config.max_upload_bytes,
            "max_rows": report.config.max_rows,
            "maturity_buffer_days": report.config.maturity_buffer_days,
            "min_sample_size": report.config.min_sample_size,
        },
        "metrics": [
            {
                "metric_id": metric.metric_id,
                "status": metric.metric_value.status.value,
                "value": (
                    str(metric.metric_value.value)
                    if metric.metric_value.value is not None
                    else None
                ),
                "period": {
                    "start_utc": _utc_iso(metric.period.start_utc),
                    "end_utc": _utc_iso(metric.period.end_utc),
                },
            }
            for metric in metrics
        ],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def integrated_report_to_json(report: IntegratedReportDocument) -> str:
    """Serialize the integrated schema without exposing source rows or identifiers."""
    metrics = sorted(
        report.metrics, key=lambda item: (item.kpi_id, item.unit, item.period.start_utc)
    )
    comparisons = sorted(
        report.comparisons,
        key=lambda item: (item.current.kpi_id, item.current.unit, item.current.period.start_utc),
    )
    findings = sorted(
        report.findings,
        key=lambda item: (
            item.priority_rank,
            item.finding_id,
            item.comparison.current.period.start_utc,
            item.comparison.current.kpi_id,
        ),
    )
    recommendations = sorted(
        report.recommendations, key=lambda item: (item.priority_rank, item.recommendation_id)
    )
    limitations = sorted(
        report.limitations, key=lambda item: (item.code, item.metric_id or "", item.count)
    )

    def metric_value(value: MetricValue) -> dict[str, Any]:
        return {
            "status": value.status.value,
            "value": str(value.value) if value.value is not None else None,
        }

    def period(value: ReportingPeriod) -> dict[str, str]:
        return {"start_utc": _utc_iso(value.start_utc), "end_utc": _utc_iso(value.end_utc)}

    payload = {
        "schema_version": report.schema_version,
        "generated_at_utc": _utc_iso(report.generated_at_utc),
        "engine_version": report.engine_version,
        "config": {
            "max_upload_bytes": report.config.max_upload_bytes,
            "max_rows": report.config.max_rows,
            "maturity_buffer_days": report.config.maturity_buffer_days,
            "min_sample_size": report.config.min_sample_size,
        },
        "reference_utc_timestamp": _utc_iso(report.reference_utc_timestamp),
        "ingestion": {
            "dataset_status": report.ingestion.dataset_status,
            "total_processed_record_count": report.ingestion.total_processed_record_count,
            "accepted_record_count": report.ingestion.accepted_record_count,
            "rejected_record_count": report.ingestion.rejected_record_count,
            "exact_duplicate_count": report.ingestion.exact_duplicate_count,
            "conflicting_duplicate_count": report.ingestion.conflicting_duplicate_count,
            "quarantined_record_count": report.ingestion.quarantined_record_count,
        },
        "periods": {
            "current": period(report.current_period),
            "baseline": period(report.baseline_period) if report.baseline_period else None,
        },
        "metrics": [
            {
                "kpi_id": item.kpi_id,
                "name": item.name,
                "status": item.metric_value.status.value,
                "value": str(item.metric_value.value)
                if item.metric_value.value is not None
                else None,
                "unit": item.unit,
                "period": period(item.period),
                "numerator": str(item.numerator) if item.numerator is not None else None,
                "denominator": str(item.denominator) if item.denominator is not None else None,
                "sample_size": item.sample_size,
                "eligible_count": item.eligible_count,
                "limitation_codes": list(item.limitation_codes),
            }
            for item in metrics
        ],
        "comparisons": [
            {
                "kpi_id": item.current.kpi_id,
                "unit": item.current.unit,
                "baseline_period": period(item.baseline.period) if item.baseline else None,
                "current_period": period(item.current.period),
                "current_status": item.current.metric_value.status.value,
                "baseline_status": item.baseline.metric_value.status.value
                if item.baseline
                else None,
                "current_value": str(item.current.metric_value.value)
                if item.current.metric_value.value is not None
                else None,
                "baseline_value": str(item.baseline.metric_value.value)
                if item.baseline and item.baseline.metric_value.value is not None
                else None,
                "absolute_change": metric_value(item.absolute_change),
                "relative_change": metric_value(item.relative_change),
                "sample_size": item.sample_size,
                "coverage_percent": str(item.coverage_percent)
                if item.coverage_percent is not None
                else None,
                "limitation_codes": list(item.limitation_codes),
            }
            for item in comparisons
        ],
        "findings": [
            {
                "finding_id": item.finding_id,
                "title": item.title,
                "priority_rank": item.priority_rank,
                "evidence_tier": item.evidence_tier.value,
                "kpi_id": item.comparison.current.kpi_id,
                "period": period(item.comparison.current.period),
                "current_value": str(item.comparison.current.metric_value.value)
                if item.comparison.current.metric_value.value is not None
                else None,
                "baseline_value": str(item.comparison.baseline.metric_value.value)
                if item.comparison.baseline
                and item.comparison.baseline.metric_value.value is not None
                else None,
                "absolute_change": str(item.comparison.absolute_change.value)
                if item.comparison.absolute_change.value is not None
                else None,
                "relative_change": str(item.comparison.relative_change.value)
                if item.comparison.relative_change.value is not None
                else None,
                "sample_size": item.comparison.sample_size,
                "rule_version": item.rule_version,
                "limitation_codes": list(item.limitation_codes),
            }
            for item in findings
        ],
        "recommendations": [
            {
                "recommendation_id": item.recommendation_id,
                "finding_id": item.finding_id,
                "priority_rank": item.priority_rank,
                "text": item.text,
                "limitation_codes": list(item.limitation_codes),
            }
            for item in recommendations
        ],
        "limitations": [
            {"code": item.code, "count": item.count, "metric_id": item.metric_id}
            for item in limitations
        ],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
