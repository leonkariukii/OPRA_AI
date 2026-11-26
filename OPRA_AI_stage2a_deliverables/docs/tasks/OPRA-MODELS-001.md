# OPRA-MODELS-001 — Core Configuration and Immutable Domain Models

**Task ID:** `OPRA-MODELS-001`  
**Version:** `0.2.0-draft`  
**Status:** Partially Implemented (Stage 2A) — Configuration complete; Domain Models Blocked on Unresolved Decisions.  
**Last Updated:** 2026-11-26  
**Related Documents:** [PROJECT_FOUNDATION.md](../PROJECT_FOUNDATION.md) | [PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md) | [TECHNICAL_DESIGN.md](../TECHNICAL_DESIGN.md) | [DATA_AND_ANALYTICS.md](../DATA_AND_ANALYTICS.md) | [PYTHON_ENGINEERING_STANDARDS.md](../PYTHON_ENGINEERING_STANDARDS.md) | [TESTING_AND_QUALITY.md](../TESTING_AND_QUALITY.md) | [SECURITY_AND_DATA_GOVERNANCE.md](../SECURITY_AND_DATA_GOVERNANCE.md) | [AGENTS.md](../../AGENTS.md)

> **Stage 2A note.** The owner authorized Stage 2A implementation of this task. Only the parts supported by approved documentation were implemented (section 9). Items in section 4 that are still open block the remaining files; they must not be invented. Step 7 criteria remain undefined in the repository (`D-12`); the owner's authorization is taken as the gate decision.

## 1. Objective

Establish the shared, deeply immutable contracts that every later pipeline stage depends on: centralized configuration with fail-fast validation, a stable per-run configuration snapshot, and typed domain models for records, reporting periods, analytics results, and intelligence results.

No pipeline behavior is implemented by this task.

## 2. Scope

### 2.1 Intended implementation files

| File | Contents |
| :--- | :--- |
| `src/opra/core/config.py` | `OpraConfig` and `ConfigSnapshot`, with configuration validation. **Implemented.** |
| `src/opra/core/exceptions.py` | `OpraError` and `ConfigurationError` (added to scope; see `D-07`). **Implemented.** |
| `src/opra/models/records.py` | Record domain models. **Blocked** (`D-01`). |
| `src/opra/models/periods.py` | Reporting-period domain models. **Blocked** (`D-02`). |
| `src/opra/models/analytics.py` | Analytics result models. **Blocked** (`D-03`, `D-06`). |
| `src/opra/models/intelligence.py` | Intelligence result models (findings and, per [TECHNICAL_DESIGN.md](../TECHNICAL_DESIGN.md) section 2, recommendations). **Blocked** (`D-04`). |

### 2.2 Explicitly out of scope

* Ingestion, validation, processing, analytics algorithms, intelligence rules, recommendation logic, reporting/exporters, and pipeline orchestration.
* Any persistence, database, disk retention, or external data transmission.
* Any new dependency (including Pydantic) and any edit to `pyproject.toml` or `uv.lock`.
* Any import of `streamlit` outside `src/opra/app/`. Domain models and configuration must not depend on Streamlit.
* Changes to `src/opra/app/main.py`, CI configuration, or approved configuration limits.

## 3. Requirements

### 3.1 Configuration (`src/opra/core/config.py`)

Sources: [PYTHON_ENGINEERING_STANDARDS.md](../PYTHON_ENGINEERING_STANDARDS.md) section 5, [AGENTS.md](../../AGENTS.md) section 2, [DATA_AND_ANALYTICS.md](../DATA_AND_ANALYTICS.md) sections 2 and 4.

| Setting | Default | Constraint |
| :--- | :--- | :--- |
| `max_upload_bytes` | `10 * 1024 * 1024` | `> 0` |
| `max_rows` | `100_000` | `> 0` |
| `maturity_buffer_days` | `3` | `>= 0` (non-negative integer) |
| `min_sample_size` | `10` | `> 0` |

