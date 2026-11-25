# OPRA.AI — Project Foundation

**Document ID:** `OPRA-DOC-01`  
**Version:** `0.1.0-draft`  
**Status:** Draft (Consolidated from Approved Governance Baseline; Execution Verification Pending)  
**Last Updated:** 2026-11-25  
**Related Documents:** [README.md](../README.md) | [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | [TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md) | [SECURITY_AND_DATA_GOVERNANCE.md](SECURITY_AND_DATA_GOVERNANCE.md)

## 1. Purpose and Scope

This document defines the strategic purpose, business context, MVP scope boundaries, and product principles for **OPRA.AI** (Operational Performance and Recommendation Analytics). It establishes the foundation for implementation without authorizing unverified runtime behavior or unapproved scope expansion.

## 2. Vision and Problem Statement

* **Vision:** Build a deterministic operational analytics and recommendation platform starting with **automotive service businesses** and scaling over time to support multi-industry operational workflows.
* **Operational Problem:** Service businesses frequently track work orders, turnaround times, billing, and job statuses in spreadsheets or fragmented logs without consistent validation, period comparisons, sample-size context, or reproducible recommendations.
* **Core Approach:** Turn structured workshop records into deterministic metrics, evidence-backed findings, prioritized recommendations, and exportable JSON and Markdown reports using a stateless Python engine decoupled from the Streamlit presentation layer.

## 3. Target Users and Initial Focus

* **Initial Industry Focus:** Automotive service operations (workshops, service bays, repair/maintenance job logs).
* **Primary Personas:**
  * **Workshop / Operations Manager:** Reviews operational health, cycle/turnaround bottlenecks, period-over-period shifts, and actionable recommendations.
  * **Technical / Data Reviewer:** Audits data ingestion constraints, quarantined/conflicting records, confidence limits, and reproducible report outputs.
  * **Developer / Maintainer:** Extends modules, tests, and documentation under approved architectural boundaries.
* **Multi-Industry Horizon:** Domain-specific schemas, categories, and rule sets are structured so future industry adapters can be evaluated under separate governance rather than hardcoded into core orchestration.

## 4. MVP Scope vs. Future Capabilities

### MVP Scope (In Scope)
* Stateless, in-memory processing of uploaded UTF-8 CSV data within configured upload and row limits.
* Deterministic pipeline flow: `Ingestion -> Validation -> Processing -> Analytics -> Intelligence -> Recommendations -> Reporting`.
* Standardized KPI outputs, deterministic findings with sample size/confidence context, prioritized recommendations, and JSON/Markdown report exports.
* Thin Streamlit presentation shell (`src/opra/app/main.py`) delegating execution to headless Python modules.

### Future / Out-of-Scope Capabilities (Requires Separate Approval)
* Mandatory database or persistent storage layers (`storage/` remains optional/reserved for approved post-MVP phases).
* Cross-session dataset caching or shared mutable state across user sessions.
* Authentication, authorization, multi-tenant access controls, or external third-party API integrations.
* Production deployment claims prior to completing verification gates in [DEPLOYMENT_AND_OPERATIONS.md](DEPLOYMENT_AND_OPERATIONS.md).

## 5. Constraints, Assumptions, and Success Criteria

* **Technical Constraints:** Python `>=3.11`, `uv` dependency/lockfile management (`pyproject.toml` and `uv.lock`), `streamlit` restricted to presentation, strict `mypy`, `ruff`, `pytest`, and at least `80%` test coverage (`--cov=opra --cov-fail-under=80`).
* **Data & Precision Constraints:** `Decimal` for precision-sensitive values; explicit distinction between `None` (absent/unavailable), `N/A` (not applicable), and genuine `0`.
* **Success Criteria:** Verified baseline quality gates (Step 7), deeply immutable domain contracts (`OPRA-MODELS-001`), deterministic reproducible outputs across runs, and clean separation between UI and analytical logic.

## 6. Unresolved Decisions

* Final automotive job/work-order CSV schema, KPI formula catalogue, and rule/confidence thresholds (to be locked prior to module implementation).
* Exact scope and timing of post-MVP persistence or multi-industry modules.

## 7. Revision History

| Version | Date | Summary |
| :--- | :--- | :--- |
| `0.1.0-draft` | 2026-11-25 | Consolidated project foundation from approved governance baseline and initialization register. |