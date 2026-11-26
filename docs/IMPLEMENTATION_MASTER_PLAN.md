# OPRA.AI — Consolidated MVP Implementation Master Plan

**Document ID:** OPRA-PLAN-MASTER-001  
**Status:** Approved for Execution  
**Baseline Completed:** Stage 3A (Ingestion Specification Finalization)  
**Target:** End-to-End MVP Release Readiness (Packages 1–4.1) & Gated Production Acceptance (Package 4.2)

---

## 1. Purpose & Execution Strategy

This master plan consolidates the remaining OPRA.AI MVP work into **four dependency-ordered implementation packages**, with Package 4 divided into **Package 4.1** (autonomous release readiness and deployment preparation) and **Package 4.2** (owner-authorized production deployment and acceptance). Rather than running one prompt per small milestone with repeated owner approval loops, the coding agent executes Packages 1 through 4.1 in one coordinated implementation cycle while respecting existing contracts, baseline diagnostics, and package-level quality gates.

### Authoritative Governance & Specifications
Existing approved governance and technical documents remain authoritative for implementation decisions. The roadmap file is a navigation index derived from this master plan; it is not recovered historical roadmap content and is not an independent source of requirements. Before implementation, the coding agent must verify actual repository paths rather than assuming any referenced document exists. If a required approved specification is missing, the agent must report a structured blocker rather than creating a replacement or guessing its contents:
1. `AGENTS.md` (Repository rules, coding standards, workflow boundaries)
2. `docs/IMPLEMENTATION_ROADMAP.md` (Derived navigation index only; use this master plan and approved specifications for requirements)
3. `docs/specifications/OPRA-INGEST-001.md` v1.0.0 (CSV ingestion, validation, duplicate detection, and quarantine rules)
4. `OPRA-MODELS-001.md` (verify exact path in `docs/` or `docs/specifications/`) and existing model modules/tests (Domain models, contracts, and public exports)
5. Approved product, technical, analytics, reporting, and security specifications in `docs/`

---

## 2. Non-Negotiable Architectural, Data & Execution Safeguards

- **Python 3.11+ Compatibility:** Strictly maintain Python 3.11+ syntax, typing, and runtime compatibility.
- **UI Boundary & Entrypoint:** Preserve `src/opra/app/main.py` as the Streamlit application entrypoint and respect the `src/opra/app/` boundary. Streamlit is strictly a presentation and orchestration layer; zero business logic, financial calculations, or CSV parsing rules may reside in UI files.
- **Contract & Field Integrity:** Do not introduce source mappings or financial fields that are not explicitly approved in specifications. Do not alter existing public model contracts or exports merely to simplify integration.
- **Strict `Decimal` Financial Math:** Use `decimal.Decimal` for all monetary amounts, rates, percentages, and KPI calculations. Never use `float` for financial or KPI math.
- **Deterministic Reports & Timestamps:** Identical inputs and explicit parameters must produce byte-identical analytics outputs, ranked findings, JSON reports, and Markdown reports. Do not inject uncontrolled current-time metadata (`datetime.now()` / wall-clock timestamps) into exported artifacts; either omit generation timestamps from deterministic output or use an explicit reporting/reference timestamp supplied by specification or input.
- **Output-Boundary Formula Injection Protection:** Apply formula-injection defense (`=`, `+`, `-`, `@` leading-character guards where required by export/spreadsheet/Markdown security rules) strictly at output boundaries without mutating canonical financial figures or corrupting legitimate negative numbers in domain models, KPI calculations, or canonical data fields.
- **Stateless MVP:** No database, ORM, or server-side persistent storage in the MVP.
- **Privacy-Safe Diagnostics:** Logs, error messages, quarantine summaries, and reports must never expose raw customer PII or sensitive row payloads.
- **Dependency & Git Control:** Do not add unapproved dependencies to `pyproject.toml`. Do not run `git commit`, `git push`, or remote repository writes without explicit owner authorization.

---

## 3. Baseline Verification Checkpoint (Before Code Changes)

Before modifying any code, the coding agent must capture and record an initial baseline snapshot covering:
1. Actual repository file tree and verified specification paths (`AGENTS.md`, `docs/`, `src/opra/`, `tests/`).
2. Current Git working-tree status (`git status` / modified or untracked state).
3. Existing test suite results (`pytest`).
4. Existing test coverage baseline.
5. Existing `ruff check .`, `ruff format --check .`, and `mypy src/opra` results.
6. Gap inventory comparing existing implementation against remaining implementation across Packages 1–4.1.

Preserving this baseline ensures pre-existing failures or coverage gaps remain clearly distinguishable from any regressions introduced during implementation.

---

## 4. Consolidated Work Packages & Dependency Chain

```text
[Stage 3A: Ingestion Specification Finalization]
                       │
                       ▼
           [Baseline Verification Checkpoint]
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ Package 1: Data & Analytics Engine (Stages 3B + 4A + 4B) │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ Package 2: Intelligence & Reporting (Stages 5A + 5B + 6A)│
└──────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ Package 3: Application Integration (Stages 7A + 8A)      │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ Package 4: Release & Deployment (Stages 8B + 9A + 9B)    │
│   ├── Package 4.1: Release Readiness & Deployment Prep   │
│   └── Package 4.2: Owner-Authorized Production Deploy    │
└──────────────────────────────────────────────────────────┘
