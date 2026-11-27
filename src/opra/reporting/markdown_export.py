"""Deterministic Markdown export for generic metric reports."""

from opra.models.reporting import ReportDocument


def _escape_cell(value: str) -> str:
    """Escape Markdown table delimiters without changing the source value."""
    escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    escaped = escaped.replace("\\", "\\\\")
    for character in ("|", "`", "[", "]", "(", ")", "!"):
        escaped = escaped.replace(character, f"\\{character}")
    return escaped.replace("\r\n", "<br>").replace("\r", "<br>").replace("\n", "<br>")


def report_to_markdown(report: ReportDocument) -> str:
    """Render metadata and generic metrics in stable order."""
    rows = sorted(
        report.metrics,
        key=lambda metric: (
            metric.metric_id,
            metric.period.start_utc,
            metric.period.end_utc,
        ),
    )
    lines = [
        "# OPRA.AI Report",
        "",
        f"- Schema version: `{_escape_cell(report.schema_version)}`",
        f"- Generated at (UTC): `{report.generated_at_utc.isoformat(timespec='microseconds').replace('+00:00', 'Z')}`",
        f"- Engine version: `{_escape_cell(report.engine_version)}`",
        "",
        "| Metric | Status | Value | Period start (UTC) | Period end (UTC) |",
        "|---|---|---|---|---|",
    ]
    for metric in rows:
        value = str(metric.metric_value.value) if metric.metric_value.value is not None else "—"
        lines.append(
            "| "
            + " | ".join(
                (
                    _escape_cell(metric.metric_id),
                    metric.metric_value.status.value,
                    _escape_cell(value),
                    metric.period.start_utc.isoformat(timespec="microseconds").replace(
                        "+00:00", "Z"
                    ),
                    metric.period.end_utc.isoformat(timespec="microseconds").replace("+00:00", "Z"),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"
