# OPRA-MODELS-001 — Core Configuration and Immutable Domain Models

**Task ID:** `OPRA-MODELS-001`  
**Version:** `0.4.0-draft`  
**Status:** Partially Implemented (Stages 2A and 2E) — Configuration, `ModelValidationError`, `periods.py` and generic `analytics.py` implemented; `records.py` and `intelligence.py` deferred and blocked.  
**Last Updated:** 2026-11-26  
**Related Documents:** [PROJECT_FOUNDATION.md](../PROJECT_FOUNDATION.md) | [PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md) | [TECHNICAL_DESIGN.md](../TECHNICAL_DESIGN.md) | [DATA_AND_ANALYTICS.md](../DATA_AND_ANALYTICS.md) | [PYTHON_ENGINEERING_STANDARDS.md](../PYTHON_ENGINEERING_STANDARDS.md) | [TESTING_AND_QUALITY.md](../TESTING_AND_QUALITY.md) | [SECURITY_AND_DATA_GOVERNANCE.md](../SECURITY_AND_DATA_GOVERNANCE.md) | [AGENTS.md](../../AGENTS.md)

> **Stage 2A note.** The owner authorized Stage 2A implementation of this task. Only the parts supported by approved documentation were implemented (section 8). Items that are still open or deferred block the remaining files and must not be invented.

> **Owner decision record, 2026-11-26.** The owner approved the decision register in section 4.1. It supersedes the earlier statuses in sections 4, 7, 8.2 and 8.3 wherever they differ; those sections are retained as decision history. The register makes `periods.py` and generic `analytics.py` result contracts eligible for implementation. Eligibility is not authorization: implementation requires a separate explicit owner instruction.

## 1. Objective

Establish the shared, deeply immutable contracts that every later pipeline stage depends on: centralized configuration with fail-fast validation, a stable per-run configuration snapshot, and typed domain models for records, reporting periods, analytics results, and intelligence results.

No pipeline behavior is implemented by this task.

## 2. Scope

### 2.1 Intended implementation files

| File | Contents |
| :--- | :--- |
| `src/opra/core/config.py` | `OpraConfig` and `ConfigSnapshot`, with configuration validation. **Implemented.** |
| `src/opra/core/exceptions.py` | `OpraError` and `ConfigurationError` (added to scope; see `D-07`). **Implemented.** |
| `src/opra/models/records.py` | Record domain models. **Deferred; blocked** until the ingestion source contract is defined (`D-01`). |
| `src/opra/models/periods.py` | Reporting-period domain models. **Eligible for implementation** (`D-02`, `D-11`). |
| `src/opra/models/analytics.py` | Generic analytics result contracts only, with no KPI catalogue or formulas. **Eligible for implementation** (`D-03` partial, `D-05`, `D-06`, `D-11`). |
| `src/opra/models/intelligence.py` | Intelligence result models (findings and, per [TECHNICAL_DESIGN.md](../TECHNICAL_DESIGN.md) section 2, recommendations). **Deferred; blocked** until the intelligence methodology is approved (`D-04`). |

### 2.2 Explicitly out of scope

* Ingestion, validation, processing, analytics algorithms, intelligence rules, recommendation logic, reporting/exporters, and pipeline orchestration.
* Any persistence, database, disk retention, or external data transmission.
* Any new dependency (including Pydantic) and any edit to `pyproject.toml` or `uv.lock`.
* KPI identifiers from a catalogue, KPI formulas, denominators, units, and KPI-specific rounding (downstream of the KPI catalogue; `D-03`, `D-05`).
* Environment or `.env` loading (`D-09`) and the final report contract (`D-10`).
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

### 3.3 Owner-approved model conventions (decisions of 2026-11-26)

These conventions record decisions `D-02`, `D-05`, `D-06` and `D-11` (section 4.1). They apply to the files eligible for implementation.

