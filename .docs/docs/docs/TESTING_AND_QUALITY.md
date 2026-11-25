# OPRA.AI — Testing and Quality Assurance Strategy

**Document ID:** `OPRA-DOC-06`  
**Version:** `0.1.0-draft`  
**Status:** Draft (Consolidated from Approved Governance Baseline; Execution Verification Pending)  
**Last Updated:** 2026-11-25  
**Related Documents:** [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | [PYTHON_ENGINEERING_STANDARDS.md](PYTHON_ENGINEERING_STANDARDS.md) | [DEPLOYMENT_AND_OPERATIONS.md](DEPLOYMENT_AND_OPERATIONS.md)

## 1. Purpose and Scope

This document defines OPRA.AI's testing taxonomy, fixture conventions, mandatory local/CI quality gates, and failure diagnosis workflow. A passing test suite confirms regression and structural checks—it must not be mistaken for proof that unimplemented requirements are satisfied.

## 2. Test Suite Organization

| Directory / File | Responsibility |
| :--- | :--- |
| `tests/conftest.py` | Shared fixtures (`reference_utc_timestamp`, `sample_csv_text`, `sample_csv_file`) free of unimplemented domain imports. |
| `tests/unit/` | Isolated tests for configuration validation, deep model immutability, normalization, KPI calculations, rules, and exporters. |
| `tests/integration/` | End-to-end headless pipeline runs (`Ingestion -> Reporting`), `ConfigSnapshot` isolation, and deterministic reproducibility checks. |
| `tests/app/` | Streamlit presentation tests (`AppTest`) and AST/import architectural boundary checks (`test_architecture_boundaries.py`). |
| `tests/sample_data/` | Synthetic automotive service datasets covering clean rows, exact/conflicting `job_id` duplicates, maturity boundaries, and multi-period comparisons. |

## 3. Core Testing Rules

* **Deep Immutability Verification:** Test both top-level `FrozenInstanceError` on attribute assignment and nested isolation (`TypeError` on `MappingProxyType` writes, plus mutating caller-owned input lists/dicts after model creation).
* **Zero vs. Missing (`None` / `N/A`) Verification:** Explicitly assert that missing/inapplicable metrics return `None` (`N/A` in rendered output) and never silently coerce to `0`.
* **Deterministic Time:** Inject fixed timezone-aware timestamps (`reference_utc_timestamp`) rather than calling wall-clock `datetime.now()` inside tests.
* **Synthetic Fixtures Only:** Never place real customer, vehicle, or workshop records in `tests/` or `examples/`.

## 4. Mandatory Quality Gate Commands

Every change must satisfy all four checks locally and in GitHub Actions CI (`.github/workflows/ci.yml`):

```bash
uv run ruff check .