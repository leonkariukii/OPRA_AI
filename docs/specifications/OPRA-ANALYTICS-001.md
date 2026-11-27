# OPRA.AI — Automotive KPI and Comparison Contract

**Document ID:** `OPRA-ANALYTICS-001`  
**Version:** `1.0.0`  
**Status:** Approved for implementation by `OPRA-ANALYTICS-V1-APPROVAL-001`  
**Scope:** Cohort maturity, KPI-01 through KPI-07, and period comparisons.

## 1. Common execution rules

- Processing receives an immutable tuple of valid canonical `JobRecord` values, one current `ReportingPeriod`, an explicit aware `reference_utc_timestamp`, and immutable `ConfigSnapshot`.
- `reference_utc_timestamp` is the caller-declared as-of time for the uploaded source snapshot and evaluation. Status values are interpreted as observed in that snapshot. An absent/mismatched as-of declaration makes status-dependent metrics unavailable.
- Normalize all aware datetimes to UTC. No wall-clock call or timezone inference is allowed.
- Require `period.end_utc <= reference_utc_timestamp`; future or partial periods are invalid inputs. Period membership remains `[start_utc, end_utc)`.
- The valid ingestion records are the analytics input. Rejected and quarantined records are excluded. No record contributes more than once to one KPI observation.
- Raw `JobRecord` is never mutated or enriched with cohort/KPI fields.
- Count values are exact integral `Decimal`. No float intermediaries are allowed.
- Ratio and mean results use `Decimal` local precision 50 and round only at the result boundary with `ROUND_HALF_UP`: percentages to `0.01` percentage points and turnaround hours to `0.01`. Counts and amount sums are not quantized.
- Zero denominator is `NOT_APPLICABLE`. Missing/invalid required data is `UNAVAILABLE`. Valid measured zero is `AVAILABLE` with `Decimal(0)`.
- Maturity buffer means elapsed 24-hour days: `opened_at + timedelta(days=maturity_buffer_days) <= reference_utc_timestamp`. Equality is mature.

## 2. Cohorts

| Cohort | Population |
|---|---|
| Intake | Records with `opened_at` in the reporting period, any canonical status. |
| Matured intake | Intake records whose opening instant plus configured buffer is at or before the reference timestamp, any status. Immature records are excluded from matured-intake rates and exposed as a limitation count; they remain eligible for KPI-01. |
| Completion | `status == completed`, non-null `completed_at`, `completed_at` within the reporting period and no later than the reference timestamp. |
| Turnaround | Completion cohort records with `completed_at >= opened_at`. Negative durations are excluded and counted as a limitation. Missing completion timestamps cannot be assigned to the period and appear only as dataset-level limitations. |

Cancelled and in-progress jobs are not completion/turnaround records. They remain in matured-intake denominators: cancelled contributes to the cancellation numerator; in-progress contributes to neither completion nor cancellation numerator.

## 3. Approved KPI catalogue

| ID / name | Formula and population | Unit and edge behavior |
|---|---|---|
| `KPI-01` Jobs Opened | Count intake cohort records. | `jobs`; empty is available zero; no maturity filter. |
| `KPI-02` Jobs Completed | Count completion cohort records. | `jobs`; empty is available zero. Completed-status records without `completed_at` are excluded and reported as a dataset-level limitation. |
| `KPI-03` Matured Intake Completion Rate | `100 × completed_matured_intake / matured_intake_count`; numerator is matured-intake records with completed status and non-null completion time at or before reference. | `%`; canceled/in-progress remain in denominator. Zero denominator is `NOT_APPLICABLE`. Completed status without completion time is excluded from numerator and adds a limitation. |
| `KPI-04` Matured Intake Cancellation Rate | `100 × cancelled_matured_intake / matured_intake_count`; numerator has cancelled status in the source snapshot. | `%`; snapshot status measure, not event rate. Zero denominator is `NOT_APPLICABLE`. |
| `KPI-05` Observed Billed Amount | For each ISO currency, sum present `billed_amount` values among the completion cohort where currency matches. Emit one metric per currency. | Currency-specific. No conversion. Negative values are included algebraically as credits/refunds; zero is retained. Missing amounts are excluded and present/eligible counts reported. No completed jobs is `NOT_APPLICABLE`; completed jobs but no known billed amount is `UNAVAILABLE`; known zero amounts produce available zero. If no currency is known, emit `KPI-05:UNSPECIFIED` unavailable. |
| `KPI-06` Matured Intake Cohort Count | Count matured-intake records. | `jobs`; includes all statuses; empty is available zero. This is cohort size, not completion rate. |
| `KPI-07` Mean Completed Turnaround Hours | `sum((completed_at − opened_at) in seconds) / eligible_count / 3600`, over turnaround cohort. | `hours`, rounded to `0.01` with `ROUND_HALF_UP`. No completion jobs is `NOT_APPLICABLE`; all candidate rows excluded for invalid negative durations is `UNAVAILABLE`; valid zero duration is available zero. No maturity buffer applies to observed completions. |

`KPI-05` reports distinct currency groups without exchange-rate conversion. `paid_amount` and `estimated_amount` are not substitutes for billed amount and have no v1 KPI.

## 4. Period comparison

- Caller supplies the current period `[S,E)`. Baseline is the immediately preceding equal-elapsed-duration period `[S−D,S)`, where `D=E−S`; baseline end must equal current start.
- Compare only the same KPI ID, unit/currency, cohort definition, and calculation version. Never compare different currencies or populations.
- Absolute change is `current − baseline`. For percentage metrics this is percentage-point change.
- Relative change is `100 × (current − baseline) / abs(baseline)`, rounded to `0.01%` with `ROUND_HALF_UP`. A zero baseline yields unavailable relative change with `ZERO_BASELINE`; absolute change remains available when possible.
- If either source metric is `NOT_APPLICABLE`, comparison changes are `NOT_APPLICABLE`. Otherwise, if either is `UNAVAILABLE`, changes are `UNAVAILABLE`. Preserve both source metric statuses in the comparison result.
- A missing baseline is not replaced implicitly; both changes are unavailable with `MISSING_BASELINE`.

## 5. Limitations and determinism

Limitation codes are stable, controlled strings and contain no job IDs, raw values, or source rows. Calculations preserve input records and return frozen models with tuple collections. Output ordering is specified by the reporting contract. Identical records, periods, reference time, and configuration yield identical KPI/comparison results.

## 6. Revision history

| Version | Date | Summary |
|---|---|---|
| `1.0.0` | 2026-11-27 | Initial owner-approved automotive KPI, maturity, and comparison contract. |
