"""Deterministic KPI and period-comparison calculations."""

from opra.analytics.comparisons import compare_kpis
from opra.analytics.kpi_engine import KPIComputation, calculate_kpis

__all__ = ["KPIComputation", "calculate_kpis", "compare_kpis"]
