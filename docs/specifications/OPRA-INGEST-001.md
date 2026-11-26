# OPRA.AI — Data Ingestion Contract

**Document ID:** `OPRA-INGEST-001`  
**Version:** `0.1.0-draft`  
**Status:** Draft — owner approval required before implementation  
**Last Updated:** 2026-11-27  
**Related Documents:** [OPRA-MODELS-001](../tasks/OPRA-MODELS-001.md) | [Data and Analytics](../DATA_AND_ANALYTICS.md) | [Product Requirements](../PRODUCT_REQUIREMENTS.md) | [Technical Design](../TECHNICAL_DESIGN.md) | [Security and Data Governance](../SECURITY_AND_DATA_GOVERNANCE.md)

## Purpose and authority

This document proposes the source-facing contract needed before `records.py` and ingestion work. Existing approved constraints are labelled **Established**; all new field/schema choices remain proposals and require owner sign-off. This document does not define KPI formulas, statuses, source-specific meanings, or statistical methods.

Carry-forward decisions: Stage 2E/2G decisions `D-01`–`D-12` and `P-01`–`P-11` in [OPRA-MODELS-001](../tasks/OPRA-MODELS-001.md) remain authoritative. In particular, `ReportingPeriod` assignment is processing logic (`P-02`); timestamps are timezone-aware and normalized to UTC, with source timezone declared upstream and never inferred (`P-03`); diagnostics contain neither raw row values nor sensitive identifiers (`P-04`); collections are tuples with element validation and no implicit list coercion (`P-06`); and Decimal preservation follows `D-05`/`D-11`.

**Stage 2G provenance limitation.** The Stage 2G completion record and the detailed local definitions of `P-01` through `P-11` are not present in the inspected repository. This specification carries forward only the P-rules explicitly restated in the Stage 2H instruction and in the context supplied by the task owner; it does not reproduce or invent absent P-rule definitions.

## 1. Input sources and formats

| Item | Contract | Basis/status |
|---|---|---|
| Source | One user-supplied automotive service job/work-order dataset per run | Proposed; approval required |
| Format | UTF-8 CSV only for initial implementation | Established in Foundation, Product Requirements, Technical Design, and Security docs |
| Limits | Enforce configured `max_upload_bytes` before full parse and `max_rows` during ingestion | Established; defaults 10 MiB and 100,000 rows |
| Source timezone declaration | Supplied as run/source metadata, outside raw record values, before timestamps are parsed | Proposed mechanism; required to comply with `P-03`; exact metadata shape requires approval |
| Other formats, APIs, databases | Out of initial contract | Proposed boundary; extension requires separate approval |
| Parsing | No formula evaluation or dynamic code execution; malformed/invalid UTF-8 payload fails cleanly | Established security rule |

No actual source dataset, vendor, or column naming convention is assumed.

## 2. Record structure

`ReportingPeriod` is not a raw input field and must be assigned downstream by processing (`P-02`). Input collections are immutable tuples with element validation; constructors do not silently coerce caller lists (`P-06`).

| Field group | Proposed disposition | Notes/status |
|---|---|---|
| `job_id` | Required | Established that records carry it; exact syntax proposed in §4 |
| Work lifecycle timestamps | Required: at least opened/received and completed/closed timestamps | Proposed minimum for duration and throughput analysis; exact field names and event semantics need approval |
| Monetary amounts and currency | Optional; only when source provides meaning-preserving values | Proposed; semantics/requiredness unresolved |
| Customer, vehicle, employee, free-text notes, raw source payload | Excluded from canonical analytical record | Proposed minimization; sensitive identifiers must not appear in diagnostics |
| Reporting period/cohort, KPI values, recommendations | Excluded | Derived downstream; formulas remain out of scope |
| Status, service category, parts/labor breakdown | Optional extensions only after their meanings are defined | Not assumed by this contract |

Exact canonical column names, types, requiredness, and allowed categorical values remain open.

## 3. KPI data requirements (no formulas)

The initial automotive scope needs an identifiable job and valid lifecycle timestamps to support downstream volume and elapsed-time analyses. Financial analysis additionally needs an amount and declared currency. These are data sufficiency statements, not KPI definitions or guarantees that every source supports every analysis.

| Downstream analysis family | Minimum source information proposed | Boundary |
|---|---|---|
| Job volume | Valid `job_id` | Does not define inclusion or counting formula |
| Elapsed-time / completion analysis | Defined start and end event timestamps | Does not decide which events constitute start/end or maturity handling |
| Financial analysis | Amount plus currency code and documented amount meaning | Does not define revenue, totals, tax treatment, or formula |
| Status/outcome analysis | A source-defined status/outcome and mapping approved for that source | No canonical statuses or interpretation established |

If required information is absent, the affected analysis is unavailable; ingestion must not fabricate values. Preserve `None`, not-applicable state, and genuine zero distinctly.

## 4. Identifiers