* **Reporting periods (`D-02`).** A period is defined by `start_utc` and `end_utc`. It contains a timestamp `t` if and only if `start_utc <= t < end_utc` (half-open). `start_utc` must be strictly before `end_utc`; equal or reversed bounds are rejected. This convention does not define period duration, cohort assignment, comparison pairing, or maturity evaluation.
* **Metric values (`D-06`).** A metric value is a `MetricStatus` with members `AVAILABLE`, `UNAVAILABLE` and `NOT_APPLICABLE`, plus `value: Decimal | None`. Construction invariants, as formulated from the decision (see 4.2):
  * `AVAILABLE` requires `value` to be a finite `Decimal`. `Decimal("0")` is a valid measured value.
  * `UNAVAILABLE` and `NOT_APPLICABLE` require `value is None`.
  * Zero is never substituted for an unavailable or not-applicable value, and no magic strings represent a state.
* **Decimal handling (`D-05`, `D-11`).** `Decimal` precision is preserved exactly. Model constructors perform no quantization or rounding and no float conversion. `float` values and non-finite `Decimal` values (`NaN`, `Infinity`) are rejected where a `Decimal` is required. KPI-specific rounding is defined in the analytics specification.
* **Integers (`D-11`).** `bool` is rejected where an integer is required.
* **Datetimes (`D-11`).** Naive datetimes are rejected. Timezone-aware datetimes are normalized to UTC; no local timezone is ever assumed.

## 4. Unresolved Decisions (Must Be Resolved Before or During Authorization)

The approved documents mark these items as open. Per [AGENTS.md](../../AGENTS.md) section 4, they must **not** be invented during implementation. The human owner must decide each one, or explicitly approve a recorded default, before the affected model is implemented.

> **Status note (2026-11-26).** The table below is preserved as the decisions were originally raised. Current statuses are in section 4.1, which supersedes it.

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

*Historical note (Stage 2A):* Items `D-01`–`D-04` mean that, until resolved, only the configuration portion (section 3.1) can be implemented with full fidelity to the documents; even that depends on `D-07` and `D-08`.

### 4.1 Decision register (owner-approved 2026-11-26)

| ID | Status | Owner decision | Effect on implementation |
| :--- | :--- | :--- | :--- |
| `D-01` | **Deferred** | Defer the canonical records schema until the ingestion source contract is defined. | `records.py` remains blocked. |
| `D-02` | **Resolved** | Approve half-open UTC reporting periods: `start_utc <= t < end_utc`, with `start < end`. | `periods.py` is eligible for implementation. |
| `D-03` | **Partially resolved** | Permit generic analytics result types. The KPI catalogue and formulas remain downstream. | Generic `analytics.py` result contracts are eligible, with no invented KPI identifiers, formulas, denominators or units. |
| `D-04` | **Deferred** | Defer confidence tiers and recommendation prioritization; intelligence implementation waits for the methodology. | `intelligence.py` remains blocked. |
| `D-05` | **Resolved** | Preserve `Decimal` precision. No model-level rounding or float conversion. | Applies to all models with `Decimal` fields. |
| `D-06` | **Resolved** | Use `MetricStatus` (`AVAILABLE`, `UNAVAILABLE`, `NOT_APPLICABLE`) plus `value: Decimal | None`, with strict construction invariants. | Defines the value representation in `analytics.py`. See 3.3 and 4.2. |
| `D-07` | **Resolved** | The exception hierarchy (`OpraError`, `ConfigurationError`) is already implemented. | Implemented in `src/opra/core/exceptions.py`. |
| `D-08` | **Resolved** | Approve the four-field `ConfigSnapshot` generated by `OpraConfig.snapshot()`. | Implemented in `src/opra/core/config.py`. Replaces the provisional status in 8.2. |
| `D-09` | **Deferred** | Environment loading remains outside this task. | No environment or `.env` loading in this task. |
| `D-10` | **Deferred** | The final report contract belongs to the reporting/pipeline specification. | No report contract in this task. |
| `D-11` | **Resolved** | Reject `bool` as `int`, `float` for `Decimal` values, non-finite `Decimal` values, and naive datetimes. Normalize timezone-aware datetimes to UTC without assuming a local timezone. | Applies to all eligible models. See 3.3 and 4.2. |
| `D-12` | **Resolved** (Option A) | Step 7 passes when the baseline quality gates (section 6, item 5) pass locally in the clean, locked environment. GitHub Actions CI execution is not required for Step 7 and remains deferred and separate. | Defines the Step 7 gate. The existing Stage 2A owner authorization is preserved. |