* `OpraConfig` holds the validated operational limits. `ConfigSnapshot` is the immutable effective configuration captured for a processing run.
* Both must be `@dataclass(frozen=True)`.
* Invalid values must raise `ConfigurationError` immediately. Values must never be silently clamped or replaced with defaults.
* A snapshot, once created, must not change if the source configuration object or any caller-supplied collection is later changed.
* The defaults above must live only in `config.py`; other modules must not hard-code them.

### 3.2 Domain models (`src/opra/models/`)

Common rules (from [PYTHON_ENGINEERING_STANDARDS.md](../PYTHON_ENGINEERING_STANDARDS.md) section 4 and [DATA_AND_ANALYTICS.md](../DATA_AND_ANALYTICS.md) section 3):

* `@dataclass(frozen=True)` for every model.
* Deep immutability: sequences stored as `tuple`, mappings wrapped in `MappingProxyType`, caller-supplied collections copied/converted at construction, no mutable default arguments.
* `Decimal` for monetary values, rates, ratios, and precision-sensitive deltas; no binary `float` arithmetic for KPI values.
* Timezone-aware UTC `datetime` for reference timestamps; no naive datetimes or implicit local-time assumptions.
* Three-way value semantics preserved: `None` (absent/unavailable), `N/A` (not applicable), and genuine zero (`Decimal("0")`), which must never be conflated.
* Explicit type annotations on all parameters, return types, attributes, and module constants; must pass strict `mypy`.
* Model invariants are validated at construction and raise a clear, non-sensitive error on violation.

Known semantic requirements per model family (these constrain the design but do **not** define fields):

| File | What the approved documents establish |
| :--- | :--- |
| `records.py` | Records carry a `job_id`; exact and conflicting duplicates exist; conflicting rows are quarantined with diagnostics. Decimal precision for financial amounts. |
| `periods.py` | Reporting periods use explicit, timezone-aware UTC boundaries and support period-over-period comparison; maturity is evaluated relative to a reference timestamp using `maturity_buffer_days`. |
| `analytics.py` | KPI results are deterministic, expose a value or an explicit `None` / `N/A`, and preserve `Decimal` precision. |
| `intelligence.py` | Findings expose sample size, confidence indicators, and explicit limitations when `n < min_sample_size` or data is missing. Recommendations link to findings and data caveats and order deterministically. |

## 4. Unresolved Decisions (Must Be Resolved Before or During Authorization)

The approved documents mark these items as open. Per [AGENTS.md](../../AGENTS.md) section 4, they must **not** be invented during implementation. The human owner must decide each one, or explicitly approve a recorded default, before the affected model is implemented.