| Rule | Proposed contract |
|---|---|
| `job_id` presence | Required, non-empty after checking whitespace |
| Preservation | Preserve source identifier text exactly; do not trim, case-fold, reformat, or convert to numeric |
| Uniqueness | Evaluate after parsing; exact duplicates and conflicts follow §5 |
| Invalid | Missing, empty/whitespace-only, or non-text identifier is invalid; reject/quarantine behavior is proposed and requires approval |
| Privacy | Treat as sensitive; never include identifier in diagnostics or logs |

Whether surrounding whitespace should invalidate instead of being preserved, maximum length, character restrictions, and source namespaces are unresolved. No normalization that could merge distinct IDs is permitted absent approval.

## 5. Duplicate handling

| Case | Required outcome |
|---|---|
| Same `job_id`, all canonical parsed field values equal | Deterministically retain one canonical record; proposed survivor is first source occurrence. Count/reporting of removed duplicates needs approval. |
| Same `job_id`, any canonical field differs | Quarantine every record with that ID and exclude all from analytical cohorts. This is established by Data and Analytics and Product Requirements. |
| Comparison basis | Compare parsed canonical values only; source row order is not a semantic field. Exact normalization/comparison rules depend on approved schema. |

The first-occurrence survivor policy and definition of equality beyond identical canonical values are proposals requiring approval.

## 6. Dates and time

| Rule | Contract |
|---|---|
| Input representation | Proposed ISO 8601 timestamp with explicit UTC offset; exact accepted lexical forms require approval |
| Source timezone | Must be declared upstream for timestamps lacking an explicit offset; never infer from machine, location, or dataset (`P-03`) |
| Normalization | Accept timezone-aware values, normalize to UTC, preserve instant; model behavior established in Stage 2E |
| Missing timestamp | Required lifecycle timestamp absent => proposed record-level quarantine; optional timestamp absent remains `None` |
| Invalid timestamp | Unparseable, impossible, or timezone-naive with no declared upstream zone => reject/quarantine; never assume local time |
| Period assignment | Not performed in ingestion/raw record; assigned by processing (`P-02`) |
| Timezone declaration carrier | Source timezone, if needed, is run/source metadata supplied upstream; it is not inferred or stored as a raw per-record field | Proposed mechanism; owner approval required |

Which lifecycle timestamps are required, how ambiguous/nonexistent wall times are handled when an upstream zone is declared, and whether date-only values are allowed remain open.

## 7. Financial data

| Topic | Proposed rule |
|---|---|
| Representation | Parse accepted decimal text directly to finite `Decimal`; preserve supplied precision and scale; no float intermediary, rounding, or quantization (`D-05`, `D-11`) |
| Invalid types | Reject `bool`, `int`, `float`, malformed text, NaN, and infinities where Decimal is required; consistent with approved model strictness |
| Currency | Each amount must have an explicit source-declared currency code; no inferred/default currency. Accepted code standard and conversion policy require approval. |
| Negative values | Preserve as signed amounts; whether they mean refund, credit, correction, or other event is source-specific and requires an approved mapping. |
| Zero | Preserve as genuine zero, distinct from missing and not applicable. |
| Missing | Preserve optional missing amount as `None`; never replace with zero. |
| Invalid amount | Proposed field-level invalidation; if the field is required for the selected analysis, quarantine the record. |
| Precision bounds | Maximum digits/scale and supported currency precision are unresolved; do not impose quantization before approval. |

No tax, gross/net, payment, refund, or accounting semantics are assumed.

## 8. Missing and invalid data

| Condition | Proposed handling |
|---|---|
| Malformed payload, invalid UTF-8, oversized upload/row count, missing header structure | Fail the dataset/run deterministically; no partial parse result |
| Missing/invalid required identity or lifecycle field | Quarantine affected record, subject to owner approval of required field set |
| Invalid optional field | Record field error and quarantine record by default; owner must approve any field-level omission/partial acceptance policy |
| Missing optional field | Preserve as `None` |
| Valid measured zero | Preserve as zero |
| Not applicable | Represent explicitly only where domain semantics establish it; do not infer from blank input |
| Unknown columns | Proposed ignore only if they do not collide with canonical names; alternatively fail closed. Owner decision required |

The final choice between record quarantine and dataset rejection for individual field errors, and treatment of blank strings, null tokens, extra columns, and duplicate headers, is open.

## 9. Quarantine handling

Quarantine diagnostics must be privacy-safe (`P-04`): no raw source values, row dumps, `job_id`, customer/vehicle identifiers, financial line items, or sensitive identifier fragments. A proposed diagnostic shape is `{source_row_number, error_code, field_name, reason_code}` where field names are canonical and reason text comes from a controlled, non-sensitive vocabulary. Source row number is optional metadata and must not expose row contents.

| Error code (proposed) | Meaning |
|---|---|
| `DATASET_ENCODING_INVALID` | Input is not valid UTF-8 |
| `DATASET_STRUCTURE_INVALID` | Header/structure invalid |
| `DATASET_LIMIT_EXCEEDED` | Configured size or row bound exceeded |
| `RECORD_REQUIRED_FIELD_MISSING` | Required field absent/blank |
| `RECORD_FIELD_INVALID` | Field cannot satisfy its declared type/constraint |
| `RECORD_DUPLICATE_CONFLICT` | Same `job_id` has conflicting canonical values; all such records quarantined |

