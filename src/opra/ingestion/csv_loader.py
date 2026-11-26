"""Deterministic UTF-8 CSV validation and quarantine."""

import csv
import io
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Final

from opra.core.config import ConfigSnapshot, OpraConfig
from opra.core.exceptions import IngestionError
from opra.models.records import ISO_4217_CODES, JobRecord, JobStatus


class IngestionErrorCode(str, Enum):
    """Stable, privacy-safe ingestion codes."""

    DATASET_ENCODING_INVALID = "DATASET_ENCODING_INVALID"
    DATASET_STRUCTURE_INVALID = "DATASET_STRUCTURE_INVALID"
    DATASET_LIMIT_EXCEEDED = "DATASET_LIMIT_EXCEEDED"
    RECORD_REQUIRED_FIELD_MISSING = "RECORD_REQUIRED_FIELD_MISSING"
    RECORD_FIELD_INVALID = "RECORD_FIELD_INVALID"
    RECORD_DUPLICATE_CONFLICT = "RECORD_DUPLICATE_CONFLICT"


@dataclass(frozen=True, slots=True)
class QuarantineDiagnostic:
    """Privacy-safe description of a quarantined record."""

    source_row_number: int | None
    error_code: IngestionErrorCode
    field_name: str | None
    reason_code: str


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Immutable ingestion outcome."""

    valid_records: tuple[JobRecord, ...]
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...]
    exact_duplicates: int = 0

    @property
    def records(self) -> tuple[JobRecord, ...]:
        """Compatibility alias for valid_records."""
        return self.valid_records

    @property
    def quarantined(self) -> tuple[QuarantineDiagnostic, ...]:
        """Compatibility alias for quarantine_diagnostics."""
        return self.quarantine_diagnostics

    @property
    def exact_duplicate_count(self) -> int:
        return len(self.exact_duplicates)


class DatasetIngestionError(IngestionError):
    """Whole-dataset rejection with a controlled code only."""

    def __init__(self, code: IngestionErrorCode) -> None:
        self.code = code
        super().__init__(code.value)


REQUIRED_HEADERS: Final[tuple[str, ...]] = ("job_id", "status", "opened_at")
AMOUNT_FIELDS: Final[tuple[str, ...]] = (
    "billed_amount",
    "paid_amount",
    "estimated_amount",
)
CURRENCY_FIELDS: Final[tuple[str, ...]] = (
    "billed_currency",
    "paid_currency",
    "estimated_currency",
)
STATUS_MAP: Final[dict[str, JobStatus]] = {
    "completed": JobStatus.COMPLETED,
    "cancelled": JobStatus.CANCELLED,
    "in_progress": JobStatus.IN_PROGRESS,
}
DECIMAL_TEXT: Final[re.Pattern[str]] = re.compile(
    r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z"
)
OFFSET_SUFFIX: Final[re.Pattern[str]] = re.compile(
    r"(?:Z|[+-]\d{2}:\d{2})\Z", re.IGNORECASE
)


def _diagnostic(
    row: int,
    code: IngestionErrorCode,
    field: str | None,
    reason: str,
) -> QuarantineDiagnostic:
    return QuarantineDiagnostic(row, code, field, reason)


def _timestamp(text: str) -> datetime:
    if not text or OFFSET_SUFFIX.search(text) is None:
        raise ValueError
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.upper().endswith("Z") else text)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(UTC)
    except (OverflowError, ValueError):
        raise


def _decimal(text: str) -> Decimal:
    if DECIMAL_TEXT.fullmatch(text) is None:
        raise InvalidOperation
    value = Decimal(text)
    if not value.is_finite():
        raise InvalidOperation
    return value


def _parse_record(
    row: dict[str, str],
    row_number: int,
) -> tuple[JobRecord | None, QuarantineDiagnostic | None]:
    job_id = row.get("job_id")
    if job_id is None or job_id == "" or job_id.strip() == "":
        return None, _diagnostic(
            row_number,
            IngestionErrorCode.RECORD_REQUIRED_FIELD_MISSING,
            "job_id",
            "REQUIRED_MISSING",
        )

    status_text = row.get("status")
    if status_text is None or status_text == "":
        return None, _diagnostic(
            row_number,
            IngestionErrorCode.RECORD_REQUIRED_FIELD_MISSING,
            "status",
            "REQUIRED_MISSING",
        )
    status = STATUS_MAP.get(status_text)
    if status is None:
        return None, _diagnostic(
            row_number,
            IngestionErrorCode.RECORD_FIELD_INVALID,
            "status",
            "VALUE_INVALID",
        )

    opened_text = row.get("opened_at")
    if opened_text is None or opened_text == "":
        return None, _diagnostic(
            row_number,
            IngestionErrorCode.RECORD_REQUIRED_FIELD_MISSING,
            "opened_at",
            "REQUIRED_MISSING",
        )
    try:
        opened_at = _timestamp(opened_text)
    except (OverflowError, ValueError):
        return None, _diagnostic(
            row_number,
            IngestionErrorCode.RECORD_FIELD_INVALID,
            "opened_at",
            "VALUE_INVALID",
        )

    completed_text = row.get("completed_at")
    completed_at: datetime | None = None
    if completed_text not in (None, ""):
        try:
            completed_at = _timestamp(completed_text)
        except (OverflowError, ValueError):
            return None, _diagnostic(
                row_number,
                IngestionErrorCode.RECORD_FIELD_INVALID,
                "completed_at",
                "VALUE_INVALID",
            )

    amount_values: dict[str, Decimal | None] = {}
    currency_values: dict[str, str | None] = {}
    for amount_field, currency_field in zip(AMOUNT_FIELDS, CURRENCY_FIELDS):
        amount_text = row.get(amount_field)
        currency = row.get(currency_field)

        if amount_text in (None, ""):
            if currency not in (None, ""):
                return None, _diagnostic(
                    row_number,
                    IngestionErrorCode.RECORD_FIELD_INVALID,
                    currency_field,
                    "CURRENCY_WITHOUT_AMOUNT",
                )
            amount_values[amount_field] = None
            currency_values[currency_field] = None
            continue

        try:
            amount = _decimal(amount_text)
        except (InvalidOperation, ValueError):
            return None, _diagnostic(
                row_number,
                IngestionErrorCode.RECORD_FIELD_INVALID,
                amount_field,
                "VALUE_INVALID",
            )

        if currency in (None, ""):
            return None, _diagnostic(
                row_number,
                IngestionErrorCode.RECORD_REQUIRED_FIELD_MISSING,
                currency_field,
                "CURRENCY_REQUIRED",
            )
        if (
            len(currency) != 3
            or not currency.isascii()
            or not currency.isalpha()
            or not currency.isupper()
            or currency not in ISO_4217_CODES
        ):
            return None, _diagnostic(
                row_number,
                IngestionErrorCode.RECORD_FIELD_INVALID,
                currency_field,
                "CURRENCY_INVALID",
            )

        amount_values[amount_field] = amount
        currency_values[currency_field] = currency

    record = JobRecord(
        job_id=job_id,
        status=status,
        opened_at=opened_at,
        completed_at=completed_at,
        billed_amount=amount_values["billed_amount"],
        billed_currency=currency_values["billed_currency"],
        paid_amount=amount_values["paid_amount"],
        paid_currency=currency_values["paid_currency"],
        estimated_amount=amount_values["estimated_amount"],
        estimated_currency=currency_values["estimated_currency"],
    )
    return record, None


def _canonical_equality_key(record: JobRecord) -> object:
    """Compare parsed canonical values, preserving Decimal scale and UTC instant."""
    amounts: tuple[tuple[object, ...] | None, ...] = ()
    return (
        record.job_id,
        record.status,
        record.opened_at,
        record.completed_at,
        (
            None
            if record.billed_amount is None
            else (record.billed_amount.as_tuple(), record.billed_currency)
        ),
        (
            None
            if record.paid_amount is None
            else (record.paid_amount.as_tuple(), record.paid_currency)
        ),
        (
            None
            if record.estimated_amount is None
            else (record.estimated_amount.as_tuple(), record.estimated_currency)
        ),
    )


def ingest_csv(
    data: bytes,
    config: ConfigSnapshot | OpraConfig,
) -> IngestionResult:
    """Validate a complete UTF-8 CSV payload and return immutable outcomes."""
    snapshot = config.snapshot() if isinstance(config, OpraConfig) else config

    if len(data) > snapshot.max_upload_bytes:
        raise DatasetIngestionError(IngestionErrorCode.DATASET_LIMIT_EXCEEDED)

    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise DatasetIngestionError(IngestionErrorCode.DATASET_ENCODING_INVALID) from None

    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        headers = next(reader)
    except (StopIteration, csv.Error):
        raise DatasetIngestionError(IngestionErrorCode.DATASET_STRUCTURE_INVALID) from None

    if (
        not headers
        or any(header == "" for header in headers)
        or len(set(headers)) != len(headers)
    ):
        raise DatasetIngestionError(IngestionErrorCode.DATASET_STRUCTURE_INVALID)
    if not set(REQUIRED_HEADERS).issubset(headers):
        raise DatasetIngestionError(IngestionErrorCode.DATASET_STRUCTURE_INVALID)

    try:
        rows = list(reader)
    except csv.Error:
        raise DatasetIngestionError(IngestionErrorCode.DATASET_STRUCTURE_INVALID) from None

    if len(rows) > snapshot.max_rows:
        raise DatasetIngestionError(IngestionErrorCode.DATASET_LIMIT_EXCEEDED)

    valid_entries: list[tuple[int, JobRecord]] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for row_number, values in enumerate(rows, start=2):
        if len(values) != len(headers):
            diagnostics.append(
                _diagnostic(
                    row_number,
                    IngestionErrorCode.RECORD_FIELD_INVALID,
                    None,
                    "ROW_SHAPE_INVALID",
                )
            )
            continue

        row = dict(zip(headers, values))
        record, diagnostic = _parse_record(row, row_number)
        if record is not None:
            valid_entries.append((row_number, record))
        elif diagnostic is not None:
            diagnostics.append(diagnostic)

    entries_by_job_id: dict[str, list[tuple[int, JobRecord]]] = {}
    for entry in valid_entries:
        entries_by_job_id.setdefault(entry[1].job_id, []).append(entry)

    retained: list[tuple[int, JobRecord]] = []
    exact_duplicate_count = 0

    for entries in entries_by_job_id.values():
        key_to_entries: dict[object, list[tuple[int, JobRecord]]] = {}
        for entry in entries:
            key = _canonical_equality_key(entry[1])
            key_to_entries.setdefault(key, []).append(entry)

        if len(key_to_entries) > 1:
            for row_number, _record in entries:
                diagnostics.append(
                    _diagnostic(
                        row_number,
                        IngestionErrorCode.RECORD_DUPLICATE_CONFLICT,
                        None,
                        "JOB_ID_CONFLICT",
                    )
                )
            continue

        first_row, first_record = sorted(entries, key=lambda item: item[0])[0]
        retained.append((first_row, first_record))
        exact_duplicate_count += len(entries) - 1

    retained.sort(key=lambda item: item[0])
    diagnostics.sort(
        key=lambda item: (
            item.source_row_number if item.source_row_number is not None else 0,
            item.error_code.value,
            item.field_name or "",
            item.reason_code,
        )
    )

    return IngestionResult(
        valid_records=tuple(record for _row_number, record in retained),
        quarantine_diagnostics=tuple(diagnostics),
        exact_duplicates=exact_duplicate_count,
    )
