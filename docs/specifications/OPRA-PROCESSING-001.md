# OPRA.AI — Automotive Record Cohort Assignment

**Document ID:** `OPRA-PROCESSING-001`  
**Version:** `1.0.0`  
**Status:** Approved for implementation by owner direction in chat on 2026-11-27 (“implement the recommended fixes and continue with implementation”).  
**Scope:** Assign canonical automotive job records to intake, completion, and turnaround period populations. This specification does not define maturity evaluation, KPI calculations, or comparisons.

## 1. Authority and boundaries

This document records the concrete cohort options recommended in `docs/reports/OPRA-ANALYTICS-DECISIONS-001.md` §3, as directed by the owner. `JobRecord` remains a raw immutable record. Cohort assignment is downstream processing in line with P-02. `ReportingPeriod` retains its approved UTC half-open `[start_utc, end_utc)` behavior.

## 2. Cohort assignment rules

| Population | Timestamp and eligibility | Period membership |
|---|---|---|
| Intake | Every input record, regardless of canonical status, uses `opened_at`. | Include the record when `opened_at` is in the supplied period. |
| Completion | Only `status == completed` and non-`None` `completed_at`. | Include when `completed_at` is in the supplied period. Canceled and in-progress jobs are excluded. A completed-status record with no completion timestamp is ineligible. |
| Turnaround | Same eligibility as completion; the record retains both `opened_at` and `completed_at` for a future approved turnaround method. | Assign by `completed_at`; no duration is calculated by this contract. |

Records outside the specified period are not included in that cohort. The same record may be present in intake and completion/turnaround populations when its respective event timestamps fall within the period. Input ordering is retained in each result tuple; no additional sorting or deduplication is performed.

## 3. Maturity and analytics exclusions

The configured `maturity_buffer_days` is not applied by this cohort-assignment contract. No maturity cutoff, inclusive/exclusive maturity boundary, reference-time behavior, or named metric applying the buffer has been approved. No cohort count in this document is a KPI formula. No `KPI-06` identity or meaning is established here.

## 4. Validation and immutability

- The processing input is a tuple of canonical `JobRecord` values and one `ReportingPeriod`.
- Lists are not silently converted to tuples.
- Results are frozen and contain tuple collections only.
- The operation is deterministic for equal input tuples and period values; it does not read the wall clock or mutate records.

## 5. Acceptance tests

Tests cover event timestamp choice, inclusive start/exclusive end period boundaries, statuses, missing completion timestamps, overlap across populations, preserved input order, strict tuple input, invalid model types, immutability, and repeatability. They do not assert a maturity rule, duration, KPI formula, or metric meaning.

## 6. Remaining open decisions

Maturity-buffer application and exact cutoff; KPI-06 identity and all KPI definitions; period comparison pairing/formulas; finding/confidence/priority/recommendation rules; and final integrated report behavior beyond generic metric serialization remain open. This document does not approve those decisions.

## 7. Revision history

| Version | Date | Summary |
|---|---|---|
| `1.0.0` | 2026-11-27 | Initial owner-directed cohort assignment contract, excluding maturity and KPI behavior. |
