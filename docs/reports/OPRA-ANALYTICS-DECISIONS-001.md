# OPRA.AI — Analytics and Intelligence Owner Decisions

**Task ID:** `OPRA-ANALYTICS-DECISIONS-001`  
**Prepared:** 2026-11-27  
**Status:** Superseded in part by `OPRA-ANALYTICS-V1-APPROVAL-001` (2026-11-27); historical proposal retained  
**Scope:** Reconcile existing decisions and present outstanding processing, KPI, comparison, intelligence, and reporting choices.

> **Approval rule:** “APPROVED” below refers only to a decision supported by the cited project record. “RECOMMENDED” is a proposed option for owner review. A recommendation does not authorize implementation or amend an authoritative specification.

> **Resolution notice (2026-11-27):** The owner subsequently directed implementation of the recommended fixes with full authorization. The exact approved scope is recorded in `docs/reports/OPRA-ANALYTICS-V1-APPROVAL-001.md` and authoritative specifications `OPRA-ANALYTICS-001.md`, `OPRA-INTELLIGENCE-001.md`, and `OPRA-REPORT-001.md` v1.1.0. Unmentioned items remain open. This notice preserves the original proposal and does not reinterpret its earlier status.

## 1. Reconciled existing decisions

| Topic | Existing decision and evidence | Current state |
|---|---|---|
| Raw service record | `OPRA-INGEST-001` v1.2.0 §§2, 4–8 defines `job_id`, canonical status, `opened_at`, optional `completed_at`, and optional finite `Decimal` amounts with currency pairs. The Stage 3B completion report records implementation and verification. | **APPROVED; IMPLEMENTED** (`src/opra/models/records.py`, ingestion module and tests). |
| Raw-record boundary | `OPRA-INGEST-001` authority text and §2; P-02: reporting-period assignment, maturity evaluation, and KPI calculations belong downstream, not in raw records. | **APPROVED; IMPLEMENTED boundary.** |
| Timestamp contract | `OPRA-INGEST-001` §§2, 6 and `OPRA-MODELS-001` §§3.3, 8.4: timestamps are aware, source timezone is declared upstream, and values normalize to UTC; no inference. | **APPROVED; IMPLEMENTED.** |
| Financial values | `OPRA-INGEST-001` §7 and `OPRA-MODELS-001` §§3.3, 8.4: finite `Decimal`, no float conversion or implicit numeric coercion; no model quantization. | **APPROVED; IMPLEMENTED** for canonical values. KPI-specific rounding remains open. |
| Reporting period bounds | `OPRA-MODELS-001` §3.3 and Stage 2E completion record §8.4: UTC half-open `[start, end)` intervals with start before end. | **APPROVED; IMPLEMENTED** in `src/opra/models/periods.py`. Period durations, cohort assignment, and comparison pairing are not thereby decided. |
| Metric value states | `OPRA-MODELS-001` §3.3 and Stage 2E §8.4: `AVAILABLE`, `UNAVAILABLE`, and `NOT_APPLICABLE`; an available value is finite `Decimal`, otherwise value is absent. | **APPROVED; IMPLEMENTED** as generic model. Per-KPI conditions and report rendering remain open. |
| Maturity buffer configuration | Root `AGENTS.md` §2 and `OPRA-MODELS-001` §3.1: `maturity_buffer_days` defaults to `3` and must be nonnegative. `DATA_AND_ANALYTICS.md` §4 describes its general purpose in assessing maturity relative to an explicit UTC reference time. | **APPROVED** parameter, default, and broad purpose. Actual application to a cohort or KPI is not defined. |
| Minimum sample size | Root `AGENTS.md` §2 and `OPRA-MODELS-001` §3.1: `min_sample_size` defaults to `10` and must be positive. | **APPROVED** configuration only. Below-threshold behavior, confidence, and finding suppression are not specified. |
| Mature cohorts outside raw record | `OPRA-INGEST-001` v1.2.0 decision register `ING-11`: downstream matured cohorts may be supported without placing `ReportingPeriod`, maturity logic, or KPI formulas in raw records. | **APPROVED** architectural boundary only. It does not define a cohort or KPI. |
| KPI-06 / matured intake cohort | `OPRA-MODELS-001` §4.1 `D-03` describes KPI identifiers (including KPI-01–KPI-06) as examples whose catalogue is unresolved. `DATA_AND_ANALYTICS.md` §6 likewise leaves identifiers/formulas open. No separate approval record for “KPI-06 — Matured Intake Cohort” was found. | **NOT APPROVED / UNRESOLVED.** Do not treat the name or a formula as settled. |
| Generic downstream contracts | `OPRA-MODELS-001` §3.3 and Stage 2E §8.4 approve generic period and metric value models; D-03 only permits a generic analytics result model, D-04 defers intelligence, and D-10 defers the final report contract. | Generic models **APPROVED; IMPLEMENTED**. Business behavior remains unresolved. |