### 4.2 Points the approved decisions do not settle

These must not be decided by the implementer. The owner is asked to confirm or amend them before the eligible files are implemented.

* **`D-06` invariant wording.** The decision specifies "strict construction invariants" without listing them. The invariants in 3.3 are a formulation of that decision and need owner confirmation. The decision defines no reason codes for the unavailable or not-applicable states.
* **`D-03` field list.** The decision permits generic result types but does not enumerate their fields. The implementation plan must propose the field list for owner confirmation. Any identifier field must be an opaque, non-empty string with no catalogue semantics.
* **`D-11` and `int` for `Decimal` fields.** The decision rejects `float` for `Decimal` values but is silent on `int`. Until the owner decides, the implementation plan must treat this as an open question rather than choose.
* **`D-11` and non-UTC aware datetimes.** The decision normalizes them to UTC. This supersedes the "UTC-only acceptance" alternative raised earlier.
* **`D-02` residuals.** Period duration, comparison pairing, which record field assigns a record to a period, and maturity evaluation remain undecided and are not part of `periods.py`.

## 5. Test Plan

Test file names below are **proposed** and may be adjusted by the owner. All tests must be deterministic, use synthetic data only, and inject fixed timezone-aware timestamps (the existing `reference_utc_timestamp` fixture in `tests/conftest.py`) rather than calling wall-clock time. Shared fixtures must not require unresolved domain definitions.

| Proposed file | Coverage |
| :--- | :--- |
| `tests/unit/test_config.py` | Defaults; boundary values; invalid-input rejection; snapshot stability; immutability. |
| `tests/unit/test_models_records.py` | **Deferred** until `D-01` is resolved. Construction and invariants; deep immutability; duplicate/quarantine-related contracts. |
| `tests/unit/test_models_periods.py` | Eligible. Construction; half-open boundary semantics; `start < end`; datetime strictness and UTC normalization (see 5.4). |
| `tests/unit/test_models_analytics.py` | Eligible. `Decimal` precision; `MetricStatus` invariants; zero distinct from unavailable and not applicable (see 5.4). |
| `tests/unit/test_models_intelligence.py` | Sample size, confidence, limitations, recommendation linkage and ordering contracts. **Deferred** until `D-04` is resolved. |

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

### 5.4 Tests required by the approved decisions

Applies to the eligible files only. Each test must assert a documented or approved rule and fail if that rule were removed.

* **Periods (`D-02`, `D-11`).**
  * A timestamp equal to `start_utc` is contained; a timestamp equal to `end_utc` is not.
  * `start_utc == end_utc` and `start_utc > end_utc` are rejected.
  * Naive `start_utc`, `end_utc` and naive membership timestamps are rejected.
  * A timezone-aware non-UTC datetime is normalized to the equivalent UTC instant; the stored value is UTC. The ordering check uses normalized values.
  * No local timezone is assumed.
* **Metric values (`D-05`, `D-06`, `D-11`).**
  * Every status and value combination is covered: `AVAILABLE` with a finite `Decimal` is accepted, including `Decimal("0")`; `AVAILABLE` with `None` is rejected; `UNAVAILABLE` and `NOT_APPLICABLE` with a non-`None` value are rejected.
  * `Decimal("0")` is distinct from both `None` states.
  * `float`, `NaN` and `Infinity` values are rejected.
  * Precision is preserved exactly, for example `Decimal("1.2300")` retains its exponent. Nothing is quantized.
* **Integers (`D-11`).** Any integer field rejects `bool`.
* **Open points.** No test may encode behavior for the items in 4.2 until the owner decides them.

## 6. Acceptance Criteria

The task as a whole is complete only when **all** of the following hold. Criteria apply per implementation stage to the files eligible at that stage; sections 6.1 to 6.3 define the incremental completion points.

