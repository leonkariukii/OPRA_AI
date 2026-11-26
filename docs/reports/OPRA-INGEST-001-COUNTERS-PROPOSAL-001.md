# Proposed Amendment — OPRA-INGEST-001 Duplicate and Outcome Counters

**Status:** PROPOSAL ONLY — owner approval required  
**Target:** Add after §10 of `docs/specifications/OPRA-INGEST-001.md`, before §11. This proposal does not amend the authoritative specification.

## Proposed §10.1 Duplicate and record outcome counters

Counters are calculated independently for each ingestion invocation. They are not persisted or accumulated across retries or repeated runs. Repeating an ingestion of the same payload starts a new counter set and, with identical configuration and input, produces the same values.

Let `T` be the number of parsed data records in a successfully parsed dataset (header excluded; each CSV data record is counted once). A dataset-level failure produces no record-level outcome counters because the dataset is rejected before record processing.

| Counter | Proposed definition | Increment rule |
|---|---|---|
| `accepted_record_count` | Number of canonical records emitted in `valid_records` after validation and duplicate resolution. | Increment once per retained valid record. |
| `exact_duplicate_count` | Number of valid records after the first valid canonical occurrence for the same `job_id` whose parsed canonical values equal that first occurrence; these rows are deduplicated and not emitted. | Increment once per subsequent equal valid row. Invalid rows do not participate. |
| `conflicting_duplicate_count` | Number of valid records belonging to any `job_id` group containing more than one distinct parsed canonical value. Count every valid member of each such group, including the first row. | Increment once per valid member of a conflicting group. |
| `quarantined_record_count` | Number of input data records that receive a record-level quarantine diagnostic and are excluded from accepted output. This includes invalid records and every valid member of a conflicting group. | Increment once per distinct quarantined input record, regardless of how many diagnostic codes might be attached. |
| `rejected_record_count` | Number of parsed data records not emitted as accepted output, including exact-duplicate rows and all quarantined rows. | Increment once for each row not emitted in `valid_records`. |

### Relationships and reconciliation

These definitions intentionally distinguish a primary disposition from overlapping reason counters:

- Primary dispositions are accepted and rejected; they are mutually exclusive and exhaustive for a successfully parsed dataset: `T = accepted_record_count + rejected_record_count`.
- `quarantined_record_count` is a subset of rejected records.
- `conflicting_duplicate_count` is a subset of quarantined records.
- `exact_duplicate_count` is also a subset of rejected records, but exact duplicates do not receive quarantine diagnostics under the existing §5 definition.
- Conflicting records are both conflicting duplicates and quarantined/rejected. They are counted once in each applicable reason counter, but once only in `rejected_record_count`.
- Therefore, `rejected_record_count` must not be calculated by adding `exact_duplicate_count` and `quarantined_record_count` where those classifications overlap. A consistency check is `0 <= conflicting_duplicate_count <= quarantined_record_count <= rejected_record_count`, `0 <= exact_duplicate_count <= rejected_record_count`, and `T = accepted_record_count + rejected_record_count`.
- Invalid records are quarantined and rejected, but do not enter exact/conflict comparison. Duplicate equality and first-valid occurrence follow §5 without adding normalization rules.

A retry or second call counts its rows anew; no counter from an earlier attempt is carried forward. Dataset-level failures (encoding, structure, or limits) remain represented by the dataset error and do not produce partial counters.

## Approval questions

1. Approve or revise the proposed meaning of `rejected_record_count`, including exact duplicates as rejected from emitted output.
2. Approve conflict count as all valid records in conflicting groups rather than only the later rows.
3. Approve quarantine count as a subset of rejected, with conflicts included and exact duplicates excluded.
4. Confirm the definition of `T` for blank lines and malformed row shapes, which may need explicit treatment in §10 if counter auditing is required.
