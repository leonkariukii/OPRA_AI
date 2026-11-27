# OPRA.AI — Deterministic Findings and Recommendations Contract

**Document ID:** `OPRA-INTELLIGENCE-001`  
**Version:** `1.0.0`  
**Status:** Approved for implementation by `OPRA-ANALYTICS-V1-APPROVAL-001`  
**Scope:** Deterministic threshold findings, evidence tiers, priorities, and fixed recommendations.

## 1. Finding rules

| Finding | Trigger | Priority |
|---|---|---:|
| `F-001` Completion Rate Declined | KPI-03 current minus baseline `<= -10.00` percentage points. | 1 |
| `F-002` Cancellation Rate Increased | KPI-04 current minus baseline `>= +5.00` percentage points. | 2 |
| `F-003` Turnaround Increased | KPI-07 relative increase `>= 20.00%` **and** absolute increase `>= 2.00` hours. | 3 |
| `F-004` Observed Billed Amount Declined | KPI-05 relative change `<= -15.00%` for the same ISO currency. | 4 |

Findings require available current and baseline metrics and `sample_size >= ConfigSnapshot.min_sample_size` in both periods. Sample size is the smaller applicable current/baseline denominator; KPI-05 uses amount-bearing records for that currency. Zero-baseline F-003/F-004 cannot trigger because relative change is unavailable. Thresholds are operational flags, not causal or predictive claims.

## 2. Evidence tiers and limitations

- `LIMITED`: `10 <= n < 20`; `MODERATE`: `20 <= n < 50`; `STRONG`: `n >= 50`.
- If required-field coverage is `< 80%`, suppress the finding and emit `INSUFFICIENT_DATA_COVERAGE`.
- If coverage is `>=80%` and `<90%`, lower the evidence tier one level. Coverage `>=90%` leaves the tier unchanged.
- If either period has `n < min_sample_size`, suppress the finding and emit `INSUFFICIENT_SAMPLE`; valid KPI values remain available.
- Evidence tiers describe sample/data sufficiency only. They are not probabilities, confidence intervals, statistical significance, or causal certainty.
- Findings contain KPI IDs, periods, metric values/changes, sample size, evidence tier, rule version, and limitation codes. They contain no raw source rows or job/customer/employee/vehicle identifiers.

## 3. Ordering

Sort findings by priority rank ascending, finding ID ascending, current period start, then KPI ID. The ranking is fixed; no hidden score is calculated.

## 4. Recommendation mappings

| Finding | Fixed recommendation | Limitation |
|---|---|---|
| F-001 | Review period scheduling capacity and the open-work queue; compare workflow categories before changing staffing or appointment policy. | Source fields do not identify workflow category or staffing; this is not a cause diagnosis. |
| F-002 | Review cancellation recording and the workshop's cancellation-reason records for the affected period. | Canonical source has no cancellation reason; do not infer why cancellations increased. |
| F-003 | Map the service process and inspect waiting stages for completed jobs in the affected period. | `opened_at` and `completed_at` alone do not identify a bottleneck cause. |
| F-004 | Check billed-amount completeness and billing-data capture for the affected currency and period. | Observed billed amount is not demand, profit, or collection performance. |

Emit one fixed recommendation per triggered finding. No finding means no recommendation. Recommendation ordering follows priority then finding ID. Text is static; there is no generative or predictive behavior and no external data.

## 5. Revision history

| Version | Date | Summary |
|---|---|---|
| `1.0.0` | 2026-11-27 | Initial owner-approved deterministic finding/evidence/recommendation contract. |
