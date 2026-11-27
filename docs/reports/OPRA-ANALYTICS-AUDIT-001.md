# OPRA.AI — Analytics and Intelligence Requirements Audit

**Task ID:** `OPRA-ANALYTICS-AUDIT-001`  
**Audit date:** 2026-11-27  
**Scope:** Read-only requirements and implementation audit for remaining processing, maturity, analytics, intelligence, recommendation, reporting, and integration work.

## 1. Repository baseline

### Repository and Git

The repository is `C:\Users\USER\Desktop\2608-dev\python_projects\OPRA_AI`. At audit start, `git status --short`, `git diff --stat`, and `git diff --cached --stat` returned no entries. The tree was clean. No application or documentation changes were present before this report was created.

The authoritative ingestion specification is present at `docs/specifications/OPRA-INGEST-001.md`, version `1.2.0`. The Stage 3B completion report is present at `docs/reports/OPRA-STAGE3B-FIX-001.md`. `docs/IMPLEMENTATION_ROADMAP.md` declares itself a derived navigation index, not recovered historical source material; implementation boundaries in it were checked against the master plan and the specifications.

### Independently executed checks

Using the existing Python 3.11 virtual environment and local uv 0.13.10:

| Check | Result |
|---|---|
| `uv --version` | `uv 0.13.10` |
| `uv run --extra dev ruff check .` | Passed: all checks passed. |
| `uv run --extra dev ruff format --check .` | Passed: 53 files already formatted. |
| `uv run --extra dev mypy src/opra` | Passed: 22 source files. |
| `uv run --extra dev pytest --cov=opra --cov-report=term --cov-fail-under=80 -q` | Passed: 338 tests, 94.42% coverage. |
| `git diff --check` | Passed. |

Pytest emitted a cache permission warning for `.pytest_cache`; test and coverage execution completed successfully. No GitHub Actions run was checked or claimed.

## 2. Documentation inventory and authority

Inspected `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_ROADMAP.md`, `docs/IMPLEMENTATION_MASTER_PLAN.md`, Product Requirements, Technical Design, Data and Analytics, Python Engineering Standards, Testing and Quality, Security and Data Governance, Deployment and Operations, `docs/specifications/OPRA-INGEST-001.md`, `docs/tasks/OPRA-MODELS-001.md`, and the Stage 3B report. The specifications directory contains only the approved ingestion specification; the tasks directory contains `OPRA-MODELS-001.md`.

Per `AGENTS.md` §4, unresolved formulas, rounding, thresholds, and schemas must not be invented. `docs/IMPLEMENTATION_MASTER_PLAN.md` says approved governance/specification documents control implementation decisions. The roadmap is a derived sequence/index, not an independent source of business rules.

## 3. Existing implementation inventory

| Area | Current implementation | Classification |
|---|---|---|
| Raw canonical job record | `src/opra/models/records.py`: frozen/slotted `JobRecord`, canonical `JobStatus`, UTC normalization, optional amount/currency pairs, strict finite `Decimal` and code validation. | IMPLEMENTED for the Stage 3B contract; see §4. |
| CSV ingestion/validation/quarantine | `src/opra/ingestion/csv_loader.py`: UTF-8/CSV loading, bounds, field checks, deterministic duplicates, safe diagnostics, v1.2 counters and partial error summaries. | IMPLEMENTED; Stage 3B report and current tests. |
| Reporting period model | `src/opra/models/periods.py`: immutable UTC-normalized half-open `[start_utc, end_utc)` interval and `contains()`. | IMPLEMENTED model only. |
| Generic metric result model | `src/opra/models/analytics.py`: `MetricStatus`, `MetricValue`, `MetricResult(metric_id, metric_value, period)`. No algorithms/catalogue. | IMPLEMENTED generic contract only. |
| Processing | `src/opra/processing/` contains only a scaffold `__init__.py`. | UNRESOLVED / NOT IMPLEMENTED. |
| KPI engine | `src/opra/analytics/` contains only a scaffold `__init__.py`. | UNRESOLVED / NOT IMPLEMENTED. |
| Intelligence | `src/opra/intelligence/` contains only a scaffold `__init__.py`. | UNRESOLVED / NOT IMPLEMENTED. |
| Recommendations | `src/opra/recommendations/` contains only a scaffold `__init__.py`. | UNRESOLVED / NOT IMPLEMENTED. |
| Reporting | `src/opra/reporting/` contains only a scaffold `__init__.py`. | PARTIALLY SPECIFIED / NOT IMPLEMENTED. |
| Pipeline | `src/opra/pipeline/` contains only a scaffold `__init__.py`. | UNRESOLVED / NOT IMPLEMENTED. |
| Tests | Period and generic analytics-model unit tests, ingestion/record tests, architecture-boundary tests; no processing/KPI/intelligence/reporting/pipeline integration tests. | PARTIAL: model and ingestion contracts are tested, downstream behavior has no implementation or tests. |

