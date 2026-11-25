# OPRA.AI — Deployment and Operations

**Document ID:** `OPRA-DOC-08`  
**Version:** `0.1.0-draft`  
**Status:** Approved Governance Baseline (Preserved; Production Readiness Not Yet Claimed)  
**Last Updated:** 2026-11-25  
**Related Documents:** [README.md](../README.md) | [TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md) | [TESTING_AND_QUALITY.md](TESTING_AND_QUALITY.md) | [SECURITY_AND_DATA_GOVERNANCE.md](SECURITY_AND_DATA_GOVERNANCE.md)

## 1. Purpose and Scope

This document defines supported runtime setup, environment promotion stages, health verification, logging/monitoring expectations, and rollback procedures for OPRA.AI. Production readiness must never be claimed until implementation, quality gates, benchmark verification, and deployment checks have been executed and reviewed.

## 2. Environment Promotion Stages

| Stage | Scope | Verification Gate Before Advancing |
| :--- | :--- | :--- |
| **Local Development** | Feature/task work and local checks on workstation (`Python >=3.11`, `uv`). | `uv sync --locked --extra dev`, `ruff`, `mypy`, `pytest` (`>=80%`), and `uv run streamlit run src/opra/app/main.py`. |
| **CI Verification** | Automated pull-request and `main` branch checks via `.github/workflows/ci.yml`. | Passing `ruff check .`, `ruff format --check .`, `mypy src/opra`, and `pytest --cov=opra --cov-fail-under=80` on Python `3.11`. |
| **Staging / Release Candidate** | End-to-end verification with synthetic datasets and `NFR-04` performance benchmarking. | Complete MVP scope, `scripts/benchmark_pipeline.py` (`50,000` rows `< 5.0s`), and explicit review approval. |
| **Production** | Live execution of the stateless Streamlit + Python monolith. | Verified staging gate, health verification, and documented rollback readiness. |

## 3. Installation, Environment Configuration, and Launch

1. Install Python `>=3.11` and `uv`.
2. Copy `.env.example` to `.env` for local non-secret configuration (`OPRA_MAX_UPLOAD_BYTES`, `OPRA_MAX_ROWS`, `OPRA_MATURITY_BUFFER_DAYS`, `OPRA_MIN_SAMPLE_SIZE`); never commit `.env`.
3. Synchronize locked dependencies:

```bash
uv sync --locked --extra dev
Launch the Streamlit application entrypoint:

Bash
uv run streamlit run src/opra/app/main.py