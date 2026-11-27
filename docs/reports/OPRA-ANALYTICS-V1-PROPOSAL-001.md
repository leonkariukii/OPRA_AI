# OPRA.AI — Analytics v1 Owner Approval Proposal

**Task ID:** `OPRA-ANALYTICS-V1-PROPOSAL-001`  
**Prepared:** 2026-11-27  
**Status:** PROPOSAL ONLY — all new business rules below require owner approval  
**Purpose:** Provide a concrete, reviewable v1 proposal for KPI formulas, cohort maturity, comparisons, intelligence, recommendations, and the integrated report.

> **Authority notice:** Existing approvals are listed separately in §1. Nothing in this proposal amends an approved specification. All IDs, formulas, thresholds, output fields, and defaults in §§2–7 are **RECOMMENDED**, not approved. Do not implement them until the owner records approval or revisions in the authoritative decision register and specifications.

## 1. Existing approved baseline

| Existing approval | Evidence | Scope boundary |
|---|---|---|
| Raw job fields and statuses, explicit-offset timestamps normalized to UTC, strict finite `Decimal` amounts and currency pairs | `OPRA-INGEST-001` v1.2.0 §§2, 4–8; Stage 3B completion report | Defines available inputs; does not supply KPI semantics. |
| Reporting periods use UTC half-open `[start_utc, end_utc)` intervals | `OPRA-MODELS-001` D-02, §3.3 and Stage 2E completion record §8.4 | Period duration and comparison pairing are not settled by this decision. |
| `MetricStatus` distinguishes `AVAILABLE`, `UNAVAILABLE`, `NOT_APPLICABLE`; available values are finite `Decimal` | `OPRA-MODELS-001` D-05, D-06, D-11, §3.3 and Stage 2E §8.4 | Per-KPI status mapping remains to be approved. |
| `maturity_buffer_days` defaults to 3 and is configurable with a nonnegative bound; `min_sample_size` defaults to 10 and is positive | Root `AGENTS.md` §2; `OPRA-MODELS-001` §3.1 | Configuration is approved; application and statistical meaning are not. |
| Mature cohorts belong downstream of raw records | `OPRA-INGEST-001` v1.2.0 decision `ING-11`; P-02 | Does not specify a maturity calculation or KPI-06. |
| Cohort assignment uses `opened_at` for intake and `completed_at` for completed/turnaround populations; canceled/in-progress records do not enter completion/turnaround cohorts | `OPRA-PROCESSING-001` §§1–4, marked owner-directed | `OPRA-ANALYTICS-DECISIONS-001` A-01 remains open in its register; owner should reconcile that record. This proposal treats the processing contract as the candidate assignment baseline but does not expand its rules. |
| Generic metric JSON/Markdown report v1.0.0, explicit timestamp input, Decimal string serialization, stable ordering and escaping | `OPRA-REPORT-001` v1.0.1 §§2–5, marked owner-directed | Generic metrics only. Integrated findings/recommendation report remains unresolved under A-10. |

## 2. Proposed v1 automotive KPI catalogue

### 2.1 Shared calculation rules (RECOMMENDED)

1. The owner supplies an explicit aware `reference_utc_timestamp` for each execution. **Proposal:** it represents both the source snapshot's as-of instant and the evaluation instant. The source must not contain operational events after this instant in a KPI population. If the owner cannot provide a snapshot as-of value, outcome KPIs that depend on current status are `UNAVAILABLE` with a limitation; do not pretend to reconstruct historical status.
2. Period assignment uses the already specified half-open UTC periods. Intake uses `opened_at`; completion uses `completed_at` for completed records. **Proposal:** require `period.end_utc ≤ reference_utc_timestamp`; reject future or partial periods rather than comparing incomplete windows. Events after `reference_utc_timestamp` are excluded from evaluated results.
3. Each job contributes at most once to a count or amount sum. The ingestion result's valid records are the processing input; quarantined/rejected records are excluded.
4. Counts are represented as exact integral `Decimal` values to fit the existing `MetricValue` contract. No float conversion is used.
5. Percentages are `100 × numerator / denominator`, rounded to `0.01` percentage points with `ROUND_HALF_UP`, only at the KPI result boundary. Intermediate calculations use `Decimal` with local precision 50. Count and amount sums are not quantized. Owner must approve the scale and rounding mode.
6. A zero denominator maps to `NOT_APPLICABLE`. Missing required inputs or insufficient source coverage maps to `UNAVAILABLE`. A valid measured zero remains `AVAILABLE` with `Decimal("0")` (or the explicitly rounded scale).
7. No currency conversion is performed. Monetary totals are computed separately for each ISO 4217 code. Negative signed amounts are retained as credits/refunds and added algebraically; zero is included. `estimated_amount` and `paid_amount` retain distinct meanings and are not substituted for `billed_amount`.
8. A status snapshot with `status == completed` but no `completed_at` is not counted as a completion event. It remains in an eligible matured-intake denominator and creates a limitation count. Owner may instead require this inconsistency to make the relevant rate unavailable.