1. Every file in section 2.1 that is eligible for the current stage exists and implements only its stated scope. Deferred files are explicitly excluded until their decisions are resolved. Every decision in section 4.1 that affects an implemented item has a recorded owner decision.
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

### 6.1 Configuration portion: complete when

* `exceptions.py`, `config.py` and `tests/unit/test_config.py` exist, and the four gates pass (`D-07`, `D-08`, `D-11` for settings).
* The owner has reviewed the result.

### 6.2 Currently eligible domain-model portion: complete when

* `periods.py` and generic `analytics.py` result contracts exist, implementing sections 3.2 and 3.3 and nothing beyond them.
* The points in 4.2 have been confirmed or amended by the owner.
* The tests in 5.2 and 5.4 exist for each implemented item and pass.
* Coverage is measured per new module as well as for the package; the package threshold remains 80%. A test is meaningful only if it asserts a documented or approved rule and would fail if that rule were removed. Tests that only construct objects, or that exist to raise the percentage, do not count. No coverage exclusions are added.
* The architecture-boundary test passes with no `streamlit` import in the new modules, and the new modules import nothing from `src/opra/app/`.
* The decision register in 4.1 is updated with any further owner decisions, and the owner has reviewed each file.

### 6.3 Deferred portion: complete when

* `records.py` is implemented after `D-01` is resolved and the ingestion source contract is defined, and `intelligence.py` after `D-04` is resolved and the methodology is approved.
* Each file then satisfies the criteria above, and the owner has reviewed it separately.
* `OPRA-MODELS-001` is not complete as a whole until the deferred files are implemented or the owner formally descopes them.

## 7. Authorization Gate

| Prerequisite | State |
| :--- | :--- |
| Stage 1C complete | Complete |
| Step 7 baseline verification passed | Criteria defined by `D-12` (Option A): the baseline quality gates pass locally in the clean, locked environment; GitHub Actions CI is not required. Local gate results were reported in Stage 1C and Stage 2A; owner to verify. |
| Open decisions in section 4 resolved or explicitly deferred by the owner | Done for the decision register in 4.1; residual points in 4.2 await owner confirmation |
| Explicit human authorization to implement | Granted for Stage 2A scope (configuration) only. `periods.py` and generic `analytics.py` are eligible but not yet authorized to start; `records.py` and `intelligence.py` are deferred and blocked |

## 8. Implementation Record (Stage 2A)

### 8.1 Implemented

* `src/opra/core/exceptions.py`: `OpraError` and `ConfigurationError(OpraError)`.
* `src/opra/core/config.py`: `OpraConfig` (defaults `10 * 1024 * 1024`, `100_000`, `3`, `10`) and `ConfigSnapshot`, both `@dataclass(frozen=True, slots=True)` and validated in `__post_init__`; `OpraConfig.snapshot()` returns the effective `ConfigSnapshot`. Default constants are defined only in this module.
* `tests/unit/test_config.py`: defaults, boundaries, invalid types, immutability, snapshot equality/hashing/validation.

### 8.2 Decision outcomes

*Recorded at Stage 2A and preserved as history. Section 4.1 supersedes it where it differs; notably `D-08` is now approved and `D-12` is resolved.*

| ID | Outcome | Basis |
| :--- | :--- | :--- |
| `D-07` | **Resolved.** `core/exceptions.py` added to scope with only `OpraError` and `ConfigurationError`. Logging is not implemented. | Standards section 5 mandate the hierarchy and file; `ConfigurationError` is required by `AGENTS.md`. |
| `D-08` | **Resolved provisionally.** `OpraConfig` has defaults; `ConfigSnapshot` has the same four fields without defaults and validates on direct construction; `OpraConfig.snapshot()` is the factory. Owner may veto. | Technical design: the runner "captures `ConfigSnapshot`"; spec section 3.1 lists the four settings. No document defines further fields. |
| `D-11` (settings only) | **Resolved for configuration.** `bool`, `float`, `str`, `None` and other non-`int` values are rejected with `ConfigurationError`; error messages for wrong types name the type, not the value. Not resolved for `Decimal`/datetime model fields (no such models exist yet). | Project rules forbid silent data coercion; standards require fail-fast validation. |
| `D-09` | **Not implemented.** No environment or file loading was added. `.env.example` keys `OPRA_ENVIRONMENT` and `OPRA_LOG_LEVEL` remain undocumented. | Not in approved scope. |
| `D-12` | **Open.** "Step 7" is still undefined in the repository. | |