| ID | Open decision | Source |
| :--- | :--- | :--- |
| `D-01` | Canonical record schema: field names, data types, required vs. optional fields, allowed statuses/categories. Blocks `records.py`. | [DATA_AND_ANALYTICS.md](../DATA_AND_ANALYTICS.md) section 6; [PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md) section 4 |
| `D-02` | Reporting-period schema and boundary rules (inclusive/exclusive ends, period length, comparison pairing). Blocks `periods.py`. | [DATA_AND_ANALYTICS.md](../DATA_AND_ANALYTICS.md) section 6 |
| `D-03` | KPI identifiers (e.g. `KPI-01`–`KPI-06` and any others), formulas, units, and rounding rules. Blocks `analytics.py` result fields. | [DATA_AND_ANALYTICS.md](../DATA_AND_ANALYTICS.md) section 6 |
| `D-04` | Confidence tier definitions, sample-size thresholds beyond `min_sample_size`, and recommendation ranking/prioritization criteria. Blocks `intelligence.py`. | [DATA_AND_ANALYTICS.md](../DATA_AND_ANALYTICS.md) section 6 |
| `D-05` | `Decimal` quantization/rounding modes per KPI. | [PYTHON_ENGINEERING_STANDARDS.md](../PYTHON_ENGINEERING_STANDARDS.md) section 7 |
| `D-06` | **Representation of `N/A` (not applicable) versus `None` (unavailable) in typed models.** [DATA_AND_ANALYTICS.md](../DATA_AND_ANALYTICS.md) section 3 requires three distinct states, while [PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md) (`FR-ANA-01`) describes missing metrics as `None` rendered as `N/A`. A typed mechanism that distinguishes "not applicable" from "unavailable" is not defined. | `DATA_AND_ANALYTICS.md` s.3 / `PRODUCT_REQUIREMENTS.md` `FR-ANA-01` |
| `D-07` | **`ConfigurationError` location.** Standards place it in the `OpraError` hierarchy in `src/opra/core/exceptions.py`, but `exceptions.py` is not in this task's intended file list. Config validation cannot raise `ConfigurationError` unless the file is added to scope or the error is provided another way. | [PYTHON_ENGINEERING_STANDARDS.md](../PYTHON_ENGINEERING_STANDARDS.md) section 5 |
| `D-08` | Relationship between `OpraConfig` and `ConfigSnapshot` (for example whether the snapshot is produced by a factory method or constructed directly), and whether `ConfigSnapshot` carries exactly the four settings above or more. | Not specified |
| `D-09` | Whether environment-variable loading (`OPRA_MAX_UPLOAD_BYTES`, `OPRA_MAX_ROWS`, `OPRA_MATURITY_BUFFER_DAYS`, `OPRA_MIN_SAMPLE_SIZE`) is part of this task. Also, `.env.example` contains `OPRA_ENVIRONMENT` and `OPRA_LOG_LEVEL`, which [SECURITY_AND_DATA_GOVERNANCE.md](../SECURITY_AND_DATA_GOVERNANCE.md) section 2 does not list among its approved keys and no document defines. | `.env.example`; `SECURITY_AND_DATA_GOVERNANCE.md` s.2 |
| `D-10` | Location and shape of the final report contract (`generated_at_utc`, `engine_version`, `ConfigSnapshot`, results). The runner is said to assemble it, but no `models/` file is listed for it. | [TECHNICAL_DESIGN.md](../TECHNICAL_DESIGN.md) section 2; `FR-RPT-01` |
| `D-11` | Construction-time strictness not specified by the documents: whether `bool` is rejected for integer settings, whether `float` is rejected where `Decimal` is required, handling of `Decimal` `NaN`/infinity, and whether non-UTC aware datetimes are rejected or converted to UTC. | Not specified |
| `D-12` | **"Step 7" is referenced as the verification gate** ([AGENTS.md](../../AGENTS.md), [PROJECT_FOUNDATION.md](../PROJECT_FOUNDATION.md)) **but is not defined in any repository document**, so its pass criteria cannot be checked from the repository alone. | `AGENTS.md` s.4; `PROJECT_FOUNDATION.md` s.5 |

Items `D-01`–`D-04` mean that, until resolved, only the configuration portion (section 3.1) can be implemented with full fidelity to the documents; even that depends on `D-07` and `D-08`.

## 5. Test Plan

Test file names below are **proposed** and may be adjusted by the owner. All tests must be deterministic, use synthetic data only, and inject fixed timezone-aware timestamps (the existing `reference_utc_timestamp` fixture in `tests/conftest.py`) rather than calling wall-clock time. Shared fixtures must not require unresolved domain definitions.

| Proposed file | Coverage |
| :--- | :--- |
| `tests/unit/test_config.py` | Defaults; boundary values; invalid-input rejection; snapshot stability; immutability. |
| `tests/unit/test_models_records.py` | Construction and invariants; deep immutability; duplicate/quarantine-related contracts once `D-01` is resolved. |
| `tests/unit/test_models_periods.py` | Construction; boundary invariants; timezone awareness. Blocked on `D-02`. |
| `tests/unit/test_models_analytics.py` | `Decimal` precision; `None` / `N/A` / zero distinction. Blocked on `D-03`, `D-06`. |
| `tests/unit/test_models_intelligence.py` | Sample size, confidence, limitations, recommendation linkage and ordering contracts. Blocked on `D-04`. |