### 2.2 Candidate catalogue (all definitions require approval)

| Proposed ID and name | Operational purpose | Candidate formula and population | Inputs / unit | Candidate edge behavior |
|---|---|---|---|---|
| `KPI-01` — Jobs Opened | Intake volume for a reporting period. | Count valid records with `opened_at ∈ period` and `opened_at ≤ reference_utc_timestamp`, regardless of status. | `opened_at`; unit `jobs`. | Empty eligible population is `AVAILABLE` zero. No maturity filter. |
| `KPI-02` — Jobs Completed | Completed workload in the completion period. | Count records with `status == completed`, non-null `completed_at`, and `completed_at ∈ period`, where `completed_at ≤ reference_utc_timestamp`. | `status`, `completed_at`; unit `jobs`. | A completed status missing its timestamp is omitted and reported as a data limitation. Empty population is zero. |
| `KPI-03` — Matured Intake Completion Rate | Share of sufficiently aged intake jobs completed by the evaluation snapshot. | `100 × completed_matured_intake / matured_intake_count`. The numerator is matured-intake records whose snapshot status is completed and whose non-null `completed_at ≤ reference_utc_timestamp`; denominator is the KPI-06 population. | `opened_at`, status, `completed_at`, maturity buffer, reference timestamp; unit `%`. | Canceled and in-progress records remain in denominator and are not numerator. Zero denominator is `NOT_APPLICABLE`. A completed status with missing completion time is not numerator and sets a limitation. |
| `KPI-04` — Matured Intake Cancellation Rate | Share of sufficiently aged intake jobs currently marked cancelled in the source snapshot. | `100 × cancelled_matured_intake / matured_intake_count`; numerator status is cancelled within the KPI-06 population. | `opened_at`, status, maturity buffer, reference timestamp; unit `%`. | Same denominator as KPI-03. A zero denominator is `NOT_APPLICABLE`. This is a snapshot-status measure, not a cancellation-event rate; no cancellation timestamp exists in the record. |
| `KPI-05` — Observed Billed Amount | Sum billed amounts for completed jobs, by currency. | For each currency `c`, sum `billed_amount` for eligible completed-cohort records with `billed_currency == c` and a present amount. | `status`, `completed_at`, `billed_amount`, `billed_currency`; unit is the currency code. | Signed values are summed without conversion. Missing amounts are excluded from the *observed* sum and accompanied by present/eligible counts. No present amount in a non-empty eligible cohort is `UNAVAILABLE`; no eligible completed jobs is `NOT_APPLICABLE`; all known zero amounts produce available zero. |
| `KPI-06` — Matured Intake Cohort Count | The denominator population available for evaluating intake outcomes. | Count records with `opened_at ∈ period` and `opened_at + maturity_buffer_days ≤ reference_utc_timestamp`, including all canonical statuses. The buffer is elapsed 24-hour days: `timedelta(days=maturity_buffer_days)`. | `opened_at`, configured buffer, reference timestamp; unit `jobs`. | Equality at the maturity cutoff is mature. With buffer 0, records opened exactly at the reference instant are mature. Empty population is available zero. |
| `KPI-07` — Mean Completed Turnaround Hours | Average elapsed time from opening to recorded completion. | For eligible completion-cohort records with `completed_at ≥ opened_at`, calculate `sum(completed_at − opened_at in seconds) / eligible_count / 3600`; round to 0.01 hours using `ROUND_HALF_UP`. | `opened_at`, `completed_at`, completed status; unit `hours`. | Completed-status records missing `completed_at` cannot be assigned to a completion period; report them as dataset-level limitations. Negative durations are excluded and counted as limitations. An empty completed cohort is `NOT_APPLICABLE`; if all candidate records are excluded for invalid times, result is `UNAVAILABLE`. A valid zero-hour duration remains available zero. No maturity buffer is applied because the completion event is observed; this exemption requires owner approval. |

