# OPRA.AI — Data Ingestion Contract

**Document ID:** `OPRA-INGEST-001`  
**Version:** `1.0.0`  
**Status:** Approved — implementation authorized for Stage 3B  
**Last Updated:** 2026-11-27  
**Related Documents:** [OPRA-MODELS-001](../tasks/OPRA-MODELS-001.md) | [Data and Analytics](../DATA_AND_ANALYTICS.md) | [Product Requirements](../PRODUCT_REQUIREMENTS.md) | [Technical Design](../TECHNICAL_DESIGN.md) | [Security and Data Governance](../SECURITY_AND_DATA_GOVERNANCE.md)

## Purpose and authority

This document defines the source-facing contract required before `records.py` and ingestion work. Existing approved constraints are labelled **Established**; approved owner decisions are labelled **APPROVED**. This document does not define KPI formulas, statistical methods, maturity calculations, or source-specific mappings not listed below.

Carry-forward decisions: Stage 2E/2G decisions `D-01`–`D-12` and `P-01`–`P-11` in [OPRA-MODELS-001](../tasks/OPRA-MODELS-001.md) remain authoritative. In particular, `ReportingPeriod` assignment is processing logic (`P-02`); timestamps are timezone-aware and normalized to UTC, with source timezone declared upstream and never inferred (`P-03`); diagnostics contain neither raw row values nor sensitive identifiers (`P-04`); collections are tuples with element validation and no implicit list coercion (`P-06`); and Decimal preservation follows `D-05`/`D-11`.

**Stage 2G provenance limitation.** The Stage 2G completion record and the detailed local definitions of `P-01` through `P-11` are not present in the inspected repository. This specification carries forward only the P-rules explicitly restated in the Stage 2H instruction and in the context supplied by the task owner; it does not reproduce or invent absent P-rule definitions.

## 1. Input sources and formats

| Item | Contract | Basis/status |
|---|---|---|
| Source | One user-supplied automotive service job/work-order dataset per run | Proposed; approval required |
| Format | UTF-8 CSV only for initial implementation | Established in Foundation, Product Requirements, Technical Design, and Security docs |
| Limits | Enforce configured `max_upload_bytes` before full parse and `max_rows` during ingestion | Established; defaults 10 MiB and 100,000 rows |
| Source timezone declaration | Not accepted as a substitute for an explicit UTC offset on any supplied timestamp | Approved under `P-03`; never inferred |
| Other formats, APIs, databases | Out of initial contract | Approved boundary; extension requires separate approval |
| Parsing | No formula evaluation or dynamic code execution; malformed/invalid UTF-8 payload fails cleanly | Established security rule |

No actual source dataset, vendor, or column naming convention is assumed.

## 2. Record structure

`ReportingPeriod` is not a raw input field and must be assigned downstream by processing (`P-02`). Input collections are immutable tuples with element validation; constructors do not silently coerce caller lists (`P-06`). The canonical record is a normalized data contract, not an analytics or maturity model.

| Field group | Proposed disposition | Notes/status |
|---|---|---|
| `job_id` | Required | Non-empty, non-whitespace `str`; preserved verbatim without trimming, case-folding, reformatting, or identifier exposure in diagnostics |
| `status` | Required | Canonical value must be `completed`, `cancelled`, or `in_progress`; explicit source-to-canonical mappings are required and unmapped values are not assigned silently |
| `opened_at` | Required | Supplied timestamp must have an explicit UTC offset and normalize to UTC |
| `completed_at` | Optional | Supplied timestamp must have an explicit UTC offset and normalize to UTC; `None` means unfinished or absent |
| Financial fields | Optional | Strict finite `Decimal` fields paired with an explicit ISO 4217 currency code whenever an amount is supplied |
| Customer, vehicle, employee, free-text notes, raw source payload | Excluded from the canonical analytical record | Sensitive source fields are not retained or exposed in diagnostics |
| Reporting period/cohort, KPI values, recommendations | Excluded | Derived downstream; no formulas or analytics logic is stored in raw records |
| Other source categories | Optional only through an approved explicit mapping | Unmapped categories are not silently assigned to canonical values |