### KPI-06 and the maturity buffer: explicit finding

The repository evidence confirms three separate points: (1) the configurable buffer and default of three days are approved; (2) `ING-11` approves supporting matured cohorts downstream of raw records; and (3) no record approves KPI-06 as a matured intake cohort, its population, maturity cutoff, or formula. The earlier audit’s broad “maturity unresolved” statement should be read with this boundary: **configuration and architectural placement are approved; cohort/KPI behavior is not**. This report does not amend that audit or any approved specification.

### Stale or overbroad documentation to keep in view

| Documentation issue | Evidence and treatment |
|---|---|
| Raw-record deferral remains in older model task | `OPRA-MODELS-001` §§2.1 and 4.1 `D-01` still say `records.py` awaits a source contract. Later `OPRA-INGEST-001` v1.2.0 §§2 and its revision/decision records provide that approved contract, and Stage 3B is reported complete. Treat the older status as stale history; do not rewrite it as part of this task. |
| Period boundary listed as open | `DATA_AND_ANALYTICS.md` §6 broadly lists period boundaries as unresolved, whereas `OPRA-MODELS-001` §3.3 / Stage 2E §8.4 approve half-open UTC bounds. The bounds are settled; period duration and analytical assignment remain open. |
| Missing-value wording differs by context | `PRODUCT_REQUIREMENTS.md` FR-ANA-01 mentions `None` and display N/A, while `DATA_AND_ANALYTICS.md` §3 and the approved metric model preserve unavailable, not-applicable, and zero as distinct. Keep the typed distinction; decide only the presentation mapping and per-metric conditions. |

## 2. Previously approved but undocumented requirements

No additional decision was found in the inspected reports, task records, or approved specifications that approves a named KPI, formula, maturity cutoff, comparison method, intelligence threshold, or final report schema beyond the approvals listed in §1. The following approvals are broader than some audit wording and should be carried forward without expanding them:

| Approved item | Exact scope | What it does not approve |
|---|---|---|
| `ING-11` in `OPRA-INGEST-001` v1.2.0 decision register | Matured cohorts may be supported in downstream processing; raw records do not calculate maturity, periods, or KPIs. | Intake cohort definition, KPI-06 identity/formula, maturity arithmetic, record eligibility, or treatment of immature records. |
| `maturity_buffer_days=3` in root `AGENTS.md` §2 and `OPRA-MODELS-001` §3.1 | Validated configurable setting with default and nonnegative bound. | Whether it applies to intake, completion, turnaround, particular KPIs, or how its boundary is calculated. |
| `min_sample_size=10` in the same references | Validated configurable minimum. | Statistical confidence, findings below the minimum, or which observations count as the sample. |
| Half-open period interval in `OPRA-MODELS-001` §3.3 / Stage 2E §8.4 | Start included, end excluded for a `ReportingPeriod`. | Which event timestamp assigns a job to a cohort or which period is selected as comparison baseline. |

## 3. Processing and maturity decisions

**Operational problem:** downstream analytics need a repeatable rule for assigning records to populations and deciding whether observations are mature enough to evaluate. Current `JobRecord` supplies status and event timestamps, but does not and must not own period or maturity logic (P-02).

