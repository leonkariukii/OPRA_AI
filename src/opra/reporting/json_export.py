"""Deterministic JSON export for generic metric reports."""

import json
from datetime import datetime

from opra.models.reporting import ReportDocument


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
