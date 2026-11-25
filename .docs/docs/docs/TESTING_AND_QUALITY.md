# OPRA.AI — Testing and Quality Assurance Strategy

**Document ID:** `OPRA-DOC-06`  
**Version:** `0.1.0-draft`  
**Status:** Draft (Consolidated from Approved Governance Baseline; Execution Verification Pending)  
**Last Updated:** 2026-11-25  
**Related Documents:** [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | [PYTHON_ENGINEERING_STANDARDS.md](PYTHON_ENGINEERING_STANDARDS.md) | [SECURITY_AND_DATA_GOVERNANCE.md](SECURITY_AND_DATA_GOVERNANCE.md) | [DEPLOYMENT_AND_OPERATIONS.md](DEPLOYMENT_AND_OPERATIONS.md)

## 1. Purpose and Scope

This document defines OPRA.AI's testing strategy, fixture conventions, mandatory quality gates, and failure diagnosis procedures. Passing tests verify implemented behavior and regression guardrails—they must never be treated as proof that unimplemented requirements are complete.

## 2. Test Layers and Directory Layout

| Path | Scope & Purpose |
| :--- | :--- |
| `tests/conftest.py` | Shared pytest fixtures (`reference_utc_timestamp`, `sample_csv_text`, `sample_csv_file`) without importing unimplemented domain models. |
| `tests/unit/` | Unit tests for `OpraConfig`, `ConfigSnapshot`, deep model immutability, validation/quarantine, normalization, KPI calculations, rules, and exporters. |
| `tests/integration/` | Multi-stage headless pipeline tests (`Ingestion -> Reporting`), snapshot isolation, deterministic replay, and boundary/error handling. |
| `tests/app/` | Streamlit UI rendering/session tests and architectural boundary tests (`test_architecture_boundaries.py` checking imports and no `streamlit` in core modules). |
| `tests/sample_data/` | Reusable synthetic automotive datasets covering normal jobs, exact/conflicting `job_id` duplicates, maturity cutoffs, and multi-period comparisons. |

## 3. Core Testing Standards

* **Deep Immutability:** Verify both top-level `FrozenInstanceError` on attribute assignment and nested immutability (`TypeError` on `MappingProxyType` writes, plus mutating caller-owned input lists/dicts after model creation to confirm no state leakage).
* **Zero vs. Missing (`None` / `N/A`) Semantics:** Explicitly test that absent or inapplicable values stay `None` (`N/A` in display) rather than silently becoming `0`.
* **Deterministic Time & Synthetic Data:** Use `reference_utc_timestamp` and synthetic fixtures rather than wall-clock `datetime.now()` or real customer/garage data.

## 4. Mandatory Quality Gate Commands

Run all four quality gates locally and in GitHub Actions CI (`.github/workflows/ci.yml`):

```bash
uv run ruff check .
Bash
uv run ruff format --check .
Bash
uv run mypy src/opra
Bash
uv run pytest --cov=opra --cov-report=term-missing --cov-fail-under=80