`tests/unit/test_periods.py` and `test_analytics.py` verify their model invariants. They do not verify cohort assignment, KPI calculations, period comparisons, confidence, recommendations, or report serialization. Architecture tests enforce package importability and no Streamlit imports outside the app, not business analytics behavior.

## 4. Data model assessment

### Approved and implemented contracts

| Contract | Requirement and reference | Status |
|---|---|---|
| Raw job fields | `OPRA-INGEST-001` v1.2.0 §2 and §§4–8: required nonblank `job_id`, canonical status (`completed`, `cancelled`, `in_progress`), required offset-aware `opened_at`, optional offset-aware `completed_at`, optional finite Decimal billed/paid/estimated amount and paired ISO 4217 currency. Sensitive source fields are excluded. | IMPLEMENTED in `JobRecord`; ingestion tests cover key validation paths. |
| Time representation | `OPRA-INGEST-001` §§2, 6; `OPRA-MODELS-001` §§3.3, 8.4: aware datetimes normalize to UTC; no timezone inference. | IMPLEMENTED. |
| Amount representation | `OPRA-INGEST-001` §7; `OPRA-MODELS-001` §§3.3, 8.4: Decimal values preserve precision, no float conversion or model quantization. | IMPLEMENTED for raw financial values. KPI-specific rounding is separate and unresolved. |
| Reporting period value object | `OPRA-MODELS-001` §3.3 and Stage 2E record §8.4: aware UTC bounds; half-open `[start, end)`; start strictly before end. | IMPLEMENTED in `ReportingPeriod`. |
| Generic metric result | `OPRA-MODELS-001` §3.3 and Stage 2E record §8.4: `AVAILABLE`, `UNAVAILABLE`, `NOT_APPLICABLE`, with finite Decimal for available and `None` otherwise. | IMPLEMENTED in `MetricValue`; `MetricResult` links an opaque ID and one period. |
| Record-to-period/metric relationship | `P-02` carried into `OPRA-INGEST-001` authority paragraph and §2: period assignment belongs to processing, not raw records. `MetricResult` has a period but no approved record/cohort/evidence relationship. | PROCESSING BOUNDARY APPROVED; assignment/linkage semantics UNRESOLVED. |

`OPRA-INGEST-001` v1.2.0 §2 supplies the canonical record contract, superseding the earlier `D-01` deferral for raw records. `OPRA-MODELS-001` §4.1 still labels `D-01` deferred and §2.1 says `records.py` awaits the ingestion contract. That older model-task status has not been updated to reflect the later approved ingestion specification.

## 5. Maturity rules assessment