Error code names, row numbering convention, aggregation, diagnostic cap, and whether any source-row locator is safe require approval. Never place exception text from a parser into user-facing diagnostics without sanitizing it.

## 10. Validation workflow

Proposed deterministic workflow, in order:

1. Check upload byte limit; decode strict UTF-8; reject malformed payload.
2. Parse CSV structure without evaluating formulas; validate header shape and row limit.
3. Map approved canonical fields and validate field types/requiredness; collect safe diagnostics.
4. Normalize aware timestamps to UTC and preserve Decimal values without rounding.
5. Validate `job_id`; group records by identifier and distinguish exact duplicates from conflicts.
6. Emit immutable valid-record tuple and immutable quarantine-diagnostic tuple; exclude all conflicting-ID records.

Dataset-level failures produce a failed ingestion outcome and no valid records. Record-level failures produce quarantined diagnostics; only records satisfying the approved contract proceed. Exact partial-acceptance policy is open. This is a proposed order, not implemented behavior.

## 11. Extensibility

Keep the core contract limited to stable shared concepts (identity, typed optional values, explicit timestamps, currency-tagged amounts, privacy-safe diagnostics). Source adapters may map vendor columns and declared semantics into the canonical contract before validation, but may not silently invent values or meanings. Automotive categories/statuses require explicit mapping. Non-automotive domains should add separately approved domain schemas/adapters and domain-specific validation; they must not change existing automotive field meanings or core identity/time/precision/privacy guarantees. Version schema changes and keep unknown source-specific fields out of core records unless approved.

This extension approach is proposed and requires approval; no adapter framework or additional runtime dependency is authorized here.

## Decision Register

Status `OPEN — APPROVAL REQUIRED` means the owner must approve or revise before implementation. “Established” references a constraint already present in approved project docs; it is not a new owner decision.

| ID | Topic | Proposed Decision | Rationale | Status | Dependencies |
|---|---|---|---|---|---|
| ING-01 | Initial sources/formats | One uploaded UTF-8 CSV per run; configured byte/row limits | Matches MVP baseline | Established | None |
| ING-02 | Canonical schema | Require `job_id` and defined lifecycle timestamps; other groups optional/extension | Enables minimum operational analyses without formulas | OPEN — APPROVAL REQUIRED | KPI catalogue/data sufficiency |
| ING-03 | Column names/types/enums | Defer exact names, types, statuses, categories | No approved source schema exists | OPEN — APPROVAL REQUIRED | Source examples; owner semantics |
| ING-04 | Job ID | Preserve text exactly; reject missing/blank/non-text; no normalization | Prevent accidental ID collisions and disclosure | OPEN — APPROVAL REQUIRED | Source format and namespace |
| ING-05 | Exact duplicates | Keep first occurrence, remove subsequent identical canonical record | Deterministic deduplication | OPEN — APPROVAL REQUIRED | Canonical schema/equality |
| ING-06 | Conflicting duplicates | Quarantine all records for conflicting `job_id` and exclude from cohorts | Existing duplicate policy | Established | `job_id` definition |
| ING-07 | Timestamp syntax/requiredness | Require explicit offset timestamps for required lifecycle fields; normalize to UTC | Avoid inferred local timezone | OPEN — APPROVAL REQUIRED | Event semantics/source timezone declaration |
| ING-08 | Decimal/currency | Strict finite Decimal, no conversion/rounding; require explicit currency for amounts | Precision and no invented currency | OPEN — APPROVAL REQUIRED | Currency-code standard/amount semantics |
| ING-09 | Invalid-record policy | Quarantine bad records; dataset-level structural/limit failures abort dataset | Clear deterministic outcomes | OPEN — APPROVAL REQUIRED | Required-field schema/partial acceptance |
| ING-10 | Optional/unknown columns | Preserve missing as `None`; approve blank tokens, extras, duplicate header policy | Prevent silent semantic coercion | OPEN — APPROVAL REQUIRED | Source mappings |
| ING-11 | Diagnostics | Controlled codes/reasons; no raw values or sensitive identifiers | Privacy-safe review and support | OPEN — APPROVAL REQUIRED | Error taxonomy/row locator policy |
| ING-12 | Future domains | Add versioned adapters/domain schemas without changing core semantics | Extend without destabilizing records | OPEN — APPROVAL REQUIRED | Future domain governance |

## Open assumptions and limitations

No source files or sample datasets were supplied or claimed as verified. Lifecycle event names, currency representation, field semantics, schemas, and KPI data sufficiency are proposals, not established source requirements. This contract does not authorize implementation; owner approval is required first.

The repository copy inspected for this specification does not contain the Stage 2G completion record or detailed `P-01`–`P-11` text; therefore, no P-rule beyond the four explicitly supplied by the task owner (`P-02`, `P-03`, `P-04`, `P-06`) is reconstructed here.

## Revision history

| Version | Date | Summary |
|---|---|---|
| `0.1.0-draft` | 2026-11-27 | Initial proposed ingestion contract; separates established project constraints from owner decisions. |
