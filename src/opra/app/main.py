"""Thin Streamlit presentation shell delegating all work to the pipeline."""

from datetime import UTC, date, datetime, time, timedelta

import streamlit as st

from opra.core.config import OpraConfig
from opra.core.exceptions import OpraError
from opra.models.periods import ReportingPeriod
from opra.pipeline.runner import run_analytics
from opra.reporting.json_export import integrated_report_to_json
from opra.reporting.markdown_export import integrated_report_to_markdown

PAGE_TITLE = "OPRA.AI"
ENGINE_VERSION = "0.1.0"


def _utc_midnight(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def main() -> None:
    """Collect explicit inputs and display/download pipeline results."""
    st.set_page_config(page_title=PAGE_TITLE)
    st.title(PAGE_TITLE)
    st.caption("Operational Performance and Recommendation Analytics")
    uploaded = st.file_uploader("Automotive service CSV", type=("csv",))
    today = datetime.now(UTC)
    start_date = st.date_input("Period start (UTC, inclusive)", today.date() - timedelta(days=30))
    last_date = st.date_input("Last included day (UTC)", today.date() - timedelta(days=1))
    reference_date = st.date_input("Source snapshot date (UTC)", today.date())
    reference_time = st.time_input("Source snapshot time (UTC)", today.time().replace(tzinfo=None))
    compare = st.checkbox(
        "Compare with the immediately preceding equal-duration period", value=True
    )
    if uploaded is None:
        st.info("Upload a CSV and set the period and source snapshot time to run analytics.")
        return
    start = _utc_midnight(start_date)
    end = _utc_midnight(last_date + timedelta(days=1))
    reference = datetime.combine(reference_date, reference_time, tzinfo=UTC)
    generated = datetime.now(UTC)
    try:
        period = ReportingPeriod(start, end)
        duration = end - start
        baseline = ReportingPeriod(start - duration, start) if compare else None
        result = run_analytics(
            uploaded.getvalue(),
            OpraConfig(),
            period,
            reference,
            generated,
            ENGINE_VERSION,
            baseline,
        )
    except OpraError as exc:
        st.error(
            f"Processing could not be completed ({type(exc).__name__}). Check the file and selected period."
        )
        return
    st.subheader("KPIs")
    st.dataframe(
        [
            {
                "KPI": item.kpi_id,
                "Name": item.name,
                "Unit": item.unit,
                "Status": item.metric_value.status.value,
                "Value": str(item.metric_value.value)
                if item.metric_value.value is not None
                else None,
            }
            for item in result.metrics
            if item.period == result.current_period
        ],
        use_container_width=True,
    )
    st.subheader("Findings")
    if result.findings:
        for finding in result.findings:
            st.write(
                f"{finding.finding_id}: {finding.title} ({finding.evidence_tier.value} evidence)"
            )
            for recommendation in result.recommendations:
                if recommendation.finding_id == finding.finding_id:
                    st.write(recommendation.text)
    else:
        st.write("No findings were triggered.")
    st.download_button(
        "Download JSON", integrated_report_to_json(result), "opra-report.json", "application/json"
    )
    st.download_button(
        "Download Markdown",
        integrated_report_to_markdown(result),
        "opra-report.md",
        "text/markdown",
    )


if __name__ == "__main__":
    main()
