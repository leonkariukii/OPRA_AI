"""In-memory orchestration for approved deterministic automotive analytics."""

from datetime import datetime

from opra.analytics.comparisons import compare_kpis
from opra.analytics.kpi_engine import calculate_kpis
from opra.core.config import ConfigSnapshot, OpraConfig
from opra.ingestion.csv_loader import IngestionResult, ingest_csv
from opra.intelligence.engine import evaluate_findings
from opra.models.analytics import AnalysisLimitation
from opra.models.periods import ReportingPeriod
from opra.models.reporting import IngestionSummary, IntegratedReportDocument
from opra.recommendations.engine import recommend


def run_analytics(
    csv_data: bytes,
    config: ConfigSnapshot | OpraConfig,
    current_period: ReportingPeriod,
    reference_utc_timestamp: datetime,
    generated_at_utc: datetime,
    engine_version: str,
    baseline_period: ReportingPeriod | None = None,
) -> IntegratedReportDocument:
    """Ingest one CSV payload and calculate current/baseline integrated output."""
    snapshot = config.snapshot() if isinstance(config, OpraConfig) else config
    ingestion: IngestionResult = ingest_csv(csv_data, snapshot)
    current = calculate_kpis(
        ingestion.valid_records, current_period, reference_utc_timestamp, snapshot
    )
    baseline = (
        calculate_kpis(ingestion.valid_records, baseline_period, reference_utc_timestamp, snapshot)
        if baseline_period
        else None
    )
    comparisons = compare_kpis(current.metrics, baseline.metrics if baseline else None)
    intelligence = evaluate_findings(comparisons, snapshot)
    recommendations = recommend(intelligence.findings)
    limitation_counts: dict[tuple[str, str | None], int] = {}
    for limitation in (
        *current.limitations,
        *(baseline.limitations if baseline else ()),
        *intelligence.limitations,
    ):
        key = (limitation.code, limitation.metric_id)
        limitation_counts[key] = limitation_counts.get(key, 0) + limitation.count
    limitations = tuple(
        AnalysisLimitation(code, count, metric_id)
        for (code, metric_id), count in sorted(limitation_counts.items())
    )
    summary = IngestionSummary(
        "success",
        ingestion.total_processed_record_count,
        ingestion.accepted_record_count,
        ingestion.rejected_record_count,
        ingestion.exact_duplicate_count,
        ingestion.conflicting_duplicate_count,
        ingestion.quarantined_record_count,
    )
    return IntegratedReportDocument(
        generated_at_utc,
        reference_utc_timestamp,
        engine_version,
        snapshot,
        summary,
        current_period,
        baseline_period,
        current.metrics + (baseline.metrics if baseline else ()),
        comparisons,
        intelligence.findings,
        recommendations,
        limitations,
    )