**Catalog notes for owner:** KPI names and IDs are proposals, not recovered decisions. KPI-06 is proposed as a cohort-size measure, not a “matured intake completion rate.” KPI-03 and KPI-04 use that population. KPI-05 is intentionally labeled “Observed” to avoid claiming a complete billed total when source amounts are missing. `paid_amount` and `estimated_amount` are excluded from v1 pending business use definitions.

### 2.3 Maturity rule (RECOMMENDED)

For reference instant `R`, buffer `B` days, and record open instant `O`, classify an intake record as mature exactly when:

```text
O + timedelta(days=B) <= R
```

All inputs are timezone-aware and normalized to UTC before evaluation. `R` is explicit and fixed for the entire execution. Immature records are excluded only from KPI-03/KPI-04 mature-intake populations; they remain eligible for KPI-01 and appear in a report limitation count. The cohort is period-selected by `opened_at`, then maturity-filtered. This proposal does not mutate records or put maturity state in `JobRecord`.

**Required owner choices:** confirm that the source snapshot corresponds to `R`; confirm elapsed 24-hour days rather than local calendar days; confirm inclusive `≤` cutoff; confirm cancellations/in-progress remain in the KPI-03 denominator; decide whether malformed status/timestamp combinations should make a metric unavailable.

## 3. Proposed period comparisons (RECOMMENDED)

| Topic | Candidate v1 rule |
|---|---|
| Period selection | Caller supplies the current period `[S,E)`. Baseline is the immediately preceding equal-elapsed-duration period `[S−D,S)`, where `D=E−S`. The baseline end equals current start. Both periods use UTC half-open bounds. |
| Comparability | Compare only the same approved KPI ID, unit/currency, cohort definition, and calculation version. Never compare different currencies or populations. If either period's data is incomplete under the KPI rule, preserve that status rather than silently dropping observations. |
| Absolute change | `current − baseline`. For percentage metrics this is a percentage-point change. For counts and amounts it uses the KPI's unit. Calculate using `Decimal`; no float intermediaries. |
| Relative change | Candidate formula: `100 × (current − baseline) / abs(baseline)`, rounded to 0.01% with `ROUND_HALF_UP`. A zero baseline produces `UNAVAILABLE` relative change with reason `ZERO_BASELINE`; retain absolute change if both values are available. |
| Missing/N/A | Proposed output preserves both source statuses. Derived absolute/relative changes are `NOT_APPLICABLE` if either input is not applicable; otherwise `UNAVAILABLE` if either is unavailable. A measured zero remains available. |
| Missing baseline | Do not select another period implicitly. Return an unavailable comparison and a controlled limitation identifying the missing baseline period. |

The relative-change denominator convention for negative billed totals is a proposal. The `abs(baseline)` convention makes the sign indicate direction of change relative to magnitude; owner may instead choose to omit relative comparisons for negative values.

## 4. Proposed intelligence and confidence contract (RECOMMENDED)

### 4.1 Deterministic finding catalogue candidates

| Finding ID | Trigger candidate | Minimum evidence / scope |
|---|---|---|
| `F-001` — Completion Rate Declined | KPI-03 current minus baseline is `≤ −10.00` percentage points. | Both periods available; each mature-intake denominator `n ≥ ConfigSnapshot.min_sample_size`; same period duration and KPI definition. |
| `F-002` — Cancellation Rate Increased | KPI-04 current minus baseline is `≥ +5.00` percentage points. | Same eligibility and sample requirements as F-001. |
| `F-003` — Turnaround Increased | KPI-07 relative increase `≥ 20.00%` **and** absolute increase `≥ 2.00` hours. | Both means available; at least `min_sample_size` completed records in each period. Zero baseline yields no relative trigger and a limitation. |
| `F-004` — Observed Billed Amount Declined | KPI-05 relative change `≤ −15.00%` in the same currency. | Compare only like currency. At least `min_sample_size` amount-bearing completed records in each period; do not interpret as demand, profit, or collection change. |

