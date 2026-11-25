# OPRA.AI — Technical Design

**Document ID:** `OPRA-DOC-03`  
**Version:** `0.1.0-draft`  
**Status:** Draft (Consolidated from Approved Governance Baseline; Execution Verification Pending)  
**Last Updated:** 2026-11-25  
**Related Documents:** [PROJECT_FOUNDATION.md](PROJECT_FOUNDATION.md) | [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | [DATA_AND_ANALYTICS.md](DATA_AND_ANALYTICS.md) | [PYTHON_ENGINEERING_STANDARDS.md](PYTHON_ENGINEERING_STANDARDS.md)

## 1. System Architecture and Layer Boundaries

OPRA.AI is a modular Python monolith (`src/opra/`) designed around strict unidirectional boundaries:

1. **Presentation Layer (`src/opra/app/`):** Streamlit UI (`main.py`, `pages/`, `components/`). Handles user input, session-scoped state, and rendering only. Never imports internal calculation/validation logic to bypass the pipeline or mutates shared state across sessions.
2. **Pipeline Orchestration (`src/opra/pipeline/runner.py`):** Captures a `ConfigSnapshot` at run start, invokes stages in deterministic order, and assembles the final immutable report contract.
3. **Core Processing Services (`ingestion/`, `validation/`, `processing/`, `analytics/`, `intelligence/`, `recommendations/`, `reporting/`):** Stateless, deterministic Python modules operating on immutable contracts. Core modules never import `streamlit`.
4. **Shared Contracts & Configuration (`src/opra/core/`, `src/opra/models/`):** Cross-cutting immutable configuration (`OpraConfig`, `ConfigSnapshot`), exceptions, PII-safe logging, and frozen domain models (`@dataclass(frozen=True)`, `tuple`, `MappingProxyType`).
5. **Optional Storage (`src/opra/storage/`):** Reserved boundary for approved post-MVP persistence; not required for MVP execution.

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