| Topic | Evidence | Classification |
|---|---|---|
| Maturity parameter | `AGENTS.md` §2 and Python Engineering Standards §5 approve `maturity_buffer_days=3`, integer and nonnegative. `DATA_AND_ANALYTICS.md` §4 says the buffer governs maturity for certain completion/turnaround or outcome evaluations relative to a reference date. | APPROVED parameter and broad purpose. |
| Explicit reference time | `DATA_AND_ANALYTICS.md` §4 requires explicit UTC reference timestamps; Python Engineering Standards §4 prohibits local/naive assumptions. | APPROVED constraint. |
| Intake cohort | No document defines exact inclusion timestamp, period assignment rule, or cohort population beyond raw `opened_at` and `P-02`. | UNRESOLVED. |
| Completion cohort | No rule selects `completed_at` versus another event or defines how cancellations count. | UNRESOLVED. |
| Turnaround cohort | No rule defines eligible records, duration population, or handling of missing completion. | UNRESOLVED. |
| Maturity cutoff and immature treatment | No exact comparison formula (including buffer boundary), record exclusion/retention behavior, or metric limitation behavior is specified. `FR-PRC-01` only says to handle immature records per those rules. | UNRESOLVED. |
| Cancelled/in-progress | The raw statuses exist in `OPRA-INGEST-001` §2; no downstream maturity/cohort treatment is approved. | UNRESOLVED. |
| Period boundaries | `OPRA-MODELS-001` §3.3 / Stage 2E §8.4 approve UTC half-open intervals. | APPROVED and implemented at model level. Period duration, pairing, and cohort assignment remain unresolved. |

No maturity or cohort behavior should be implemented until the owner decides the above semantics. The current model's `maturity_buffer_days` setting is not itself a maturity algorithm.

## 6. KPI catalogue assessment

`DATA_AND_ANALYTICS.md` §6 explicitly leaves KPI IDs, formulas, units, and rounding open. `PRODUCT_REQUIREMENTS.md` §4 leaves identifiers and formulas open. `OPRA-MODELS-001.md` §§2.2 and 4.1 (`D-03` partially resolved) allow only generic analytics result types, not KPI catalogue semantics. The mentions of `KPI-01` through `KPI-06` in those sections are examples of unresolved IDs, not approved KPIs.

| Required KPI detail | Audit finding | Classification |
|---|---|---|
| Approved identifier/name | No KPI catalogue found. | UNRESOLVED |
| Formula, numerator, denominator | No formula found. | UNRESOLVED |
| Required source fields/cohort | General inputs must be documented per `DATA_AND_ANALYTICS.md` §5, but no KPI-specific mapping exists. | UNRESOLVED |
| Aggregation/period rules | No KPI-specific aggregation or cohort method exists. | UNRESOLVED |
| Rounding/scale | Generic Decimal precision is approved; per-KPI quantization is explicitly open in `DATA_AND_ANALYTICS.md` §6 and Python Engineering Standards §7. | UNRESOLVED per KPI |
| Zero denominator | `DATA_AND_ANALYTICS.md` §5 requires documentation of this edge case; no behavior is selected. | UNRESOLVED |
| Missing/not-applicable | Three-way distinction is approved in `DATA_AND_ANALYTICS.md` §3 and represented by `MetricStatus`; per-KPI conditions mapping inputs to unavailable vs not applicable remain unspecified. | PARTIALLY APPROVED / UNRESOLVED per KPI |
| Tests | Generic value/result model tests exist; no KPI algorithm tests exist. | NOT IMPLEMENTED |

There are no approved KPIs for which a numerator, denominator, formula, rounding rule, zero-denominator result, or required test can be identified. The audit therefore does not invent a KPI list.

## 7. Period comparison assessment

`OPRA-MODELS-001.md` §3.3 and Stage 2E §8.4 approve the period value object's half-open UTC semantics. `DATA_AND_ANALYTICS.md` §4 calls for deterministic periods and period-over-period comparisons. `OPRA-MODELS-001.md` §3.3 explicitly says D-02 does not define period duration, cohort assignment, comparison pairing, or maturity evaluation.

| Comparison requirement | Status |
|---|---|
| Comparison period selection and pairing | UNRESOLVED |
| Baseline selection/eligibility | UNRESOLVED |
| Percentage-change formula and scale | UNRESOLVED; no calculation is specified |
| Zero baseline behavior | UNRESOLVED |
| Missing baseline behavior | UNRESOLVED |
| N/A vs unavailable vs measured zero representation | Representation APPROVED in generic `MetricValue`; condition-specific comparison semantics UNRESOLVED |
| Comparison implementation/tests | No comparison model or algorithm exists. `MetricResult` contains a single period. | NOT IMPLEMENTED |

No comparison logic can proceed without owner choices about paired periods, comparable cohorts, formulas, and edge-case outputs.

## 8. Intelligence and recommendations assessment