These are candidate operational thresholds only. They are not statistically derived and must not be described as causal or predictive. No rule evaluates customer, employee, vehicle, or job identifiers.

### 4.2 Sample size and evidence strength proposal

- Use the smallest applicable denominator across the current and baseline periods as the comparison sample size; for KPI-05 use the amount-bearing record count for the currency being compared.
- If either period is below `min_sample_size`, suppress that finding and emit a limitation `INSUFFICIENT_SAMPLE`; do not suppress an otherwise valid KPI value.
- Proposed evidence tiers (not statistical confidence): `LIMITED` for n from 10–19, `MODERATE` for 20–49, `STRONG` for n ≥ 50. If required source-field coverage is below 90%, lower the tier one level; below 80%, suppress the finding and report `INSUFFICIENT_DATA_COVERAGE`.
- Do not label these tiers probability, confidence interval, or statistical significance. If product wording requires statistical confidence, approve a separate validated method before implementation.
- Every finding includes the triggering KPI IDs, current/baseline periods and values, comparison delta, sample size, evidence tier, rule version, and limitations. It includes no raw rows or identifiers.

### 4.3 Priority proposal

Use a fixed priority per finding ID and then sort by priority rank ascending, finding ID ascending, current period start, and KPI ID. Proposed ranks: F-001 `1`, F-002 `2`, F-003 `3`, F-004 `4`. No hidden weighted score or dynamic ranking is used. The ranking and tie-break order need owner approval.

## 5. Proposed recommendation mappings (RECOMMENDED)

| Finding | Candidate recommendation | Guardrail |
|---|---|---|
| F-001 | Review the period's scheduling capacity and open-work queue; compare the same workflow categories before changing staffing or appointment policy. | The available source contract has no workflow category or staffing field. Report this as a review prompt, not a diagnosed cause. |
| F-002 | Review cancellation recording and the workshop's cancellation-reason records for the affected period. | Do not claim why cancellations increased; cancellation reasons are not present in the canonical record. |
| F-003 | Map the service process and inspect waiting stages for completed jobs in the affected period. | No bottleneck cause can be inferred from `opened_at` and `completed_at` alone. |
| F-004 | Check billed-amount completeness and billing-data capture for the affected currency and period before drawing an operational conclusion. | A decline in observed billed amount is not a revenue, demand, or profitability diagnosis. |

Emit only the fixed recommendation linked to a triggered finding. Each recommendation contains `recommendation_id`, linked `finding_id`, fixed priority, text, and limitations. If no finding triggers, emit no recommendation. No generative text, predictive advice, or external data is used.

## 6. Proposed integrated report contract (RECOMMENDED)

Keep generic report schema v1.0.0 as already specified. Add a new integrated schema version `1.1.0` only after approval; this is an additive extension and must not change v1.0.0 output.

| Section | Candidate fields and representation |
|---|---|
| `metadata` | `schema_version`, explicit `generated_at_utc`, `engine_version`, immutable `ConfigSnapshot`, `reference_utc_timestamp`, and deterministic rule/catalog versions. All timestamps are UTC ISO 8601 strings. |
| `ingestion` | Record outcome counters from the existing ingestion summary, dataset status, and privacy-safe limitation codes only. Never include raw source rows, job IDs, customer/employee/vehicle identifiers, or parser exceptions. |
| `periods` | Explicit current and baseline period IDs/labels and UTC start/end bounds. No timezone-dependent display names in machine fields. |
| `metrics` | Stable array of metric ID/name, status, value, unit/currency, period, numerator/denominator where defined, sample size, and controlled limitation codes. Decimal values are strings; absent values are JSON `null` accompanied by status. |
| `comparisons` | Metric ID, current/baseline period references, absolute change, relative change when defined, status and limitation code. Never serialize missing or N/A as numeric zero. |
| `findings` | Stable finding ID, priority, evidence tier, rule/catalog version, triggering metric references, periods, sample size, and limitation codes. No raw identifiers. |
| `recommendations` | Recommendation ID, linked finding ID, priority, approved fixed text, and limitation references. |
| `limitations` | Deduplicated controlled codes, sorted lexically, with safe human-readable descriptions. No unsanitized source values. |

