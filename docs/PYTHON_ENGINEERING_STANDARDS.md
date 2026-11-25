# OPRA.AI — Python Engineering Standards

**Document ID:** `OPRA-DOC-05`  
**Version:** `0.1.0-draft`  
**Status:** Draft (Consolidated from Approved Governance Baseline; Execution Verification Pending)  
**Last Updated:** 2026-11-25  
**Related Documents:** [TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md) | [DATA_AND_ANALYTICS.md](DATA_AND_ANALYTICS.md) | [TESTING_AND_QUALITY.md](TESTING_AND_QUALITY.md) | [SECURITY_AND_DATA_GOVERNANCE.md](SECURITY_AND_DATA_GOVERNANCE.md)

## 1. Purpose and Scope

This document defines mandatory Python coding, typing, immutability, configuration, and tooling standards for all code under `src/opra/`, `tests/`, and `scripts/`.

## 2. Runtime, Dependencies, and Tooling

* **Python Version:** Target `Python >=3.11` consistently across `pyproject.toml`, local development, and GitHub Actions CI.
* **Dependency Management:** Use `uv` with `pyproject.toml` as the configuration source and `uv.lock` as the canonical lockfile. Do not add runtime dependencies without explicit architectural approval.
* **Presentation Isolation:** `streamlit` is allowed only inside `src/opra/app/` and UI-focused tests in `tests/app/`. Core modules (`core/`, `models/`, `pipeline/`, `ingestion/`, `validation/`, `processing/`, `analytics/`, `intelligence/`, `recommendations/`, `reporting/`, `storage/`) must never import `streamlit`.

## 3. Typing, Formatting, and Static Analysis

* **Explicit Type Annotations:** Annotate all function parameters, return types, class attributes, and module constants. Avoid `Any` unless strictly justified and isolated.
* **Strict Mypy:** All code in `src/opra/` must pass `uv run mypy src/opra` under strict type-checking rules with zero errors.
* **Ruff Linting & Formatting:** All repository Python files must pass `uv run ruff check .` and `uv run ruff format --check .` without warnings or diffs.

## 4. Deep Immutability & Data Representation

* **Frozen Models:** All domain contracts and snapshots must use `@dataclass(frozen=True)`.
* **Deep Immutability:** Frozen dataclasses alone do not protect nested mutable containers.
  * Store sequences as `tuple` (never `list`).
  * Wrap mappings in `MappingProxyType` (never expose raw `dict`).
  * Copy/convert caller-supplied collections at construction so mutating caller inputs afterward cannot mutate the model.
  * Never use mutable default arguments.
* **Numerical Precision:** Use `Decimal` for monetary values, rates, ratios, and precision-sensitive deltas. Avoid binary `float` arithmetic for KPI calculations and define rounding rules explicitly where rounding occurs.
* **Missing Values:** Preserve the explicit three-way distinction between `None` (absent/unavailable), `N/A` (not applicable), and genuine `0` / `Decimal("0")`.
* **Temporal Handling:** Use timezone-aware UTC `datetime` objects (`timezone.utc`) for reference timestamps; avoid naive datetimes or implicit local timezone assumptions.

## 5. Configuration, Exceptions, and Logging

* **Centralized Configuration:** All operational limits and defaults (`max_upload_bytes = 10 * 1024 * 1024`, `max_rows = 100_000`, `maturity_buffer_days = 3`, `min_sample_size = 10`) live in `src/opra/core/config.py` (`OpraConfig` and `ConfigSnapshot`).
* **Fail-Fast Validation:** Invalid configuration values must raise `ConfigurationError` immediately—never silently clamp or fall back to defaults.
* **Exception Hierarchy:** Inherit domain errors from `OpraError` (`src/opra/core/exceptions.py`) with actionable, non-sensitive messages.
* **PII-Safe Logging:** Log structural execution events and metrics via `src/opra/core/logging.py`; never log secrets, raw CSV rows, or customer/vehicle identifiers.

## 6. Architectural Restraint

* Keep modules focused and cohesive without premature abstractions or speculative plugin frameworks.
* Keep `src/opra/app/main.py` minimal and free of business logic, data transformation, or analytical rules.

## 7. Unresolved Decisions

* Specific `Decimal` quantization/rounding modes per KPI once formulas are locked in [DATA_AND_ANALYTICS.md](DATA_AND_ANALYTICS.md).

## 8. Revision History

| Version | Date | Summary |
| :--- | :--- | :--- |
| `0.1.0-draft` | 2026-11-25 | Consolidated Python 3.11+, immutability, Decimal, typing, and Ruff/Mypy standards. |