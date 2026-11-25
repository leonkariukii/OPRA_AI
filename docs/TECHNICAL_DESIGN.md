# OPRA.AI — Technical Design

**Document ID:** `OPRA-DOC-03`  
**Version:** `0.1.0-draft`  
**Status:** Draft (Consolidated from Approved Governance Baseline; Execution Verification Pending)  
**Last Updated:** 2026-11-25  
**Related Documents:** [PROJECT_FOUNDATION.md](PROJECT_FOUNDATION.md) | [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | [DATA_AND_ANALYTICS.md](DATA_AND_ANALYTICS.md) | [PYTHON_ENGINEERING_STANDARDS.md](PYTHON_ENGINEERING_STANDARDS.md) | [SECURITY_AND_DATA_GOVERNANCE.md](SECURITY_AND_DATA_GOVERNANCE.md) | [DEPLOYMENT_AND_OPERATIONS.md](DEPLOYMENT_AND_OPERATIONS.md)

## 1. System Architecture and Architectural Principles

OPRA.AI is designed as a modular, stateless Python monolith (`src/opra/`) that separates presentation from analytical execution and enforces strict data contracts:

* **Presentation vs. Logic Separation:** Streamlit (`src/opra/app/`) handles rendering and session-scoped UI state only; analytical logic lives in headless Python modules (`src/opra/pipeline/` and core services) with zero `streamlit` imports.
* **Stateless In-Memory Execution:** Each pipeline invocation runs in memory without a required database or cross-session dataset caching.
* **Shared Immutable Contracts:** Configuration (`OpraConfig`, `ConfigSnapshot`) and frozen domain models (`@dataclass(frozen=True)`, `tuple`, `MappingProxyType`) are shared across layers rather than acting as a late pipeline step.
* **Fail-Fast & Deterministic:** Invalid configurations and contract violations fail explicitly; identical inputs and snapshots produce deterministic outputs.

## 2. Application Layers and Module Responsibilities

| Layer / Directory | Responsibility | Key Modules |
| :--- | :--- | :--- |
| **Presentation (`app/`)** | Thin Streamlit shell, pages, and display components; delegates runs to the pipeline without computing KPIs or validation rules. | `src/opra/app/main.py`, `pages/`, `components/` |
| **Orchestration (`pipeline/`)** | Captures `ConfigSnapshot`, coordinates stage execution, and assembles final immutable report contracts. | `src/opra/pipeline/runner.py` |
| **Shared Core (`core/`)** | Centralized configuration, fail-fast validation, exception hierarchy, and PII-safe logging. | `config.py`, `exceptions.py`, `logging.py` |
| **Domain Models (`models/`)** | Deeply immutable typed contracts for records, periods, analytics outputs, and intelligence/recommendations. | `records.py`, `periods.py`, `analytics.py`, `intelligence.py` |
| **Ingestion, Validation & Processing** | UTF-8 CSV loading + size/row checks; validation + duplicate quarantine; domain normalization and maturity/cohort slicing. | `ingestion/csv_loader.py`, `validation/validator.py`, `processing/normalizer.py` |
| **Analytics, Intelligence, Recommendations & Reporting** | `Decimal` KPI calculations; deterministic findings + confidence/sample-size rules; ranked recommendations; JSON/Markdown export. | `analytics/kpi_engine.py`, `intelligence/findings_engine.py`, `recommendations/recommender.py`, `reporting/exporters.py` |
| **Optional Storage (`storage/`)** | Reserved post-MVP persistence boundary; not active in the stateless MVP. | `storage/repositories.py` |

## 3. System Architecture Diagram

```mermaid
flowchart TD
    UI["Streamlit Presentation (src/opra/app/)"]
    Runner["Pipeline Orchestrator (src/opra/pipeline/runner.py)"]
    Services["Sequential Processing Services (ingestion -> reporting)"]
    Shared["Shared Contracts & Config (src/opra/core/, src/opra/models/)"]
    Storage["Optional Storage Boundary (src/opra/storage/, post-MVP)"]

    UI -->|"delegates run"| Runner
    Runner -->|"executes stages"| Services
    UI -.->|"reads typed outputs"| Shared
    Runner -.->|"captures ConfigSnapshot & models"| Shared
    Services -.->|"consumes/produces immutable contracts"| Shared
    Services -.->|"reserved boundary only"| Storage