### 5.1 Configuration tests

* Defaults equal the approved values (`10 * 1024 * 1024`, `100_000`, `3`, `10`).
* Boundary handling per setting:
  * `max_upload_bytes`: `1` accepted; `0` and negative rejected.
  * `max_rows`: `1` accepted; `0` and negative rejected.
  * `maturity_buffer_days`: `0` accepted; negative rejected.
  * `min_sample_size`: `1` accepted; `0` and negative rejected.
* Invalid values raise `ConfigurationError` and are never clamped or defaulted.
* Wrong-typed values are rejected according to the outcome of `D-11`.
* Snapshot stability: a snapshot compares equal to another built from identical values; it does not change when the source configuration or caller inputs are later changed; two runs with identical configuration yield equal snapshots.
* Immutability: attribute assignment on `OpraConfig` and `ConfigSnapshot` raises `FrozenInstanceError`.

### 5.2 Domain model tests (apply to every model once its fields are defined)

* Valid construction, and rejection of each invariant violation with a clear, non-sensitive message.
* Top-level immutability: attribute assignment raises `FrozenInstanceError`.
* Deep immutability: sequence fields are `tuple`; mapping fields are `MappingProxyType` and writes raise `TypeError`; mutating the caller's original list/dict after construction does not change the model.
* No mutable default arguments (verify instances do not share state).
* Datetime handling: aware UTC accepted; naive handled per `D-11`.
* Numeric handling: `Decimal` precision preserved with no float round-trip; `Decimal("0")` is distinct from `None` and `N/A` (per `D-06`); boundary values and zero denominators where a model represents a ratio.
* Missing-data semantics: absent and not-applicable values are never coerced to `0`.

### 5.3 Architecture and regression

* The existing boundary tests in `tests/app/test_architecture_boundaries.py` continue to pass, with zero `streamlit` imports in the new modules.
* All new packages import cleanly without Streamlit.

## 6. Acceptance Criteria

The task is complete only when **all** of the following hold:

