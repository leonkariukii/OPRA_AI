from datetime import UTC, datetime
from decimal import Decimal

import pytest

from opra.core.config import OpraConfig
from opra.core.exceptions import ModelValidationError
from opra.ingestion.csv_loader import DatasetIngestionError, IngestionErrorCode, ingest_csv
from opra.models.records import JobRecord, JobStatus


def csv(*rows: str) -> bytes:
    headers = (
        "job_id,status,opened_at,completed_at,billed_amount,billed_currency,"
        "paid_amount,paid_currency,estimated_amount,estimated_currency"
    )
    padded: list[str] = []
    for row in rows:
        fields = row.split(",")
        if len(fields) < 10:
            fields.extend([""] * (10 - len(fields)))
        padded.append(",".join(fields[:10]))
    return (headers + "\n" + "\n".join(padded) + "\n").encode()


def test_record_is_frozen_and_normalizes_utc() -> None:
    record = JobRecord(
        " id ", JobStatus.COMPLETED, datetime.fromisoformat("2026-01-01T03:00:00+03:00")
    )
    assert record.opened_at == datetime(2026, 1, 1, tzinfo=UTC)
    assert record.job_id == " id "
    with pytest.raises((AttributeError, TypeError)):
        record.job_id = "x"  # type: ignore[misc]


def test_record_rejects_bad_decimal_and_unpaired_currency() -> None:
    stamp = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ModelValidationError):
        JobRecord("x", JobStatus.COMPLETED, stamp, billed_amount=1.0, billed_currency="USD")  # type: ignore[arg-type]
    with pytest.raises(ModelValidationError):
        JobRecord("x", JobStatus.COMPLETED, stamp, billed_currency="USD")


def test_csv_exact_and_conflicting_duplicates_and_invalid_isolated() -> None:
    result = ingest_csv(
        csv(
            "a,completed,2026-01-01T00:00:00Z,,1.230,USD",
            "a,completed,2025-12-31T19:00:00-05:00,,1.230,USD",
            "b,completed,2026-01-01T00:00:00Z,,1,USD",
            "b,cancelled,2026-01-01T00:00:00Z,,1,USD",
            "bad,wrong,not-a-time,,,",
        ),
        OpraConfig(),
    )
    assert [r.job_id for r in result.records] == ["a"]
    assert result.exact_duplicates == 1
    assert [d.error_code for d in result.quarantined].count(
        IngestionErrorCode.RECORD_DUPLICATE_CONFLICT
    ) == 2
    assert result.records[0].billed_amount == Decimal("1.230")
    assert result.records[0].opened_at.tzinfo == UTC


def test_dataset_level_rejections() -> None:
    config = OpraConfig(max_upload_bytes=1000, max_rows=1)
    with pytest.raises(DatasetIngestionError) as error:
        ingest_csv(b"\xff", config)
    assert error.value.code == IngestionErrorCode.DATASET_ENCODING_INVALID
    with pytest.raises(DatasetIngestionError) as error:
        ingest_csv(
            b"job_id,status,opened_at\na,completed,2026-01-01T00:00:00Z\nb,completed,2026-01-01T00:00:00Z",
            config,
        )
    assert error.value.code == IngestionErrorCode.DATASET_LIMIT_EXCEEDED
    with pytest.raises(DatasetIngestionError) as error:
        ingest_csv(b"job_id,job_id,status,opened_at\n", config)
    assert error.value.code == IngestionErrorCode.DATASET_STRUCTURE_INVALID


def test_timestamp_currency_and_diagnostics_are_safe() -> None:
    result = ingest_csv(csv("secret-id,completed,2026-01-01T00:00:00,,7,ZZZ"), OpraConfig())
    assert not result.records
    diagnostic = result.quarantined[0]
    assert diagnostic.error_code == IngestionErrorCode.RECORD_FIELD_INVALID
    assert "secret-id" not in repr(diagnostic)
    assert "7" not in repr(diagnostic)


def test_missing_completed_time_is_none_and_bad_offset_quarantined() -> None:
    result = ingest_csv(
        csv("a,in_progress,2026-01-01T00:00:00Z,,,,", "b,completed,2026-01-01T00:00:00,,,,"),
        OpraConfig(),
    )
    assert len(result.records) == 1 and result.records[0].completed_at is None
    assert len(result.quarantined) == 1