**Serialization rules proposed:** JSON keys follow fixed schema order; arrays sort by the keys specified in the approved schema; Decimal strings use the existing `str(Decimal)` preservation rule; Markdown output uses typed values and the existing HTML/table/link escaping. `generated_at_utc` is supplied explicitly; exporters never read the wall clock. Schema-breaking changes increment major, additive compatible fields increment minor, and editorial-only changes increment patch.

## 7. Dependencies and proposed implementation order

| Order | Owner decision / implementation | Must precede |
|---|---|---|
| 0 | Reconcile A-01 and A-10 approval-register status; approve this proposal or record revisions. | All new business behavior. |
| 1 | Approve source snapshot/reference-time contract, cohort/maturity rule, statuses, and KPI catalogue/formulas/precision. | Processing maturity logic and KPI engine. |
| 2 | Implement/test maturity selection and KPI-01–KPI-07 only as approved. | Comparison calculations. |
| 3 | Approve comparison periods and change/status semantics; implement comparisons. | Comparison-triggered findings. |
| 4 | Approve finding IDs, numeric thresholds, sample behavior, evidence tiers/confidence terminology, and ranking. | Intelligence engine. |
| 5 | Approve fixed recommendation wording and mappings; implement recommendation stage. | Integrated report findings/recommendation sections. |
| 6 | Approve integrated schema v1.1.0 and version-compatibility behavior; implement report model/exporters. | Pipeline/UI integration. |
| 7 | Wire pipeline and presentation boundaries; test end-to-end determinism, privacy, and documented cases. | Release-readiness work. |

No formula, trigger, maturity behavior, or recommendation text should be implemented before the corresponding owner decision is recorded in the authoritative specification. Existing raw-record, period, metric-status, and generic report contracts remain unchanged.

## 8. Owner decision form

For each group, mark `APPROVE`, `REVISE`, or `DEFER`. A decision applies only to its group and does not approve dependent groups implicitly.

| Group | Owner decision | Notes / revisions |
|---|---|---|
| P-01 — Snapshot/reference time and maturity rule |  |  |
| P-02 — KPI-01 through KPI-07 names, populations and formulas |  |  |
| P-03 — KPI-06 matured intake cohort definition |  |  |
| P-04 — Decimal scale, rounding, missing/zero/currency behavior |  |  |
| P-05 — Comparison periods and change semantics |  |  |
| P-06 — Finding triggers and thresholds |  |  |
| P-07 — Sample-size and evidence/confidence policy |  |  |
| P-08 — Priority order and recommendation mappings/text |  |  |
| P-09 — Integrated report schema and compatibility |  |  |

**Overall status:** OPEN — OWNER SIGN-OFF REQUIRED. All definitions in this proposal are candidates; no implementation authorization is implied by this report.

## References reviewed

- `AGENTS.md` §§2–4.
- `docs/reports/OPRA-ANALYTICS-DECISIONS-001.md` §§1–10, especially A-01–A-10.
- `docs/specifications/OPRA-INGEST-001.md` v1.2.0 §§2, 6–7, decision `ING-11`.
- `docs/specifications/OPRA-PROCESSING-001.md` §§1–6.
- `docs/specifications/OPRA-REPORT-001.md` v1.0.1 §§2–6.
- `docs/tasks/OPRA-MODELS-001.md` D-02–D-06, D-10–D-11, §§3–4.
- `docs/PROJECT_FOUNDATION.md` §§4–6; `docs/PRODUCT_REQUIREMENTS.md` §§2–4; `docs/DATA_AND_ANALYTICS.md` §§3–6.
- `docs/TECHNICAL_DESIGN.md` §§1–2; `docs/PYTHON_ENGINEERING_STANDARDS.md` §§3–7; `docs/TESTING_AND_QUALITY.md` §§2–4; `docs/SECURITY_AND_DATA_GOVERNANCE.md` §§3–5.