`OPRA-MODELS-001.md` §3.2 records intended generic finding/recommendation properties: sample size, confidence indicators, limitations for `n < min_sample_size` or missing data, links to findings/caveats, deterministic ordering. `AGENTS.md` §2 and `OPRA-MODELS-001.md` §3.1 approve `min_sample_size=10`. But `OPRA-MODELS-001.md` §4.1 marks D-04 deferred; `DATA_AND_ANALYTICS.md` §6 and `PRODUCT_REQUIREMENTS.md` §4 leave confidence tiers, thresholds beyond minimum sample size, and recommendation ranking unresolved.

| Item | Audit finding | Classification |
|---|---|---|
| Finding IDs and definitions | None specified. | UNRESOLVED |
| Trigger thresholds | None specified. | UNRESOLVED |
| Confidence method/tiers | None specified; `min_sample_size=10` is a configuration threshold, not a confidence calculation. | UNRESOLVED |
| Evidence requirements | Generic design requires evidence/sample-size/limitations, but no per-finding evidence schema or provenance rule is defined. | PARTIALLY SPECIFIED |
| Small-sample handling | Requirement to show limitations when `n < min_sample_size`; exact resulting status/text and whether findings are suppressed are not stated. | PARTIALLY SPECIFIED |
| Priority ranking and recommendation mapping | No priority tiers, ranking criteria, mapping, or tie-break rules. | UNRESOLVED |
| Implementation/tests | Intelligence and recommendation packages are scaffolds; no behavior tests exist. | NOT IMPLEMENTED |
| Generative/predictive methods | No approved requirement for them; no implementation is present. | OUT OF APPROVED SCOPE |

## 9. Reporting contract assessment

`PRODUCT_REQUIREMENTS.md` §2 (`FR-RPT-01`) requires reproducible JSON and Markdown reports with `generated_at_utc`, `engine_version`, and `ConfigSnapshot`. `DATA_AND_ANALYTICS.md` §5 repeats these metadata requirements and requires each method/KPI/finding/recommendation to document output and edge cases. `OPRA-MODELS-001.md` §4.1 marks D-10 (final report contract location and shape) deferred. The master plan's deterministic-output rule requires timestamps to be controlled/explicit rather than uncontrolled wall-clock values.

| Reporting item | Status |
|---|---|
| JSON and Markdown output formats | APPROVED high-level; no exporters implemented. |
| Metadata fields | APPROVED: `generated_at_utc`, engine version, config snapshot. |
| KPI/finding/recommendation shape | Depends on unresolved downstream contracts. |
| Decimal serialization form | UNRESOLVED (JSON number vs string/encoding policy). |
| `None`/N/A rendering in JSON and Markdown | Three-way value semantics approved; output encoding/display mapping not fully specified. |
| Deterministic timestamp source | Must be explicit/controlled per master plan; exact reporting API/time input contract not selected. |
| Ordering, whitespace, schema/version, formula-injection handling | General determinism/security intent exists; exact JSON/Markdown serialization and output-context escaping rules are not defined by a reporting specification. |
| Implementation/tests | `src/opra/reporting/` is a scaffold; no exporter tests exist. | NOT IMPLEMENTED |

This audit found no requirements specifying that JSON Decimal values must be numeric versus strings. Neither behavior should be selected without approval because it affects consumers and determinism.

## 10. Requirements classification summary

