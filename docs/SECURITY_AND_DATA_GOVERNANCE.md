# OPRA.AI — Security and Data Governance

**Document ID:** `OPRA-DOC-07`  
**Version:** `0.1.0-draft`  
**Status:** Approved Governance Baseline (Preserved from Approved Governance Register)  
**Last Updated:** 2026-11-25  
**Related Documents:** [PROJECT_FOUNDATION.md](PROJECT_FOUNDATION.md) | [TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md) | [DEPLOYMENT_AND_OPERATIONS.md](DEPLOYMENT_AND_OPERATIONS.md)

## 1. Purpose and Scope

This document establishes mandatory data privacy, file upload security, secrets management, session isolation, and governance controls for OPRA.AI.

## 2. Secrets and Environment Governance

* **Zero Committed Secrets:** Never commit `.env`, API keys, tokens, credentials, or private certificates to Git. `.env` must remain listed in `.gitignore`.
* **Safe Template Only:** `.env.example` may contain only non-sensitive configuration keys and safe defaults (`OPRA_MAX_UPLOAD_BYTES`, `OPRA_MAX_ROWS`, `OPRA_MATURITY_BUFFER_DAYS`, `OPRA_MIN_SAMPLE_SIZE`).
* **Dependency Supply Chain:** Pin and verify dependencies through `pyproject.toml` and `uv.lock` (`uv sync --locked`) with least-privilege GitHub Actions permissions (`permissions: contents: read`).

## 3. Untrusted Input & Upload Controls

* **Bounded Uploads:** Treat every uploaded CSV file as untrusted input. Enforce `max_upload_bytes` (`10 * 1024 * 1024` default) before full parsing and `max_rows` (`100_000` default) during ingestion.
* **Encoding & Structure Validation:** Require valid UTF-8 decoding, verify required columns, and reject malformed or oversized payloads cleanly without executing dynamic code or formula evaluation.

## 4. Statelessness, Session Isolation, and Retention

* **No Cross-Session Dataset Caching:** Do not use global variables, module-level caches, or cross-session `@st.cache_data` storage for user-uploaded business records.
* **In-Memory MVP Lifecycle:** Uploaded operational data exists only in memory for the active user session and is discarded when the session ends or resets.
* **No Unauthorized Persistence or Egress:** Do not add database storage (`storage/`), disk retention of user uploads, or external network calls without separate explicit approval.

## 5. Logging, Error Disclosure, and Privacy

* **PII & Business Record Redaction:** Never write raw CSV rows, customer identifiers, vehicle identifiers, or financial line items into application logs or unhandled tracebacks.
* **Controlled Error Messages:** Surface structured, user-safe validation and configuration errors in the UI while keeping internal stack traces out of user-facing alerts.
* **Synthetic Data Discipline:** Development, benchmarking, and automated tests must use synthetic datasets exclusively.

## 6. Revision History

| Version | Date | Summary |
| :--- | :--- | :--- |
| `0.1.0-draft` | 2026-11-25 | Preserved approved security, upload boundary, session isolation, and PII-protection rules. |