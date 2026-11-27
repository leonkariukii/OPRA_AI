# OPRA.AI — Analytics v1 Owner Approval Record

**Record ID:** `OPRA-ANALYTICS-V1-APPROVAL-001`  
**Date:** 2026-11-27  
**Source:** Owner instruction in this conversation: “implement the recommended fix and finish the implementation of code, full authorization and no blockage whatsoever.”  
**Decision:** APPROVED — adopt the recommended v1 rules in `OPRA-ANALYTICS-V1-PROPOSAL-001` for implementation, subject to the clarifications recorded in the authoritative specifications listed below.

## Approved scope

| Decision group | Approved scope | Authority after this record |
|---|---|---|
| Cohort and maturity | Intake by `opened_at`; completion/turnaround by completed status and `completed_at`; half-open periods; fixed explicit UTC reference; elapsed-day maturity cutoff; matured intake population and stated status handling. | `docs/specifications/OPRA-PROCESSING-001.md` v1.1.0 and `OPRA-ANALYTICS-001.md` v1.0.0 |
| KPI catalogue | KPI-01 through KPI-07 names, populations, formulas, units, precision, currency separation, and missing/zero handling in the analytics specification. | `docs/specifications/OPRA-ANALYTICS-001.md` v1.0.0 |
| Comparisons | Immediately preceding equal-duration period, absolute and relative change formulas, status behavior, and zero-baseline rule. | `docs/specifications/OPRA-ANALYTICS-001.md` v1.0.0 |
| Findings and evidence | F-001 through F-004 deterministic thresholds, minimum sample handling, evidence tiers, coverage cutoffs, and ordering. Evidence tiers are not statistical probability claims. | `docs/specifications/OPRA-INTELLIGENCE-001.md` v1.0.0 |
| Recommendations | Fixed finding-to-recommendation mappings and ordering. Recommendations are review prompts and do not assert causes. | `docs/specifications/OPRA-INTELLIGENCE-001.md` v1.0.0 |
| Integrated report | Additive schema `1.1.0` with metrics, comparisons, findings, recommendations, ingestion summary, and privacy-safe limitations; retain generic schema `1.0.0`. | `docs/specifications/OPRA-REPORT-001.md` v1.1.0 |

## Preserved boundaries

- `OPRA-INGEST-001` v1.2.0 and `OPRA-MODELS-001` approved model contracts are unchanged.
- `JobRecord` remains raw and does not gain reporting-period, maturity, or KPI fields (P-02).
- Strict `Decimal`, immutable tuple collections, UTC normalization, privacy-safe diagnostics, stateless processing, and the Streamlit boundary remain in force.
- No predictive or generative methods, external data, currency conversion, root-cause inference, storage, or deployment behavior is authorized by this record.

## Register reconciliation

This approval supersedes the proposal-only status for the approved items above. A-01 is resolved for the cohort rules recorded in `OPRA-PROCESSING-001`/`OPRA-ANALYTICS-001`. A-10 is resolved only for generic metric reporting plus the integrated report schema recorded in `OPRA-REPORT-001`; it does not approve behavior outside those contracts.

All approvals apply to the exact versioned specifications above. Later changes require a new owner decision.