| Requirement | Classification | Exact reference |
|---|---|---|
| Canonical raw record fields, status enum, timestamp, financial representation | APPROVED and IMPLEMENTED | `OPRA-INGEST-001` v1.2.0 §§2, 4, 6, 7; `records.py`; ingestion tests |
| UTC-normalized half-open ReportingPeriod | APPROVED and IMPLEMENTED at model level | `OPRA-MODELS-001` §3.3, Stage 2E §8.4; `periods.py` |
| Period/cohort assignment is processing, not raw record | APPROVED boundary; processing behavior unresolved | `OPRA-INGEST-001` authority paragraph and §2; `P-02` |
| Metric tri-state and finite Decimal invariant | APPROVED and IMPLEMENTED as generic model | `OPRA-MODELS-001` §3.3 / Stage 2E §8.4; `analytics.py` |
| KPI catalogue and methods | UNRESOLVED | `DATA_AND_ANALYTICS.md` §6; `PRODUCT_REQUIREMENTS.md` §4; `OPRA-MODELS-001` D-03 |
| Maturity buffer purpose/default | APPROVED at broad level | `AGENTS.md` §2; `DATA_AND_ANALYTICS.md` §4; `PRODUCT_REQUIREMENTS.md` FR-PRC-01 |
| Cohort definitions and maturity calculation/record treatment | UNRESOLVED | `DATA_AND_ANALYTICS.md` §4; `PRODUCT_REQUIREMENTS.md` FR-PRC-01; `OPRA-MODELS-001` §3.3 D-02 limitation |
| Comparison pairing/formula/zero baseline | UNRESOLVED | `OPRA-MODELS-001` §3.3; `DATA_AND_ANALYTICS.md` §§4, 6 |
| `min_sample_size=10` | APPROVED configuration only | `AGENTS.md` §2; `OPRA-MODELS-001` §3.1 |
| Confidence methodology, finding triggers, recommendation priorities | UNRESOLVED | `OPRA-MODELS-001` D-04; `DATA_AND_ANALYTICS.md` §6; `PRODUCT_REQUIREMENTS.md` §4 |
| Report formats and metadata | APPROVED high-level, not implemented | `PRODUCT_REQUIREMENTS.md` FR-RPT-01; `DATA_AND_ANALYTICS.md` §5 |
| Final report model and serialization details | UNRESOLVED | `OPRA-MODELS-001` D-10; no reporting specification |
| Determinism, Decimal, missing values, immutable contracts | APPROVED general constraints | `AGENTS.md` §2; Python Engineering Standards §§3–4; Data and Analytics §3 |
| Security/privacy and app boundary | APPROVED general constraints | Security and Data Governance §§3–5; Technical Design §1; architecture tests |

## 11. Conflicting or stale requirements

1. **Canonical record decision status:** `OPRA-INGEST-001` v1.2.0 §2 establishes the canonical record contract and its revision history says v1.0.0 incorporates approved owner decisions. The older `OPRA-MODELS-001.md` §2.1 and §4.1 still say D-01 is deferred and `records.py` is blocked pending an ingestion contract. The ingestion contract now exists and is approved. This is a stale-status conflict; the later, specifically scoped ingestion specification and Stage 3B implementation report establish the current raw-record authority, but the model task's historical status was not reconciled.
2. **Reporting-period status inventory:** `OPRA-MODELS-001.md` §3.3 / Stage 2E §8.4 explicitly resolve D-02 to half-open UTC boundaries, while `DATA_AND_ANALYTICS.md` §6 still lists period boundary rules as unresolved. The boundary itself is settled; period duration, comparison pairing, cohorts, and maturity remain unresolved. The latter document's unresolved list is overbroad/stale on boundary inclusivity.
3. **Report timestamp determinism:** `PRODUCT_REQUIREMENTS.md` FR-RPT-01 and `DATA_AND_ANALYTICS.md` §5 require `generated_at_utc`; the master plan forbids uncontrolled current-time timestamps in deterministic outputs and permits controlled/explicit timestamps. These can coexist if generation time is an explicit input, but no report API contract defines that input. This is a specification gap, not a settled contradiction.
4. **Missing value display wording:** `DATA_AND_ANALYTICS.md` §3 distinguishes `None` (unavailable) and N/A (not applicable), while `PRODUCT_REQUIREMENTS.md` FR-ANA-01 says missing metrics yield `None` (`N/A` in display). `OPRA-MODELS-001` §3.3 / Stage 2E §8.4 resolves the typed distinction with `MetricStatus`; the exact mapping for rendering and per-KPI applicability is not specified. This is a display-contract gap and potentially conflicting wording, not authority to collapse the typed states.

## 12. Concise owner-review proposals (not approved requirements)

These proposals are decision prompts only. They are not implementation instructions and must be approved or revised before the affected stages.

