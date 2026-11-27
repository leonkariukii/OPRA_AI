# OPRA.AI — Deterministic Metric Report Contract

**Document ID:** `OPRA-REPORT-001`  
**Version:** `1.0.0`  
**Status:** Approved for implementation by owner direction in chat on 2026-11-27 (“implement the recommended fixes and continue with implementation”).  
**Scope:** Deterministic JSON and Markdown serialization of existing generic metric results. This contract does not define KPI formulas, cohorts, findings, recommendations, or a final integrated report.

## 1. Authority and limits

This contract implements the reporting options recommended in `docs/reports/OPRA-ANALYTICS-DECISIONS-001.md` §7 to the extent supported by current public models. The owner instruction approves the recommended report encoding choices, not unresolved analytics or intelligence rules. `OPRA-MODELS-001` and `OPRA-INGEST-001` remain authoritative for their respective model boundaries.

## 2. Report document

| Field | Rule |
|---|---|
| `schema_version` | Required string, currently `1.0.0`; independent of package/engine version. |
| `generated_at_utc` | Required aware `datetime` supplied by the caller; normalize to UTC. Exporters do not read the wall clock. |
| `engine_version` | Required non-empty string supplied by the caller. |
| `config` | Required immutable `ConfigSnapshot` for the execution. |
| `metrics` | Required immutable tuple of existing `MetricResult` values; no implicit list conversion. |

This v1 schema reports generic metrics only. Findings, recommendations, caveats beyond metric status, and pipeline execution metadata beyond these fields are out of scope until their contracts are approved.

## 3. JSON representation

- UTF-8 JSON; deterministic object key order and compact separators; no insignificant whitespace or non-finite numbers.
- Root keys, in order: `schema_version`, `generated_at_utc`, `engine_version`, `config`, `metrics`.
- `generated_at_utc` and period boundaries use ISO 8601 UTC strings ending in `Z`.
- Config keys are ordered as `max_upload_bytes`, `max_rows`, `maturity_buffer_days`, `min_sample_size`.
- Each metric has keys `metric_id`, `status`, `value`, `period`; period has `start_utc`, `end_utc`.
- Metric entries are sorted by `(metric_id, period.start_utc, period.end_utc)` using their stored values. Duplicate entries are retained; the serializer does not infer or merge metric identity.
- `Decimal` values are JSON strings using `str(value)` to preserve exact value and scale. Non-available values serialize with explicit status and JSON `null`; a measured zero remains a string such as `"0"`.
- Strings use standard JSON escaping. Serialization is deterministic for the same report document.

## 4. Markdown representation

- Output is a deterministic UTF-8 Markdown document with metadata followed by a metric table.
- Metrics use the same stable ordering as JSON. Status is shown explicitly; an absent value is rendered as `—`, while `AVAILABLE` Decimal values use `str(value)`.
- Escape `\\`, `|`, backticks, and line breaks in table text so values cannot alter table structure. Do not change canonical model values.
- Markdown is not a spreadsheet formula format; do not prefix or rewrite metric values as a formula-injection workaround. Any future spreadsheet export must define its own output-boundary protection.

## 5. Compatibility and validation

- Schema-breaking changes require a major schema version. Additive compatible fields require a minor version; editorial or non-contract changes use a patch version.
- Construction rejects naive timestamps, empty engine versions, wrong config/model types, and non-tuple metric collections.
- The report model and exporters add no analytics behavior. They preserve the generic metric tri-state and exact Decimal value.

## 6. Acceptance checks

Tests must cover UTC normalization, strict tuple/model validation, stable ordering, schema field order, Decimal string precision, explicit null/status distinction, zero distinction, deterministic repeat serialization, and Markdown escaping. No tests in this contract assert KPI meaning or formulas.

## 7. Revision history

| Version | Date | Summary |
|---|---|---|
| `1.0.0` | 2026-11-27 | Initial generic metric-report contract based on owner-directed recommended choices; excludes unresolved KPI, intelligence, and recommendation behavior. |