| Decision for owner | RECOMMENDED option | Alternatives and consequences | Affected modules/tests | Approved-contract effect |
|---|---|---|---|---|
| Intake cohort event | Use `opened_at` to assign an intake event to the half-open reporting period; define separately whether the metric counts opened jobs or a later outcome. | Assign by completion time (changes the question from intake volume to resolved volume); define a separate KPI-06 (requires a new named business definition). | `processing/` cohort assignment; KPI tests for period edges, offsets, statuses. | No raw-record change; adds downstream semantics. |
| Completion cohort event | Assign completed outcomes by `completed_at`; do not silently substitute `opened_at`. Decide explicitly whether canceled jobs are excluded or form a separate population. | Include cancellation as a terminal outcome (requires an approved status/outcome meaning); exclude canceled records from completion metrics (simpler but needs a documented denominator). | `processing/`; KPI population tests for completed/cancelled/in-progress. | Uses approved fields/statuses; adds eligibility rules. |
| Turnaround cohort and eligibility | Require both `opened_at` and `completed_at`, assign by completion timestamp, and state that this is a proposal pending owner selection. | Assign by opening timestamp or report both cohorts as different measures; results answer different operational questions. | `processing/`, analytics tests for missing completion and boundary events. | No field change; cohort behavior is new. |
| Maturity-buffer use and boundary | Apply the configured day buffer only to explicitly named outcome/completion measures, using an explicit UTC reference timestamp and a documented inclusive/exclusive cutoff. Decide each measure’s cutoff before implementation. | Apply globally to all metrics (couples unrelated measures); omit the buffer for a metric (may include immature outcomes). | `processing/` and relevant analytics tests with reference-time injection and exact boundary cases. | Preserves approved setting; selection of metrics and formula requires approval. |
| Reference timestamp | Supply one explicit aware timestamp per processing run, normalize it to UTC, and reuse it throughout that run; do not call the wall clock implicitly in deterministic logic. | Capture a clock value inside orchestration (less reproducible in tests); use a reporting-period end (can differ from the actual evaluation time). | Pipeline/config or processing input contract; deterministic tests. | Consistent with UTC and master-plan determinism; makes input contract explicit. |
| UTC period boundaries | Retain approved `[start_utc, end_utc)` containment for all period membership. | No alternative proposed; clarify only which event timestamp is tested for each cohort. | `processing/` boundary tests. | No change to approved period model. |
| Immature observations | Recommended default: exclude from an evaluated KPI denominator and expose a count/limitation separately; do not convert absence to zero. Approve per KPI because populations differ. | Include as pending (changes denominator and interpretation); suppress the whole metric (loses available mature observations). | `analytics/` population and status tests; report limitation tests. | Respects tri-state semantics but adds KPI-specific behavior. |
| Cancelled/in-progress and absent completion time | Recommended default: cancelled jobs are not completed; in-progress jobs and records missing `completed_at` are ineligible for completion/turnaround measures, but remain available to intake measures. | Treat cancellation as a separate completion outcome; reject missing completion upstream (would conflict with optional `completed_at`); exclude the records from all analysis. | `processing/` and per-KPI tests. | No raw schema change; requires approved analytics rules. |
| KPI-06 identity | Do not use KPI-06 until its owner-approved name, purpose, population, and formula are recorded. If “Matured Intake Cohort” is desired, approve it as a distinct catalogue entry rather than inferring it from `ING-11`. | Select another name/metric or leave the ID unused. Assigning the ID without approval creates a false source of authority. | KPI catalogue and tests. | New named KPI; no existing approved formula to preserve. |

## 4. KPI catalogue decisions

**Operational problem:** the model can represent a metric result, but there is no approved catalogue defining what a KPI means. `DATA_AND_ANALYTICS.md` §6, `PRODUCT_REQUIREMENTS.md` §4, and `OPRA-MODELS-001` D-03 leave identifiers/formulas open. No formulas are supplied here.