### 8.3 Still blocked: options for the owner

Each option below is a proposal only; none is implemented. *Preserved as history: section 4.1 records the owner's choices, including half-open periods for `D-02` and the `MetricStatus` representation for `D-06`, which differs from both options listed here.*

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

### 8.4 Stage 2E completion record (2026-11-26)

*Appended record. Where it differs, it supersedes the "eligible" and "not yet authorized" statuses of `periods.py` and `analytics.py` in sections 2.1 and 7. Earlier sections are kept as history.*

* **Implemented, per owner rulings A to I of Stage 2D:**
  * `src/opra/core/exceptions.py`: `ModelValidationError(OpraError)`; `ConfigurationError` unchanged (ruling A).
  * `src/opra/models/periods.py`: frozen, slotted `ReportingPeriod(start_utc, end_utc)`. One datetime helper serves construction and `contains()` (ruling B). It rejects non-`datetime` and naive values (including a `tzinfo` with no offset), maps `ValueError` and `OverflowError` to `ModelValidationError`, normalizes to UTC first, then requires `start_utc < end_utc`. Membership is `[start_utc, end_utc)`.
  * `src/opra/models/analytics.py`: `MetricStatus` (plain `Enum`, values `"available"`, `"unavailable"`, `"not_applicable"`), `MetricValue(status, value=None)` and `MetricResult(metric_id, metric_value, period)` (rulings C, E, F, G). `comparison` and `sample_size` are not included (ruling D).
  * Tests: `tests/unit/test_exceptions.py`, `tests/unit/test_periods.py`, `tests/unit/test_analytics.py`. These file names replace the proposed `test_models_periods.py` and `test_models_analytics.py` in section 5.
* **Decimal rules as implemented (`D-05`, `D-11`):** only `Decimal` instances; `bool`, `int`, `float`, `str`, `NaN` and `Infinity` are rejected; the supplied object is stored unchanged (tests assert `is` and `as_tuple()`). This closes the `int` point left open in 4.2, and supersedes the narrower wording in 3.3.
* **Behavior pinned by tests:** period normalization discards the input offset; `MetricValue` equality is numeric (`Decimal("1.0") == Decimal("1.00")`), so representation is not part of equality.
* **Not changed:** `records.py` (`D-01`) and `intelligence.py` (`D-04`) remain deferred and blocked; `models/__init__.py` is unmodified (ruling H).
* **Verification (Python 3.11.18, locked environment, local only):** `ruff check .` pass; `ruff format --check .` pass (42 files); `mypy src/opra` pass (20 files); `pytest --cov=opra --cov-fail-under=80` pass: 294 passed, 100% line and branch coverage (108 statements, 32 branches). No GitHub Actions run was triggered or observed (`D-12`).
* **Not updated in this entry:** the README status table and the wording of 3.3 and 4.2.

## 9. Revision History

| Version | Date | Summary |
| :--- | :--- | :--- |
| `0.1.0-draft` | 2026-11-25 | Initial task specification prepared during Stage 1C. Not authorized for implementation. |
| `0.2.0-draft` | 2026-11-26 | Stage 2A: configuration and exceptions implemented; section 8 added with decision outcomes and options. |
| `0.3.0-draft` | 2026-11-26 | Owner decision register recorded (section 4.1). Added 3.3 approved model conventions, 4.2 residual points, 5.4 decision-driven tests, and 6.1 to 6.3 incremental acceptance criteria. Eligible and deferred model files marked in 2.1. Gate table updated. Corrected the section reference in the Stage 2A note and in the `0.2.0-draft` revision row. |
| `0.4.0-draft` | 2026-11-26 | Stage 2E: `ModelValidationError`, `periods.py` and generic `analytics.py` implemented and verified. Completion record added as 8.4; status line updated. `records.py` and `intelligence.py` remain deferred. |