1. Every file in section 2.1 exists and implements only its stated scope; every open decision in section 4 that affects an implemented item has a recorded owner decision.
2. No new dependency is added; `pyproject.toml` and `uv.lock` are unchanged.
3. All models and configuration are frozen and deeply immutable, with explicit type annotations.
4. The tests in section 5 exist for every implemented item and pass.
5. All quality gates pass, with outputs reviewed:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src/opra
   uv run pytest --cov=opra --cov-report=term-missing --cov-fail-under=80
   ```

6. Coverage is at least 80% and reflects meaningful tests of the new code (not inflated by trivial tests). Note that `pyproject.toml` currently omits `src/opra/app/main.py` from coverage; the new modules must be fully measured.
7. Architectural boundaries remain intact (no `streamlit` imports outside `src/opra/app/`).
8. No persistence, external transmission, secrets, or real customer/vehicle data are introduced.
9. Documentation affected by the change is updated, and the task report distinguishes completed, blocked, and pending work.
10. The human owner has reviewed and approved the result. Commits and publication remain exclusively the owner's responsibility.

## 7. Authorization Gate

| Prerequisite | State |
| :--- | :--- |
| Stage 1C complete | Complete |
| Step 7 baseline verification passed | Criteria not defined in repository (`D-12`); owner authorized Stage 2A |
| Open decisions in section 4 resolved or explicitly deferred by the owner | Partially: see section 9 |
| Explicit human authorization to implement | Granted for Stage 2A scope only; remaining model files need decisions `D-01`–`D-06` |

## 8. Implementation Record (Stage 2A)

### 8.1 Implemented

* `src/opra/core/exceptions.py`: `OpraError` and `ConfigurationError(OpraError)`.
* `src/opra/core/config.py`: `OpraConfig` (defaults `10 * 1024 * 1024`, `100_000`, `3`, `10`) and `ConfigSnapshot`, both `@dataclass(frozen=True, slots=True)` and validated in `__post_init__`; `OpraConfig.snapshot()` returns the effective `ConfigSnapshot`. Default constants are defined only in this module.
* `tests/unit/test_config.py`: defaults, boundaries, invalid types, immutability, snapshot equality/hashing/validation.

### 8.2 Decision outcomes

| ID | Outcome | Basis |
| :--- | :--- | :--- |
| `D-07` | **Resolved.** `core/exceptions.py` added to scope with only `OpraError` and `ConfigurationError`. Logging is not implemented. | Standards section 5 mandate the hierarchy and file; `ConfigurationError` is required by `AGENTS.md`. |
| `D-08` | **Resolved provisionally.** `OpraConfig` has defaults; `ConfigSnapshot` has the same four fields without defaults and validates on direct construction; `OpraConfig.snapshot()` is the factory. Owner may veto. | Technical design: the runner "captures `ConfigSnapshot`"; spec section 3.1 lists the four settings. No document defines further fields. |
| `D-11` (settings only) | **Resolved for configuration.** `bool`, `float`, `str`, `None` and other non-`int` values are rejected with `ConfigurationError`; error messages for wrong types name the type, not the value. Not resolved for `Decimal`/datetime model fields (no such models exist yet). | Project rules forbid silent data coercion; standards require fail-fast validation. |
| `D-09` | **Not implemented.** No environment or file loading was added. `.env.example` keys `OPRA_ENVIRONMENT` and `OPRA_LOG_LEVEL` remain undocumented. | Not in approved scope. |
| `D-12` | **Open.** "Step 7" is still undefined in the repository. | |

### 8.3 Still blocked: options for the owner

Each option below is a proposal only; none is implemented.

| ID | Option A | Option B | Notes |
| :--- | :--- | :--- | :--- |
| `D-01` Record schema | Owner supplies the canonical CSV column list, types and allowed enums; model is generated from it. | Implement only a minimal identity model with `job_id` (the one field documents name) and defer all other fields. | Option B still requires deciding which fields are required; documents name only `job_id`. |
| `D-02` Period boundaries | Half-open `[start, end)` UTC interval. | Closed `[start, end]` interval. | Documents require explicit aware-UTC boundaries but not inclusivity or period length. |
| `D-03` KPI results | Owner supplies the KPI catalogue (IDs, formulas, units); result models mirror it. | Generic result shape (`kpi_id`, optional `Decimal` value, sample size) with no catalogue. | Option B fixes a shape the owner has not approved. |
| `D-04` Intelligence | Owner supplies confidence tiers and ranking criteria. | Generic finding shape with sample size, limitations, and linked-evidence tuple; tiers deferred. | Same caveat as `D-03` Option B. |
| `D-05` Rounding | Per-KPI quantization once formulas exist (blocked on `D-03`). | Single project-wide rounding mode. | |
| `D-06` `None` vs `N/A` | A frozen `NotApplicable` sentinel type alongside `None`: `Decimal | NotApplicable | None`. | An explicit tri-state wrapper (value / unavailable / not applicable). | `DATA_AND_ANALYTICS.md` requires three states; `FR-ANA-01` describes two. Needs the owner to reconcile the documents first. |
| `D-10` Report contract | Add `models/report.py` for the final report contract. | Keep the contract in `pipeline/` or `reporting/`. | Out of scope for the five approved files. |

Recommended path: the owner resolves `D-01`–`D-04` and `D-06`; the models are then implemented in a follow-up stage using the test plan in section 5.

## 9. Revision History

| Version | Date | Summary |
| :--- | :--- | :--- |
| `0.1.0-draft` | 2026-11-25 | Initial task specification prepared during Stage 1C. Not authorized for implementation. |
| `0.2.0-draft` | 2026-11-26 | Stage 2A: configuration and exceptions implemented; section 9 added with decision outcomes and options. |