| Decision for owner | RECOMMENDED option | Alternatives and consequences | Affected modules/tests | Approved-contract effect |
|---|---|---|---|---|
| Catalogue and IDs/names | Approve a versioned, small v1 automotive catalogue; for each entry sign off ID, stable name, purpose, and owner. Keep KPI-01…06 as unassigned examples until approved; decide explicitly whether KPI-06 is the matured intake concept. | Start with fewer KPIs or use descriptive IDs; either is simpler but changes expected catalog size/naming. | `analytics/` catalogue, public exports if any, table-driven tests. | Fills unresolved business scope; does not change generic `MetricResult`. |
| Definition for every KPI | Require owner-supplied formula, numerator, denominator, eligible records, source fields, grouping/aggregation, unit, and missing-data rules before coding. | Approve them KPI by KPI across separate reviews; slower but narrows each decision. No formula should be inferred from a name. | `analytics/` implementation; one formula/edge-case test set per KPI. | Adds business definitions; no raw-record change. |
| Precision and rounding | Preserve exact Decimal inputs/intermediates; specify output scale and rounding mode for each KPI, and round only at an approved presentation/result boundary. | Keep full precision in results and round only for display; simpler but consumers may disagree on displayed precision. | Analytics Decimal tests, serialization tests. | Retains approved no-implicit-quantization model rule; output precision requires new approval. |
| Zero denominator and missing inputs | Decide per KPI whether result is unavailable or not applicable; reserve measured zero for a valid calculation whose result is zero. Specify partial-data behavior. | Suppress calculation or return another status only if status meaning is defined. | Analytics tests for zero, absent input, and applicable/not-applicable populations. | Uses approved `MetricStatus`; supplies unresolved mapping. |
| Aggregation and mixed currency | Specify aggregation order and whether values can be combined only within one currency. Recommended: never add amounts across currency codes without an approved conversion source/rule; report separately or unavailable. | Convert after owner approves rates/source/date methodology; adds external-data and reproducibility needs. | Analytics grouping and tests for currency partitions. | Consistent with explicit currency pairs; adds aggregation policy. |

For each approved KPI, acceptance should include a worked example supplied or approved by the owner, exact expected Decimal result, zero-denominator behavior, missing-input behavior, period/cohort assignment, and tests at all boundaries. This is a proposal for acceptance evidence, not a definition of any KPI.

## 5. Period comparison decisions

**Operational problem:** existing `MetricResult` carries one period. No comparison contract states which baseline is comparable or how a change is represented.

| Decision for owner | RECOMMENDED option | Alternatives and consequences | Affected modules/tests | Approved-contract effect |
|---|---|---|---|---|
| Comparison-period selection | Compare against an explicitly supplied prior period with the same duration and same KPI/cohort definition; never select a baseline implicitly. | Compare to a fixed historical baseline or rolling window; useful for other questions but needs period-calendar rules. | Analytics comparison model/service; selection and mismatch tests. | Adds a new comparison contract; preserves half-open periods. |
| Baseline eligibility | Require an available baseline for numeric changes and preserve current and baseline statuses in output. | Allow partial baselines or imputation; changes interpretation and needs business approval. | Analytics tests for absent, unavailable, and not-applicable baseline. | Extends generic metric representation; does not alter it. |
| Absolute change | Define as current metric minus baseline only for compatible, available values and units. | Use ratio/other domain-specific differences; not interchangeable for rates or counts. | Comparison calculations and unit compatibility tests. | New formula; owner must approve for each compatible metric class. |
| Percentage change | Do not calculate until owner approves a precise formula, units, rounding, and zero-baseline behavior. A conventional denominator choice is only a candidate, not a project requirement. | Omit percentage change and report absolute difference; less ambiguous but may be less useful across scales. | Comparison tests for positive/negative/zero baseline and precision. | Adds an unresolved derived metric. |
| Zero/missing baseline and N/A | Never fabricate a percentage from zero/missing baseline. Preserve unavailable vs not-applicable based on an approved reason mapping; a genuine current value of zero remains a measured zero. | Omit comparison field instead of emitting a status; less explicit to consumers. | Comparison/status and report serialization tests. | Aligns with approved tri-state model; mapping remains to approve. |

## 6. Intelligence decisions

**Operational problem:** no finding catalogue or rule method is approved. Configured `min_sample_size=10` is available, but it is not a confidence method and does not specify what to do below the threshold.

