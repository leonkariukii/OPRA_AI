# OPRA.AI — Product Requirements

**Document ID:** `OPRA-DOC-02`  
**Version:** `0.1.0-draft`  
**Status:** Draft (Consolidated from Approved Governance Baseline; Execution Verification Pending)  
**Last Updated:** 2026-11-25  
**Related Documents:** [PROJECT_FOUNDATION.md](PROJECT_FOUNDATION.md) | [TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md) | [DATA_AND_ANALYTICS.md](DATA_AND_ANALYTICS.md) | [TESTING_AND_QUALITY.md](TESTING_AND_QUALITY.md)

## 1. Purpose and Scope

This document defines testable functional and non-functional requirements for the OPRA.AI MVP. Requirement IDs provide traceability across design, implementation, and automated tests.

## 2. Functional Requirements

| ID | Category | Requirement | Testable Acceptance Condition |
| :--- | :--- | :--- | :--- |
| `FR-ING-01` | Ingestion | Accept UTF-8 CSV input and enforce `max_upload_bytes` (`10 * 1024 * 1024` default) and `max_rows` (`100_000` default). | Oversized byte payloads or row counts exceeding `max_rows` fail deterministically with a clear error. |
| `FR-VAL-01` | Validation | Validate required structure/fields and isolate exact vs. conflicting `job_id` duplicates (quarantining all rows of conflicting IDs). | Conflicting duplicate `job_id` rows are excluded from valid analytical cohorts and recorded in quarantine output. |
| `FR-PRC-01` | Processing | Normalize domain fields, define reporting periods, and apply maturity rules (`maturity_buffer_days`, default `3`). | Immature records within the maturity buffer are handled per period/maturity rules without mutating input data. |
| `FR-ANA-01` | Analytics | Compute deterministic KPI metrics and period-over-period comparisons using `Decimal` and explicit `None` / `N/A` vs. `0` semantics. | Missing metrics yield `None` (`N/A` in display) rather than `0`, and `Decimal` precision is preserved. |
| `FR-INT-01` | Intelligence | Evaluate deterministic rules using `ConfigSnapshot` thresholds (including `min_sample_size`, default `10`) and report sample size and confidence. | Findings expose sample size, confidence indicators, and explicit limitations when sample size is small or data is missing. |
| `FR-REC-01` | Recommendations | Generate prioritized, actionable recommendations linked to findings and data caveats. | Recommendations order deterministically and surface underlying data limitations. |
| `FR-RPT-01` | Reporting | Produce reproducible JSON and Markdown outputs including execution metadata (`generated_at_utc`, `engine_version`, `ConfigSnapshot`). | Re-running identical inputs and configuration produces deterministic analytical content and valid metadata. |
| `FR-APP-01` | Presentation | Render Streamlit UI in `src/opra/app/` without embedding KPI math, validation rules, or cross-session dataset caching. | Core modules pass AST/import boundary checks with zero `streamlit` imports; session state stays isolated. |

## 3. Non-Functional Requirements

| ID | Category | Requirement | Target / Verification Gate |
| :--- | :--- | :--- | :--- |
| `NFR-01` | Determinism & Statelessness | Run statelessly in memory per execution with no database or cross-session dataset cache. | Repeated runs on identical input produce identical analytical outputs. |
| `NFR-02` | Immutability & Type Safety | Enforce frozen models (`tuple`, `MappingProxyType`), strict `mypy`, and `ruff` checks. | `ruff check .`, `ruff format --check .`, and `mypy src/opra` exit `0`. |
| `NFR-03` | Test Coverage | Maintain at least `80%` test coverage across `opra`. | `pytest --cov=opra --cov-report=term-missing --cov-fail-under=80` passes. |
| `NFR-04` | Performance | Process `50,000` synthetic rows within benchmark budget (`< 5.0s` under approved benchmark conditions). | Verified via `scripts/benchmark_pipeline.py` as a release benchmark gate. |
| `NFR-05` | Security & Privacy | Avoid committing secrets, avoid cross-session data leakage, and avoid logging PII or raw customer/garage rows. | Verified via governance checks, `.gitignore`, and unit/app tests. |

## 4. Unresolved Decisions

* Exact required CSV column names, allowed enum values, and parsing edge cases (`FR-ING-01`, `FR-VAL-01`, `FR-PRC-01`).
* Exact KPI identifiers, formulas, confidence levels, and recommendation prioritization rules (`FR-ANA-01`, `FR-INT-01`, `FR-REC-01`).

## 5. Revision History

| Version | Date | Summary |
| :--- | :--- | :--- |
| `0.1.0-draft` | 2026-11-25 | Authored initial testable `FR-*` and `NFR-*` requirement set aligned to approved baseline. |