Matured intake cohorts may be supported downstream from canonical jobs and processing metadata. Raw records contain no maturity calculation, `ReportingPeriod` assignment, or KPI formula.

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

| Rule | Approved contract |
|---|---|
| `job_id` presence | Required, non-empty, non-whitespace `str` |
| Preservation | Preserve source identifier text verbatim; do not trim, case-fold, reformat, or convert to numeric |
| Uniqueness | Evaluate after parsing; exact duplicates and conflicts follow §5 |
| Invalid | Missing, empty/whitespace-only, or non-text identifiers are record-level invalid |
| Privacy | Treat as sensitive; never include identifier in diagnostics or logs |

No normalization may merge distinct identifiers. Whitespace-only identifiers are invalid, while surrounding whitespace within a non-empty identifier is preserved rather than silently stripped.

## 5. Duplicate handling

| Case | Required outcome |
|---|---|
| Same `job_id`, all canonical parsed field values equal | Compare parsed canonical values only. Retain the first valid occurrence and classify each subsequent equal valid record as an exact duplicate; do not overwrite or add it to the valid cohort. |
| Same `job_id`, any canonical field differs | Quarantine every record with that ID and exclude all from analytical cohorts. This is established by Data and Analytics and Product Requirements. |
| Invalid records | Evaluate invalid records independently; invalid records do not participate in valid-record equality comparisons or conflict resolution. |
| Comparison basis | Compare parsed canonical values only; source row number and raw source formatting are not semantic fields. |

An exact duplicate is a subsequent valid record with parsed canonical field values equal to an earlier retained valid record. A conflicting duplicate exists only among valid canonical records and is resolved by quarantining all valid records with that `job_id`.

## 6. Dates and time

| Rule | Contract |
|---|---|
| Input representation | Every supplied timestamp must include an explicit UTC offset; offset-free timestamps are invalid |
| Source timezone | Never infer or supply a timezone as a substitute for an explicit UTC offset; never infer from OS, user or dataset location, or source-timezone metadata (`P-03`) |
| Normalization | Accept timezone-aware values, normalize to UTC, preserve instant; model behavior established in Stage 2E |
| `opened_at` | Required; missing or invalid `opened_at` is a record-level validation failure |
| `completed_at` | Optional; absence or unfinished status is represented as `None`, not as an invalid timestamp |
| Invalid timestamp | Unparseable, impossible, or timezone-naive supplied timestamps are invalid; never assume local time |
| Period assignment | Not performed in ingestion/raw record; assigned by processing (`P-02`) |
| Date-only values | Not timestamps under this contract; a date-only value is invalid unless it includes an explicit offset |

Timezone-aware timestamps are normalized to UTC before canonical storage. Missing `completed_at` is represented as `None`; it is distinct from a supplied, invalid timestamp. No source timezone declaration, OS timezone, location, or dataset metadata may supply an offset.

## 7. Financial data

| Topic | Proposed rule |
|---|---|
| Representation | Parse valid decimal strings directly into finite `Decimal` instances; do not use `float`, implicit `bool`, `int`, or `float` coercion, rounding, or quantization (`D-05`, `D-11`) |
| Invalid types | Reject `bool`, `int`, `float`, malformed text, NaN, and infinities where a `Decimal` is required |
| Currency | Every amount requires an explicit ISO 4217 currency code; no currency is inferred or defaulted |
| Negative values | Preserve signed amounts exactly; refunds, credits, and corrections require an explicitly approved source mapping and never acquire implicit accounting semantics |
| Zero | Preserve as genuine zero, distinct from missing and not applicable. |
| Missing | Preserve optional missing amount as `None`; never replace with zero. |
| Invalid amount | Invalid amount representations quarantine the affected record |
| Precision and scale | Preserve the supplied `Decimal` precision and scale; do not quantize or round |
| Currency conversion | Never convert currencies implicitly |
| Amount meanings | Billed, paid, estimated, and other amount meanings remain distinct and are never interchangeable |