| Decision for owner | RECOMMENDED option | Alternatives and consequences | Affected modules/tests | Approved-contract effect |
|---|---|---|---|---|
| Finding IDs and triggers | Start with a small, explicitly enumerated deterministic rule catalogue; approve each ID, trigger inputs, exact threshold, scope, and non-trigger cases. | Defer findings until KPI acceptance; safest if no approved rule examples exist. Avoid broad “insight” labels with unclear triggers. | `intelligence/` rules and table-driven trigger tests. | Adds business rules; does not alter KPI formulas. |
| Evidence | Every finding should cite metric IDs/periods, sample size, and limitations needed to reproduce its trigger, without disclosing sensitive raw identifiers. | Provide only a summary number; easier but weaker auditability. | Finding model, privacy/traceability tests. | Aligns with existing explainability/privacy intent; exact shape new. |
| Thresholds | Use owner-approved fixed thresholds in immutable configuration; document units, comparison operator, and boundary examples. | Derive thresholds from historical distributions; adds statistical methodology and is out of current deterministic rule scope. | Config/validation and threshold-edge tests. | New threshold catalogue; no formula assumed. |
| Confidence | Defer confidence scores/tiers until an owner-approved, explainable method and calibration evidence exist; expose sample size and limitations first. | Use explicit qualitative tiers with defined criteria; needs approved rules and avoids unsupported statistical claims. | Intelligence result model and deterministic tests. | Adds new behavior; `min_sample_size` alone does not authorize it. |
| Below `min_sample_size` | Recommended: suppress the affected finding and expose a clear insufficient-sample limitation; approve whether KPI values themselves remain available. | Emit a qualified finding; more informative but risks implying support from small samples. | Intelligence tests at `n=9`, `10`, and above, with configurable minimum. | Uses approved default threshold; behavior is new. |
| Priority ordering | Define a fixed priority rank per finding and a stable tie-break by approved finding ID; avoid hidden score aggregation. | Rank by impact/confidence score; requires scales, formula, and calibration. | Recommendation/intelligence ordering tests. | New ranking rule; no current ranking contract. |
| Recommendation mapping | Approve explicit finding-to-recommendation mappings, text/content owner, and any action constraints. Until then, emit no operational recommendation. | Findings only in v1; limits actionability but avoids unsupported advice. | `recommendations/` mapping and content tests. | New recommendation content/rules. |
| Method boundary | Keep v1 intelligence deterministic and rule-based; no generative or predictive method absent a separate approval. | Later proposal may add a validated method; changes evidence, privacy, and maintenance needs. | `intelligence/` architecture tests. | Consistent with current scope and deterministic requirements. |

## 7. Reporting decisions

**Operational problem:** JSON and Markdown with execution metadata are required at a high level (`PRODUCT_REQUIREMENTS.md` FR-RPT-01; `DATA_AND_ANALYTICS.md` §5), but `OPRA-MODELS-001` D-10 defers the final schema and encoding details.

| Decision for owner | RECOMMENDED option | Alternatives and consequences | Affected modules/tests | Approved-contract effect |
|---|---|---|---|---|
| Final schema/version | Define a versioned JSON document schema with explicit sections for metadata, periods, metrics/statuses, findings, recommendations, and limitations; version independently from engine version. | Embed engine version only; consumers cannot distinguish incompatible schema changes reliably. | `reporting/` models/exporters, schema and compatibility tests. | Fills D-10; adds public output contract. |
| Decimal JSON form | Serialize Decimal as a decimal string to preserve exact scale/value; document canonical formatting. | JSON number is easier for some consumers but common decoders may lose precision; requires consumer agreement. | JSON serializer tests for large/scale-sensitive values and round trips. | New wire-format choice; does not change internal Decimal contract. |
| Missing values | Encode metric status explicitly; represent absent numeric `value` as JSON `null` (or omit only if schema explicitly chooses); represent not-applicable through status, never numeric zero. | Separate N/A token/string is consumer-friendly but risks collapsing type semantics. | JSON/Markdown status mapping tests. | Preserves approved tri-state distinction; output mapping is new. |
| Generation timestamp | Require an explicit aware `generated_at_utc` input, normalize to UTC, and include it as execution metadata; do not read wall clock inside deterministic export. | Omit timestamp from deterministic artifact; conflicts with high-level FR-RPT-01 metadata requirement unless metadata is external. | Report model and deterministic byte-output tests. | Consistent with high-level metadata plus master-plan determinism; API detail new. |
| Stable ordering | Specify ordering for metrics, findings, recommendations, periods, and keys; use stable identifiers and fixed schema order. | Preserve insertion order from upstream; easier but may vary with collection construction. | Serializer determinism tests with permuted input collections. | Makes determinism testable; adds serialization rules. |
| Markdown and escaping | Render from typed report values; escape Markdown control characters and apply formula-injection defenses only at applicable export boundaries, without mutating canonical values. | Plain interpolation is simpler but can change document meaning or create unsafe exports. | Markdown security tests for control characters and `= + - @` boundary cases. | Follows master-plan output-boundary safeguards; exact escaping policy new. |
| Schema evolution | Require explicit schema version and compatibility policy; reject unsupported major versions and document additive/minor changes. | No version field; simpler initially but consumers cannot detect breaking changes. | Version compatibility tests and report contract docs. | New wire contract. |

