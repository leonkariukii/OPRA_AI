# OPRA.AI — Data and Analytics Specification

**Document ID:** `OPRA-DOC-04`  
**Version:** `0.1.0-draft`  
**Status:** Draft (Consolidated from Approved Governance Baseline; Execution Verification Pending)  
**Last Updated:** 2026-11-25  
**Related Documents:** [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | [TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md) | [PYTHON_ENGINEERING_STANDARDS.md](PYTHON_ENGINEERING_STANDARDS.md)

## 1. Purpose and Scope

This document defines data representation rules, duplicate and missing-value handling, period/maturity semantics, and the analytical structure for OPRA.AI. Where exact domain schemas or KPI formulas are not yet locked, they are explicitly marked as unresolved rather than invented.

## 2. Ingestion, Validation, and Duplicate Handling

* **Input Source:** UTF-8 CSV data within `ConfigSnapshot.max_upload_bytes` (`10 * 1024 * 1024` default) and `ConfigSnapshot.max_rows` (`100_000` default).
* **Duplicate `job_id` Policy:**
  * **Exact Duplicates:** Identical records sharing a `job_id` are handled deterministically per validation/normalization rules.
  * **Conflicting Duplicates:** Rows sharing a `job_id` with conflicting field values are quarantined (all conflicting rows for that `job_id` are excluded from clean analytical cohorts and recorded in quarantine diagnostics).

## 3. Missing-Value and Numerical Precision Semantics

* **Three-Way Value Distinction:**
  * `None`: Data is absent, missing, or unavailable (rendered as `N/A` in human-readable/Markdown displays where applicable).
  * `N/A`: Metric or rule is not applicable to the record, cohort, or period comparison.
  * `Decimal("0")` (or numeric zero): A genuine measured value of zero—never conflated with `None` or `N/A`.
* **Precision:** Financial amounts, rates, ratios, and deltas use `Decimal` rather than unguarded binary `float` arithmetic.

## 4. Reporting Periods and Maturity Semantics

* **Deterministic Temporal Windows:** Reporting periods and period-over-period comparisons use explicit date/timestamp boundaries and timezone-aware UTC reference points (`reference_utc_timestamp` in tests; explicit UTC timestamps in runs).
* **Maturity Buffer:** `maturity_buffer_days` (default `3`, non-negative integer) governs whether recent jobs/outcomes are mature enough for certain completion/turnaround or outcome evaluations relative to the evaluation reference date.

## 5. Analytical, Intelligence, and Reporting Contract Structure

Each analytical method, KPI, finding rule, and recommendation rule must document:

* **Purpose:** What operational question or performance dimension it addresses.
* **Required Inputs:** Normalized fields, period definitions, and `ConfigSnapshot` parameters (including `min_sample_size`, default `10`).
* **Calculation / Rule Method:** Deterministic `Decimal` calculation or rule logic.
* **Output:** Immutable model instance with explicit values or `None` / `N/A`.
* **Edge Cases & Missing Data:** Zero-denominator cases, empty cohorts, immature records, conflicting duplicates, and small sample sizes (`n < min_sample_size`).
* **Validation & Testing Criteria:** Unit and integration test expectations.
* **Report Metadata:** Every exported JSON/Markdown report carries `generated_at_utc`, `engine_version`, and `ConfigSnapshot` metadata for reproducibility.

## 6. Unresolved Decisions (Explicitly Open Before Implementation)

* **Canonical Record & Period Schemas:** Exact column names, data types, allowed statuses/categories, and period boundary rules for `records.py` and `periods.py`.
* **KPI Catalogue & Identifiers:** Exact KPI IDs (e.g., `KPI-01` through `KPI-06` and any additional metrics), formulas, and rounding rules in `analytics.py` / `kpi_engine.py`.
* **Confidence & Recommendation Rules:** Exact confidence tier definitions, sample-size thresholds beyond `min_sample_size`, and recommendation ranking/prioritization criteria in `intelligence.py` and `recommender.py`.

## 7. Revision History

| Version | Date | Summary |
| :--- | :--- | :--- |
| `0.1.0-draft` | 2026-11-25 | Consolidated data semantics, duplicate/maturity rules, and open schema/KPI decisions. |