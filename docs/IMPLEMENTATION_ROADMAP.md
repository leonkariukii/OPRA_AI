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
| 1 | Package 1: Stages 3B, 4A, 4B | Records, CSV ingestion/validation/quarantine; processing normalization, periods/cohorts; automotive analytics and tests | Run package quality gates and record actual results |
| 2 | Package 2: Stages 5A, 5B, 6A | Findings, recommendations, deterministic JSON and Markdown reports | Depends on Package 1 contracts; run and record quality gates |
| 3 | Package 3: Stages 7A, 8A | Presentation integration, uploads, feedback, dashboards, downloads, pipeline wiring, end-to-end tests | Preserve Streamlit boundary; run and record quality gates |
| 4.1 | Package 4.1: Stages 8B, 9A | Performance/security checks, final coverage, local deployment preparation and validation | Stop after local readiness; no live deployment or remote Git writes |
| 4.2 | Package 4.2: Stage 9B | Production deployment and acceptance | Separate explicit owner authorization required; excluded from autonomous execution |

## Execution controls

- Use the package scopes, authoritative sources, quality gates, and stop conditions in [IMPLEMENTATION_MASTER_PLAN.md](IMPLEMENTATION_MASTER_PLAN.md).
- Do not infer missing business rules, source mappings, KPI formulas, or statistical methods.
- Record baseline and package-boundary results with actual command output; distinguish pre-existing failures from regressions.
- No production deployment, production credential use, Git commits, pushes, or remote repository writes without the authorizations specified in the master plan.

## Provenance

Created 2026-11-27 to provide the repository path referenced by the supplied master execution prompt. The stage sequence above is transcribed from that plan. No separate historical roadmap content was available in the repository or supplied attachments.