## 8. Dependency map

```text
Approved raw record + config + period models (implemented)
                  │
                  ▼
Owner-approved event/cohort/maturity and reference-time rules
                  │
                  ▼
Owner-approved KPI catalogue, populations, formulas, precision
                  │
                  ├──────────────► Comparison contract (compatible periods/baselines)
                  │                              │
                  └──────────────┴──────────────► Approved metric outputs
                                                 │
                                                 ▼
Finding rules + evidence + sample behavior + confidence decision
                  │
                  ▼
Recommendation mapping and priority ordering
                  │
                  ▼
Versioned reporting schema + JSON/Markdown representation
                  │
                  ▼
Pipeline and UI integration, end-to-end acceptance
```

No downstream dependency should be treated as settled solely because a model or configuration field exists. In particular, the three-day maturity default and ten-record minimum are inputs to future rules, not those rules themselves.

## 9. Proposed implementation sequence

The sequence below aligns with Package boundaries in `docs/IMPLEMENTATION_MASTER_PLAN.md` §§1, 4 and the derived index `docs/IMPLEMENTATION_ROADMAP.md`; it does not add requirements to either document.

| Order | Work | Entry dependency | Proposed acceptance evidence |
|---|---|---|---|
| 0 | Owner approval and authoritative specification updates for decisions in §§3–7. | This proposal reviewed; owner marks each decision approved, revised, or deferred. | Approved decisions recorded in the relevant specification/task record; unresolved items remain out of implementation scope. |
| 1 | Package 1 processing and analytics (Stages 4A/4B): cohort assignment, maturity evaluation, KPI catalogue, and comparisons. | Approved period/cohort/reference-time and maturity rules; complete per-KPI definitions and comparison rules. | Unit tests for UTC/half-open boundaries, maturity boundaries, status/missing cases, every formula, Decimal precision, zero denominators and comparisons; quality gates pass. |
| 2 | Package 2 intelligence and reporting (Stages 5A/5B/6A): findings, recommendations, JSON and Markdown. | Approved trigger/evidence/sample/priority/mapping rules and final report schema. | Deterministic rule and ordering tests; privacy and escaping tests; Decimal/status serialization tests; schema-version tests; quality gates pass. |
| 3 | Package 3 application integration (Stages 7A/8A). | Stable processing, analytics, intelligence and reporting interfaces. | End-to-end tests across valid data, limitations, quarantine summaries, outputs and UI boundary; no business logic in Streamlit. |
| 4 | Package 4.1 release readiness and deployment preparation. | Integrated MVP and approved release criteria. | Recorded performance/security checks, full quality gates, and local deployment preparation as specified in master plan. |
| 5 | Package 4.2 production deployment and acceptance. | Separate explicit owner authorization. | Follow master-plan deployment and acceptance gate; outside this proposal’s scope. |

### Cross-cutting proposed test expectations

- Keep exact Decimal arithmetic and explicit rounding tests for each approved KPI.
- Test tri-state values separately from measured zero.
- Use explicit reference timestamps; tests must not rely on local timezone or wall-clock timing.
- Test period start inclusion/end exclusion, and each cohort’s selected event timestamp.
- Verify deterministic ordering/output and safe handling of absent, invalid, or restricted data.
- Add no formulas, source mappings, confidence calculations, or recommendation text without owner-approved definitions.

## 10. Owner decision register (historical proposal with current resolution)

The status column below reflects the owner approval recorded in `OPRA-ANALYTICS-V1-APPROVAL-001` and the authoritative specifications it cites. The original recommendations remain preserved as the proposal history.

