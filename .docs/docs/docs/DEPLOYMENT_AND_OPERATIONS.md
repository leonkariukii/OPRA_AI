# OPRA.AI — Deployment and Operations

**Document ID:** `OPRA-DOC-08`  
**Version:** `0.1.0-draft`  
**Status:** Approved Governance Baseline (Preserved; Production Readiness Not Yet Claimed)  
**Last Updated:** 2026-11-25  
**Related Documents:** [README.md](../README.md) | [TESTING_AND_QUALITY.md](TESTING_AND_QUALITY.md) | [SECURITY_AND_DATA_GOVERNANCE.md](SECURITY_AND_DATA_GOVERNANCE.md)

## 1. Purpose and Scope

This document defines runtime requirements, environment promotion stages (local development, CI verification, staging, and production), health verification, and operational procedures for OPRA.AI. Production readiness must never be claimed until all implementation, testing, benchmark, and deployment gates have been executed and verified.

## 2. Environment Lifecycle Stages

| Stage | Purpose | Entry / Verification Gate |
| :--- | :--- | :--- |
| **1. Local Development** | Implement tasks incrementally and run local quality/UI checks. | `uv sync --locked --extra dev`, `ruff`, `mypy`, `pytest` (`>=80%`), and `streamlit run src/opra/app/main.py`. |
| **2. CI Verification** | Automated pull-request and `main` branch enforcement via `.github/workflows/ci.yml`. | Clean execution of `ruff check .`, `ruff format --check .`, `mypy src/opra`, and `pytest --cov=opra --cov-fail-under=80` on Python `3.11`. |
| **3. Staging / Release Candidate** | End-to-end validation with synthetic datasets and performance benchmarking. | All MVP tasks complete, `scripts/benchmark_pipeline.py` (`50,000` rows `< 5.0s`) verified, and human review sign-off. |
| **4. Production** | Controlled user-facing deployment of the stateless Streamlit + Python monolith. | Explicit release approval after staging verification, health checks, and rollback readiness. |

## 3. Runtime & Execution Procedures

* **Supported Runtime:** `Python >=3.11` with locked dependencies installed via `uv sync --locked` (or `--extra dev` in development/CI).
* **Environment Configuration:** Copy `.env.example` to `.env` for local overrides; supply explicit environment variables in hosted environments without committing secrets.
* **Canonical Entrypoint:**
  ```bash
  uv run streamlit run src/opra/app/main.py