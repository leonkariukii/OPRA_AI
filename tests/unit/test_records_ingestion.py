"""Unit tests for canonical records and deterministic CSV ingestion."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from opra.core.config import ConfigSnapshot
from opra.core.exceptions import ModelValidationError
from opra.ingestion.csv_loader import (
    DatasetIngestionError,
    IngestionErrorCode,
    ingest_csv,
)
from opra.models.records import JobRecord, JobStatus


CONFIG = ConfigSnapshot(
    max_upload_bytes=1_000_000,
    max_rows=100,
    maturity_buffer_days=3,
    min_sample_size=10,
)
OPENED = datetime(2026, 1, 1, 12, tzinfo=UTC)


def test_job_record_is_frozen_and_normalizes_utc() -> None:
    plus_two = timezone(timedelta(hours=2))
    record = JobRecord(
        "JOB-1",
        JobStatus.COMPLETED,
        datetime(2026, 1, 1, 14, tzinfo=plus_two),
        datetime(2026, 1, 2, 14, tzinfo=plus_two),
    )
    assert record.opened_at == OPENED
    assert record.opened_at.tzinfo is UTC
    assert record.completed_at == datetime(2026, 1, 2, 12, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        record.job_id = "OTHER"  # type: ignore[misc]


@pytest.mark.parametrize("value", [None, "", " ", 1, True])
def test_job_record_rejects_invalid_job_id(value: object) -> None:
    with pytest.raises(ModelValidationError):
        JobRecord(value, JobStatus.COMPLETED, OPENED)  # type: ignore[arg-type]


def test_job_record_preserves_surrounding_identifier_whitespace() -> None:
    record = JobRecord(" JOB-1 ", JobStatus.IN_PROGRESS, OPENED)
    assert record.job_id == " JOB-1 "


@pytest.mark.parametrize("value", [datetime(2026, 1, 1, 12), None])
def test_job_record_rejects_naive_or_missing_opened_at(value: object) -> None:
    with pytest.raises(ModelValidationError):
        JobRecord("JOB-1", JobStatus.IN_PROGRESS, value)  # type: ignore[arg-type]


def test_job_record_accepts_missing_completed_at() -> None:
    assert JobRecord("JOB-1", JobStatus.IN_PROGRESS, OPENED).completed_at is None


def test_job_record_rejects_naive_completed_at() -> None:
    with pytest.raises(ModelValidationError):
        JobRecord("JOB-1", JobStatus.IN_PROGRESS, OPENED, datetime(2026, 1, 2))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "currency",
    ["usd", "US", "USDD", "12D", "ZZZ", ""],
)
def test_job_record_rejects_invalid_currency(currency: str) -> None:
    with pytest.raises(ModelValidationError):
        JobRecord(
            "JOB-1",
            JobStatus.COMPLETED,
            OPENED,
            billed_amount=Decimal("12.30"),
            billed_currency=currency,
        )


def test_job_record_accepts_iso_currency_and_decimal_precision() -> None:
    record = JobRecord(
        "JOB-1",
        JobStatus.COMPLETED,
        OPENED,
        billed_amount=Decimal("12.300"),
        billed_currency="USD",
        paid_amount=Decimal("0"),
        paid_currency="USD",
    )
    assert record.billed_amount.as_tuple() == Decimal("12.300").as_tuple()
    assert record.paid_amount == Decimal("0")


def test_job_record_rejects_float_amount_and_currency_without_amount() -> None:
    with pytest.raises(ModelValidationError):
        JobRecord(
            "JOB-1",
            JobStatus.COMPLETED,
            OPENED,
            billed_amount=12.5,  # type: ignore[arg-type]
            billed_currency="USD",
        )
    with pytest.raises(ModelValidationError):
        JobRecord(
            "JOB-1",
            JobStatus.COMPLETED,
            OPENED,
            paid_currency="USD",
        )


def _csv(*rows: str) -> bytes:
    headers = (
        "job_id,status,opened_at,completed_at,billed_amount,billed_currency,"
        "paid_amount,paid_currency,estimated_amount,estimated_currency"
    )
    padded_rows: list[str] = []
    for row in rows:
        fields = row.split(",")
        if len(fields) < 10:
            fields.extend([""] * (10 - len(fields)))
        padded_rows.append(",".join(fields[:10]))
    return ("\n".join((headers, *padded_rows))).encode("utf-8")


def test_ingest_accepts_valid_record_and_normalizes_timestamp() -> None:
    result = ingest_csv(
        _csv(
            "JOB-1,completed,2026-01-01T14:00:00+02:00,,12.300,USD,12.30,USD,,"
        ),
        CONFIG,
    )
    assert len(result.records) == 1
    record = result.records[0]
    assert record.opened_at == OPENED
    assert record.completed_at is None
    assert record.billed_amount == Decimal("12.300")
    assert record.billed_currency == "USD"
    assert record.paid_amount == Decimal("12.30")
    assert record.estimated_amount is None
    assert result.quarantined == ()


def test_ingest_rejects_invalid_utf8() -> None:
    with pytest.raises(DatasetIngestionError) as exc:
        ingest_csv(b"\xff\xfe", CONFIG)
    assert exc.value.code is IngestionErrorCode.DATASET_ENCODING_INVALID


def test_ingest_rejects_upload_limit_before_parsing() -> None:
    small = ConfigSnapshot(10, 100, 3, 10)
    with pytest.raises(DatasetIngestionError) as exc:
        ingest_csv(b"job_id,status,opened_at\n", small)
    assert exc.value.code is IngestionErrorCode.DATASET_LIMIT_EXCEEDED


def test_ingest_rejects_missing_required_headers() -> None:
    with pytest.raises(DatasetIngestionError) as exc:
        ingest_csv(b"job_id,status\nJOB-1,completed\n", CONFIG)
    assert exc.value.code is IngestionErrorCode.DATASET_STRUCTURE_INVALID


def test_ingest_rejects_duplicate_headers() -> None:
    data = b"job_id,status,opened_at,job_id\nJOB-1,completed,2026-01-01T00:00:00Z,J2\n"
    with pytest.raises(DatasetIngestionError) as exc:
        ingest_csv(data, CONFIG)
    assert exc.value.code is IngestionErrorCode.DATASET_STRUCTURE_INVALID


def test_ingest_rejects_row_limit() -> None:
    limited = ConfigSnapshot(1_000_000, 1, 3, 10)
    data = _csv(
        "JOB-1,completed,2026-01-01T00:00:00Z,,,",
        "JOB-2,completed,2026-01-01T00:00:00Z,,,",
    )
    with pytest.raises(DatasetIngestionError) as exc:
        ingest_csv(data, limited)
    assert exc.value.code is IngestionErrorCode.DATASET_LIMIT_EXCEEDED


def test_ingest_rejects_naive_and_offset_free_timestamps() -> None:
    result = ingest_csv(
        _csv(
            "JOB-1,completed,2026-01-01T12:00:00,,",
            "JOB-2,completed,2026-01-01T12:00:00+02:00,,",
        ),
        CONFIG,
    )
    assert len(result.records) == 1
    assert len(result.quarantined) == 1
    assert result.quarantined[0].field_name == "opened_at"
    assert "JOB-1" not in str(result.quarantined)


def test_ingest_rejects_missing_completed_at_as_none_but_invalid_completed_at() -> None:
    result = ingest_csv(
        _csv(
            "JOB-1,in_progress,2026-01-01T12:00:00Z,,,,",
            "JOB-2,completed,2026-01-01T12:00:00Z,2026-01-02T12:00:00,,,,",
        ),
        CONFIG,
    )
    assert len(result.records) == 1
    assert result.records[0].completed_at is None
    assert len(result.quarantined) == 1
    assert result.quarantined[0].field_name == "completed_at"


def test_exact_duplicate_retains_first_and_reports_no_quarantine() -> None:
    row = "JOB-1,completed,2026-01-01T12:00:00Z,2026-01-02T12:00:00Z,12.30,USD,12.30,USD,,"
    result = ingest_csv(_csv(row, row), CONFIG)
    assert len(result.records) == 1
    assert result.exact_duplicates == 1
    assert result.quarantined == ()


def test_conflicting_records_quarantine_every_valid_record_for_id() -> None:
    result = ingest_csv(
        _csv(
            "JOB-1,completed,2026-01-01T12:00:00Z,,,",
            "JOB-1,cancelled,2026-01-01T12:00:00Z,,,",
        ),
        CONFIG,
    )
    assert result.records == ()
    assert len(result.quarantined) == 2
    assert all(
        diagnostic.error_code is IngestionErrorCode.RECORD_DUPLICATE_CONFLICT
        for diagnostic in result.quarantined
    )


def test_invalid_record_does_not_participate_in_conflict_resolution() -> None:
    result = ingest_csv(
        _csv(
            "JOB-1,completed,2026-01-01T12:00:00Z,,,",
            "JOB-1,unknown,2026-01-01T12:00:00Z,,,",
        ),
        CONFIG,
    )
    assert len(result.records) == 1
    assert len(result.quarantined) == 1
    assert result.quarantined[0].error_code is IngestionErrorCode.RECORD_FIELD_INVALID


def test_diagnostics_are_privacy_safe() -> None:
    result = ingest_csv(
        _csv("SECRET-JOB,unknown,not-a-time,SECRET-COMPLETED,,,,,"),
        CONFIG,
    )
    rendered = repr(result.quarantined)
    assert "SECRET-JOB" not in rendered
    assert "SECRET-COMPLETED" not in rendered
    assert "not-a-time" not in rendered


def test_unknown_columns_are_ignored() -> None:
    data = b"job_id,status,opened_at,customer_name\nJOB-1,completed,2026-01-01T12:00:00Z,Secret\n"
    result = ingest_csv(data, CONFIG)
    assert len(result.records) == 1
