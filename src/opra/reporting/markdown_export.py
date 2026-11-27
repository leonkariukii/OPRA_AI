"""Deterministic Markdown export for generic metric reports."""

from opra.models.reporting import IntegratedReportDocument, ReportDocument


def _escape_cell(value: str) -> str:
    """Escape text for Markdown and guard formula-like text copied to spreadsheets."""
    if value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        value = "'" + value
    return _escape_markdown_cell(value)


def _escape_numeric_cell(value: str) -> str:
    """Escape numeric presentation without formula-prefix rewriting."""
    return _escape_markdown_cell(value)


def _escape_markdown_cell(value: str) -> str:
    """Escape markup delimiters and line breaks without changing canonical values."""
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
                    _escape_numeric_cell(value)
                    if metric.metric_value.value is not None
                    else _escape_cell(value),
                    metric.period.start_utc.isoformat(timespec="microseconds").replace(
                        "+00:00", "Z"
                    ),
                    metric.period.end_utc.isoformat(timespec="microseconds").replace("+00:00", "Z"),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def integrated_report_to_markdown(report: IntegratedReportDocument) -> str:
    """Render integrated KPI, comparison, finding, recommendation and limitation sections."""
    lines = [
        "# OPRA.AI Analytics Report",
        "",
        f"- Schema version: `{_escape_cell(report.schema_version)}`",
        f"- Generated at (UTC): `{report.generated_at_utc.isoformat(timespec='microseconds').replace('+00:00', 'Z')}`",
        f"- Reference time (UTC): `{report.reference_utc_timestamp.isoformat(timespec='microseconds').replace('+00:00', 'Z')}`",
        f"- Ingestion: `{_escape_cell(report.ingestion.dataset_status)}` ({report.ingestion.accepted_record_count} accepted, {report.ingestion.rejected_record_count} rejected, {report.ingestion.quarantined_record_count} quarantined)",
        "",
        "## KPIs",
        "",
        "| KPI | Unit | Status | Value | Sample |",
        "|---|---|---|---|---:|",
    ]
    for item in sorted(
        report.metrics, key=lambda value: (value.kpi_id, value.unit, value.period.start_utc)
    ):
        val = str(item.metric_value.value) if item.metric_value.value is not None else "—"
        rendered_value = (
            _escape_numeric_cell(val) if item.metric_value.value is not None else _escape_cell(val)
        )
        lines.append(
            f"| {_escape_cell(item.kpi_id + ' ' + item.name)} | {_escape_cell(item.unit)} | {item.metric_value.status.value} | {rendered_value} | {item.sample_size} |"
        )
    lines.extend(
        [
            "",
            "## Period comparisons",
            "",
            "| KPI | Unit | Absolute | Relative |",
            "|---|---|---|---|",
        ]
    )
    for comparison in sorted(
        report.comparisons, key=lambda value: (value.current.kpi_id, value.current.unit)
    ):
        absolute = (
            str(comparison.absolute_change.value)
            if comparison.absolute_change.value is not None
            else comparison.absolute_change.status.value
        )
        relative = (
            str(comparison.relative_change.value)
            if comparison.relative_change.value is not None
            else comparison.relative_change.status.value
        )
        rendered_absolute = (
            _escape_numeric_cell(absolute)
            if comparison.absolute_change.value is not None
            else _escape_cell(absolute)
        )
        rendered_relative = (
            _escape_numeric_cell(relative)
            if comparison.relative_change.value is not None
            else _escape_cell(relative)
        )
        lines.append(
            f"| {_escape_cell(comparison.current.kpi_id)} | {_escape_cell(comparison.current.unit)} | {rendered_absolute} | {rendered_relative} |"
        )
    lines.extend(["", "## Findings and recommendations", ""])
    if not report.findings:
        lines.append("No findings were triggered.")
    for finding in sorted(
        report.findings, key=lambda value: (value.priority_rank, value.finding_id)
    ):
        lines.append(
            f"- **{_escape_cell(finding.finding_id)} — {_escape_cell(finding.title)}** (priority {finding.priority_rank}; {_escape_cell(finding.evidence_tier.value)} evidence)"
        )
        for recommendation in report.recommendations:
            if recommendation.finding_id == finding.finding_id:
                lines.append(f"  - {_escape_cell(recommendation.text)}")
    lines.extend(["", "## Limitations", ""])
    if not report.limitations:
        lines.append("None.")
    else:
        for limitation in sorted(
            report.limitations, key=lambda value: (value.code, value.metric_id or "", value.count)
        ):
            lines.append(
                f"- `{_escape_cell(limitation.code)}`: {limitation.count}"
                + (f" ({_escape_cell(limitation.metric_id)})" if limitation.metric_id else "")
            )
    return "\n".join(lines) + "\n"