| Approval ID | Topic requiring owner decision | Recommended starting point | Status |
|---|---|---|---|
| A-01 | Intake, completion, and turnaround cohort event timestamps and populations | Separate event timestamps and status eligibility by cohort. | **APPROVED — `OPRA-PROCESSING-001` / `OPRA-ANALYTICS-001`** |
| A-02 | Whether KPI-06 is “Matured Intake Cohort”; ID, purpose, population, and formula | KPI-06 is the matured intake cohort count used by KPI-03/04. | **APPROVED — `OPRA-ANALYTICS-001` §3** |
| A-03 | Scope and exact boundary/application of the three-day maturity buffer | Elapsed 24-hour days; inclusive cutoff against one explicit UTC reference. | **APPROVED — `OPRA-ANALYTICS-001` §§1–2** |
| A-04 | Immature, cancelled, in-progress, and missing-completion treatment per KPI | Per-cohort status and limitation behavior defined by KPI contract. | **APPROVED — `OPRA-ANALYTICS-001` §§2–3** |
| A-05 | Complete v1 KPI catalogue and definitions, including source fields, aggregation, units, and edge cases | KPI-01 through KPI-07. | **APPROVED — `OPRA-ANALYTICS-001` §3** |
| A-06 | KPI output precision, rounding mode, zero-denominator and missing/not-applicable mappings | Exact Decimal, 50-digit intermediate precision, result rounding/status rules. | **APPROVED — `OPRA-ANALYTICS-001` §§1, 3** |
| A-07 | Comparison period/baseline selection, absolute and percentage changes, zero/missing baseline behavior | Immediately preceding equal-duration period; specified delta and zero-baseline behavior. | **APPROVED — `OPRA-ANALYTICS-001` §4** |
| A-08 | Finding IDs, triggers, thresholds, evidence, confidence, and small-sample behavior | F-001 through F-004 with evidence-sufficiency tiers, not statistical confidence. | **APPROVED — `OPRA-INTELLIGENCE-001` §§1–2** |
| A-09 | Priority ranking and finding-to-recommendation mapping/content | Fixed rank and recommendation mappings. | **APPROVED — `OPRA-INTELLIGENCE-001` §§3–4** |
| A-10 | Final report schema/version, Decimal and missing-value encoding, timestamp input, ordering, Markdown escaping | Generic schema 1.0.0 preserved; integrated schema 1.1.0 is additive. | **PARTIALLY APPROVED — `OPRA-REPORT-001` v1.1.0; scope limited to specified fields** |

**Resolution record:** The grouped approval is in `OPRA-ANALYTICS-V1-APPROVAL-001`. The integrated report scope does not include behavior outside `OPRA-REPORT-001` v1.1.0.

## Sources reviewed

- Root `AGENTS.md` §§2–4.
- `docs/reports/OPRA-ANALYTICS-AUDIT-001.md` §§1–13.
- `docs/reports/OPRA-STAGE3B-FIX-001.md`.
- `docs/specifications/OPRA-INGEST-001.md` v1.2.0, especially §§2, 4–8, 10.1–10.2 and decision register `ING-11`.
- `docs/tasks/OPRA-MODELS-001.md`, especially §§2–4, decision register D-01–D-12, and Stage 2E/2G records.
- `docs/DATA_AND_ANALYTICS.md` §§3–6; `docs/PRODUCT_REQUIREMENTS.md` §§2–4.
- `docs/IMPLEMENTATION_MASTER_PLAN.md` §§1–4; `docs/IMPLEMENTATION_ROADMAP.md` purpose, stages, and provenance.
- `docs/TECHNICAL_DESIGN.md`; `docs/PYTHON_ENGINEERING_STANDARDS.md`; `docs/TESTING_AND_QUALITY.md`; `docs/SECURITY_AND_DATA_GOVERNANCE.md`; `docs/DEPLOYMENT_AND_OPERATIONS.md`.
- Existing model modules and associated period, analytics, ingestion, and architecture tests.

**Decision-record search result:** Within the repository records reviewed, no separate owner approval was found that defines KPI-06 as a matured intake cohort. The only directly relevant approval is the generic downstream boundary in `ING-11`; the maturity setting approval is a separate configuration decision.
