# AGENTS.md — Engineering Instructions for AI Coding Agents on OPRA.AI

**Document ID:** `OPRA-AGENTS-01`  
**Version:** `0.1.0-draft`  
**Status:** Draft (Consolidated from Approved Governance Baseline; Execution Verification Pending)  
**Last Updated:** 2026-11-25  
**Authoritative References:** [README.md](README.md) | [PROJECT_FOUNDATION.md](docs/PROJECT_FOUNDATION.md) | [PRODUCT_REQUIREMENTS.md](docs/PRODUCT_REQUIREMENTS.md) | [TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md) | [DATA_AND_ANALYTICS.md](docs/DATA_AND_ANALYTICS.md) | [PYTHON_ENGINEERING_STANDARDS.md](docs/PYTHON_ENGINEERING_STANDARDS.md) | [TESTING_AND_QUALITY.md](docs/TESTING_AND_QUALITY.md) | [SECURITY_AND_DATA_GOVERNANCE.md](docs/SECURITY_AND_DATA_GOVERNANCE.md) | [DEPLOYMENT_AND_OPERATIONS.md](docs/DEPLOYMENT_AND_OPERATIONS.md)

## 1. Project Context and Role

You are acting as a disciplined engineering partner on **OPRA.AI** (Operational Performance and Recommendation Analytics)—a deterministic operational analytics and recommendation platform starting with **automotive service businesses** and designed to evolve toward multi-industry operational analytics.

Read the relevant governance and task documents before making changes. Treat documented decisions as authoritative rather than guessing missing rules or requirements.

## 2. Locked Technology and Architecture Decisions

* **Runtime & Tooling:** Python `>=3.11`, `uv` dependency management (`pyproject.toml` as source of truth, `uv.lock` as canonical lockfile), `streamlit` (presentation layer only), `ruff`, `mypy` (strict mode), `pytest`, `pytest-cov` (`80%` minimum coverage threshold on package `opra`), and GitHub Actions CI.
* **Canonical Entrypoint:** `src/opra/app/main.py` remains a thin Streamlit presentation shell and must not contain KPI math, validation rules, or direct business logic.
* **Unidirectional Architecture & Pipeline Order:**
  * Presentation (`src/opra/app/`) delegates to pipeline orchestration (`src/opra/pipeline/runner.py`).
  * Core processing services execute in order: `ingestion -> validation -> processing -> analytics -> intelligence -> recommendations -> reporting`.
  * Domain models (`src/opra/models/`) and core configuration/exceptions/logging (`src/opra/core/`) serve as shared contracts across modules—not as a stage after reporting.
  * `src/opra/storage/` is an optional post-MVP persistence boundary and must not be implemented as a mandatory MVP database.
* **Stateless & Deeply Immutable MVP:** Process in memory per execution without cross-session dataset caching. Enforce deep immutability (`@dataclass(frozen=True)`, `tuple`, `MappingProxyType`), explicit `Decimal` precision, and explicit distinction between `None` (absent/unavailable), `N/A` (not applicable), and genuine `0`.
* **Approved Configuration Limits:** `max_upload_bytes = 10 * 1024 * 1024` (`> 0`), `max_rows = 100_000` (`> 0`), `maturity_buffer_days` default `3` (`>= 0`), and `min_sample_size` default `10` (`> 0`), with fail-fast `ConfigurationError` validation and immutable `ConfigSnapshot`.

## 3. Repository Conventions and Module Responsibilities

* Keep canonical documentation in `docs/` at the repository root (consolidate or avoid unintended nested `.docs/docs/...` paths).
* Place task specifications under `docs/tasks/` before implementing code for a task.
* Keep tests organized under `tests/unit/`, `tests/integration/`, `tests/app/`, and `tests/sample_data/`, with shared fixtures in `tests/conftest.py`.

## 4. Handling Ambiguity, Scope, and Verification

* **Never Invent Requirements or Claim Unrun Checks:** If a schema, KPI formula, rounding rule, or threshold is marked unresolved in `docs/`, record it as an open decision rather than inventing arbitrary business rules. Never claim a command or CI job passed unless it was actually executed and its output reviewed.
* **Respect Task Gates:** Do not advance past a blocked gate (such as running `OPRA-MODELS-001` before Step 7 baseline verification passes) or add unapproved runtime dependencies.
* **Definition of Done:** A task is complete only when all required files and tests exist, all quality gates (`ruff check .`, `ruff format --check .`, `mypy src/opra`, and `pytest --cov=opra --cov-report=term-missing --cov-fail-under=80`) pass, architectural boundaries remain intact, and changes are reviewed and approved.

## 5. Git and Change Management

* Never commit `.env`, secrets, credentials, or raw customer/garage data.
* Keep changes small, scoped to the active task, and consistent across code, configuration, and documentation.