1. **Maturity/cohorts:** Approve separately defined intake, completion, and turnaround cohorts; specify the event timestamp and eligibility per cohort, the exact use of the UTC reference time and `maturity_buffer_days`, boundary inclusivity, and treatments for cancelled, in-progress, missing-completion, and immature jobs.
2. **KPI catalogue:** For each owner-selected KPI, approve an ID/name, operational purpose, cohort, numerator, denominator, required fields, aggregation, unit, precision/rounding, zero-denominator result, missing-data result (`UNAVAILABLE` vs `NOT_APPLICABLE`), and test examples. The current illustrative KPI IDs should remain examples unless selected.
3. **Period comparison:** Approve period pairing/selection, comparable-cohort rules, absolute and percentage change definitions, rounding, and zero/missing baseline outcomes.
4. **Intelligence:** Approve finding IDs/triggers, thresholds, evidence/provenance, confidence method, sample-size behavior (including `n < 10`), priority ordering/ties, recommendation mapping, and data-caveat propagation.
5. **Reporting:** Approve a final immutable report schema/location, deterministic timestamp input, JSON Decimal encoding, N/A/None representation, stable ordering/serialization, schema versioning, and Markdown/output escaping requirements.
6. **Document reconciliation:** Update older open-decision/status inventories only through controlled documentation maintenance after confirming the owner-approved decisions; do not silently rewrite decision history.

## 13. Recommended implementation order and dependencies

| Proposed stage | Scope | Must be approved first | Proposed acceptance criteria |
|---|---|---|---|
| 4A-1: Processing and maturity contract | Normalize canonical job data, assign cohorts/periods, maturity eligibility. Keep `JobRecord` free of period/KPI fields (`P-02`). | Cohort definitions, maturity cutoff/treatments, reference-time input. | Immutable deterministic processing outputs; UTC boundaries tested; all status/missing/immature cases covered; raw input objects unchanged; no invented fields. |
| 4A-2: KPI catalogue and calculations | Implement only owner-approved KPI methods using `Decimal`. | Complete per-KPI catalogue including formulas, rounding, zero and missing semantics. | One traceable test set per KPI, including normal/zero/missing/immature/conflicting cases; exact Decimal expectations; deterministic results. |
| 4A-3: Period comparison | Pair eligible periods and compute approved comparisons. | Pairing, baseline and change formula, zero/missing baseline rules. | Boundary/cohort pairing tests; deterministic Decimal results; explicit unavailable/not-applicable/zero outcomes. |
| 5A: Findings/intelligence | Produce deterministic evidence-backed findings. | Finding catalog, trigger/confidence rules, sample-size policy. | Trigger/no-trigger, small-sample, missing-evidence, ordering and caveat tests. |
| 5B: Recommendations | Map findings/caveats to prioritized recommendations. | Recommendation catalogue, mappings, priority/tie-break rules. | Every emitted recommendation traceable to finding; deterministic order and limitations; edge-case tests. |
| 6A: Reporting | JSON/Markdown exports and final report contract. | Report schema, timestamp API, serialization and rendering rules. | Stable repeat output given explicit timestamp/config; Decimal and missing-state serialization tests; privacy and escaping checks. |
| Integration: Pipeline | Wire processing through reporting and app boundary. | Stable contracts from preceding stages. | Headless end-to-end tests for valid, partial, rejected, missing-data and deterministic replay cases; app remains presentation-only. |

These stages are dependency-ordered proposals aligned to the derived roadmap and module order in `AGENTS.md` §2. Actual roadmap stage identifiers should be confirmed in task specifications before work starts; the roadmap does not define business semantics.

## 14. Overall readiness recommendation

**Readiness: BLOCKED for analytics, maturity, intelligence, recommendation, and reporting implementation; READY for owner decision-making and specification updates.** The current model and ingestion layers are verified, but no approved KPI catalogue, maturity algorithm, comparison method, confidence method, recommendation ranking, or detailed report serialization contract exists. The live baseline gates pass, which establishes engineering-tool readiness only; it does not satisfy these missing business contracts.

Do not begin Stage 4A calculations or later dependent functionality until the owner approves the open requirements and the authoritative specifications are updated. This audit did not change source code, tests, specifications, dependencies, lockfiles, or existing working-tree changes.