No tax, gross/net, payment, refund, or accounting semantics are assumed.

## 8. Missing and invalid data

| Condition | Proposed handling |
|---|---|
| Malformed payload, invalid UTF-8, oversized upload/row count, missing or duplicate header structure | Reject the whole dataset deterministically; no partial parse result |
| Missing/invalid required `job_id`, `status`, or `opened_at` | Quarantine the affected record |
| Invalid optional `completed_at` or financial field | Quarantine the affected record |
| Missing optional field | Preserve as `None` |
| Valid measured zero | Preserve as zero |
| Not applicable | Represent explicitly only where domain semantics establish it; do not infer from blank input |
| Unknown columns | Ignore unknown source columns without retaining their values in canonical records or diagnostics |
| Blank/null tokens | Blank required fields are missing; blanks in optional fields remain `None` only when that field's approved representation permits absence |

Dataset-level failures reject all records. Record-level failures quarantine only the affected record. Unknown source columns are discarded and never retained as free-form canonical data.

## 9. Quarantine handling

Quarantine diagnostics must be privacy-safe (`P-04`): no raw source values, complete source rows, `job_id`, customer/employee/vehicle identifiers, financial line-item values, or unsanitized parser exception messages. The diagnostic shape is `{source_row_number, error_code, field_name, reason_code}`. `source_row_number` is optional metadata and must not expose row contents; field names are canonical and reasons use controlled non-sensitive vocabulary.

| Error code | Meaning |
|---|---|
| `DATASET_ENCODING_INVALID` | Input is not valid UTF-8 |
| `DATASET_STRUCTURE_INVALID` | Header/structure invalid |
| `DATASET_LIMIT_EXCEEDED` | Configured size or row bound exceeded |
| `RECORD_REQUIRED_FIELD_MISSING` | Required field absent/blank |
| `RECORD_FIELD_INVALID` | Field cannot satisfy its declared type/constraint |
| `RECORD_DUPLICATE_CONFLICT` | Same `job_id` has conflicting canonical values; all such records quarantined |

Parser exception text is never copied into a diagnostic. Row numbering, aggregation, and diagnostic limits are implementation details, but the public diagnostic contract remains limited to the controlled fields and codes above.

## 10. Validation workflow

Approved deterministic workflow, in order:

1. Check upload byte limit; decode strict UTF-8; reject malformed payload.
2. Parse CSV structure without evaluating formulas; validate header shape and row limit.
3. Map approved canonical fields and validate field types/requiredness; collect safe diagnostics.
4. Normalize aware timestamps to UTC and preserve Decimal values without rounding.
5. Validate `job_id`; group records by identifier and distinguish exact duplicates from conflicts.
6. Emit immutable valid-record tuple and immutable quarantine-diagnostic tuple; exclude all conflicting-ID records.

Dataset-level failures produce a failed ingestion outcome and no valid records. Record-level failures produce quarantined diagnostics; only records satisfying the approved contract proceed.

## 11. Extensibility

Keep the core contract limited to stable shared concepts (identity, typed optional values, explicit timestamps, currency-tagged amounts, privacy-safe diagnostics). Source adapters may map vendor columns and declared semantics into the canonical contract before validation, but may not silently invent values or meanings. Automotive categories/statuses require explicit mapping. Non-automotive domains should add separately approved domain schemas/adapters and domain-specific validation; they must not change existing automotive field meanings or core identity/time/precision/privacy guarantees. Version schema changes and keep unknown source-specific fields out of core records unless approved.

This extension approach is approved; no adapter framework or additional runtime dependency is authorized here.

## Decision Register

The nine owner-decision groups below are `APPROVED`. `ING-01` and `ING-06` remain `Established` baseline rules and are not counted as owner-decision groups.

