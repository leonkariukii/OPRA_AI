# OPRA.AI — Implementation Roadmap

**Document ID:** `OPRA-ROADMAP-001`  
**Status:** Derived execution index; see approval status in the linked master plan  
**Last Updated:** 2026-11-27  
**Authority:** [Consolidated MVP Implementation Master Plan](IMPLEMENTATION_MASTER_PLAN.md)

## Purpose

This roadmap is a navigation aid derived from the package sequence in `OPRA-PLAN-MASTER-001`. It does not claim to recover an earlier roadmap or add requirements. The master plan and approved specifications remain authoritative. Execute only the scope and gates stated there.

## Dependency-ordered stages

| Order | Stage/package | Scope | Gate / boundary |
|---|---|---|---|
| Baseline | Stage 3A | Ingestion specification finalization | Completed per master plan; verify repository copy and version before implementation |
| Checkpoint | Baseline Verification | Verify repository paths, Git status, existing quality results, coverage, and package gaps | Required before code changes; stop on missing required approved specifications or unresolved contract gaps |
| 1 | Package 1, Stage 3B | Records, CSV ingestion/validation/quarantine | Completed per `OPRA-STAGE3B-FIX-001`; preserve the verified ingestion contract |
| 1A | Package 1, Stage 4A: Processing Cohort Membership | Intake, completion, and turnaround cohort assignment under `OPRA-PROCESSING-001`; period membership, input order, immutable inputs/results | Depends on Stage 3B canonical `JobRecord` and approved `ReportingPeriod`; does not apply maturity, compute durations, calculate KPIs, or compare periods |
| 1B | Package 1, Stage 4B: Analytics Eligibility and Calculations | Reference-time and maturity rules, KPI-01–KPI-07, KPI-07 nonnegative-duration eligibility and limitation counts, approved period comparisons under `OPRA-ANALYTICS-001` | Depends on Stage 4A cohorts; preserve existing models and `OPRA-REPORT-001` v1.1.0 serialization; run package quality gates |
| 2 | Package 2: Stages 5A, 5B, 6A | Findings, recommendations, deterministic JSON and Markdown reports | Depends on Package 1 contracts; run and record quality gates |
| 3 | Package 3: Stages 7A, 8A | Presentation integration, uploads, feedback, dashboards, downloads, pipeline wiring, end-to-end tests | Preserve Streamlit boundary; run and record quality gates |
| 4.1 | Package 4.1: Stages 8B, 9A | Performance/security checks, final coverage, local deployment preparation and validation | Stop after local readiness; no live deployment or remote Git writes |
| 4.2 | Package 4.2: Stage 9B | Production deployment and acceptance | Separate explicit owner authorization required; excluded from autonomous execution |

## Package 1 stage boundaries and acceptance

Owner decisions A-01 and A-11, recorded in [the analytics decision register](reports/OPRA-ANALYTICS-DECISIONS-001.md) and [Package 1 reconciliation report](reports/OPRA-PACKAGE1-RECONCILIATION-001.md), separate cohort membership from downstream KPI eligibility:

- **Stage 4A:** Follow `OPRA-PROCESSING-001` §§2–5. A completed record with in-period `completed_at` remains in both completion and turnaround cohorts even if `completed_at < opened_at`. Processing preserves input order and immutable tuples/records; it does not perform maturity filtering, duration calculations, KPI calculations, or comparisons.
- **Stage 4B:** Follow `OPRA-ANALYTICS-001` §§1–5. Apply explicit reference time and maturity rules, calculate KPI-01–KPI-07, exclude negative durations only from KPI-07, include equal timestamps as zero duration, count negative exclusions using `NEGATIVE_TURNAROUND_DURATION` in the existing `AnalysisLimitation`, and calculate approved comparisons. Serialize limitations using the existing integrated contract in `OPRA-REPORT-001` v1.1.0.
- **Acceptance:** Each stage requires focused tests for its boundary, review of actual quality-gate output, and a completion report. Stage status is determined from those results; the existence of implementation files alone does not establish completion. Package 2 remains dependent on completed and accepted Package 1 contracts.

## Execution controls

- Use the package scopes, authoritative sources, quality gates, and stop conditions in [IMPLEMENTATION_MASTER_PLAN.md](IMPLEMENTATION_MASTER_PLAN.md).
- Do not infer missing business rules, source mappings, KPI formulas, or statistical methods.
- Record baseline and package-boundary results with actual command output; distinguish pre-existing failures from regressions.
- No production deployment, production credential use, Git commits, pushes, or remote repository writes without the authorizations specified in the master plan.

## Provenance

Created 2026-11-27 to provide the repository path referenced by the supplied master execution prompt. The stage sequence above is transcribed from that plan. No separate historical roadmap content was available in the repository or supplied attachments.