| ID | Topic | Proposed Decision | Rationale | Status | Dependencies |
|---|---|---|---|---|---|
| ING-01 | Initial sources/formats | One uploaded UTF-8 CSV per run; configured byte/row limits | Matches MVP baseline | Established | None |
| ING-02 | Canonical schema and field definitions | Require `job_id`, canonical `status`, `opened_at`, optional `completed_at`, and optional strict `Decimal` fields with ISO 4217 currency; preserve identifiers verbatim and require explicit source mappings | Consolidates the canonical schema, column/enum, and identifier decisions; enables downstream analysis without inventing formulas or unmapped statuses | APPROVED | `D-01`, `D-05`, `D-11`, `P-02`, `P-06` |
| ING-03 | Exact duplicates | Compare parsed canonical field values; retain the first valid occurrence and classify subsequent equal valid records as exact duplicates | Provides deterministic, non-overwriting duplicate handling | APPROVED | `D-01`, `FR-VAL-01`, `P-04` |
| ING-04 | Timestamp contract | Require an explicit UTC offset on every supplied timestamp, normalize to UTC, reject naive/inferred timestamps, require `opened_at`, and represent absent `completed_at` as `None` | Prevents implicit local-time assumptions and distinguishes missing completion from invalid timestamps | APPROVED | `D-02`, `D-11`, `P-02`, `P-03` |
| ING-05 | Financial contract | Parse decimal strings directly to finite `Decimal`; preserve precision and scale; require ISO 4217 currency; distinguish zero, missing, and separate amount meanings | Prevents conversion, rounding, implicit currency, and value-semantics errors | APPROVED | `D-05`, `D-11`, `P-06` |
| ING-06 | Conflicting duplicates | Quarantine all records for conflicting `job_id` and exclude from cohorts | Existing duplicate policy | Established | `job_id` definition |
| ING-07 | Invalid-record policy | Reject dataset-level encoding, limit, structure/header, and duplicate-header failures; quarantine record-level failures | Separates total dataset failure from affected-record failure | APPROVED | `D-01`, `FR-ING-01`, `FR-VAL-01`, `P-04` |
| ING-08 | Missing and unknown columns | Preserve missing optional fields as `None`, reject invalid required fields, and ignore unknown source columns without retaining values | Prevents silent coercion and retention of unmapped source data | APPROVED | `D-01`, `D-06`, `D-11`, `P-06` |
| ING-09 | Quarantine diagnostics | Use controlled error/reason codes only; exclude raw values, full rows, identifiers, financial line items, and unsanitized parser exceptions | Provides privacy-safe structured review | APPROVED | `D-01`, `P-04`, security governance |
| ING-11 | Matured intake cohorts | Support downstream matured cohorts without `ReportingPeriod`, maturity logic, or KPI formulas in raw records | Keeps cohort support separate from ingestion and analytics | APPROVED | `D-02`, `P-02`, `P-03` |
| ING-12 | Future domains | Add versioned adapters and separately approved domain schemas without changing core automotive semantics | Enables governed extension rather than core destabilization | APPROVED | `P-02`, `P-03`, `P-04`, `P-06`, `D-05`, `D-11` |

## Open assumptions and limitations

No source files or sample datasets were supplied or claimed as verified. Vendor mappings are not listed unless explicitly canonicalized above. This contract authorizes only the specification stage and Stage 3B implementation work named in the approved status.

The repository copy inspected for this specification does not contain the Stage 2G completion record or detailed `P-01`–`P-11` text; therefore, no P-rule beyond the four explicitly supplied by the task owner (`P-02`, `P-03`, `P-04`, `P-06`) is reconstructed here.

## Revision history

| Version | Date | Summary |
|---|---|---|
| `0.1.0-draft` | 2026-11-27 | Initial proposed ingestion contract; separates established project constraints from owner decisions. |
| `1.0.0` | 2026-11-27 | Incorporates the nine approved owner decisions and resolves Stage 3A audit blockers. Canonical schema, timestamps, duplicates, finances, invalid data, privacy, cohorts, and extensibility are now approved without rewriting prior history. |
