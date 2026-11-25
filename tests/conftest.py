"""Shared test fixtures.

Fixtures here must not import unimplemented domain modules. The CSV content is a
schema-neutral synthetic placeholder: the canonical CSV schema is an unresolved
decision in docs/DATA_AND_ANALYTICS.md and must not be invented here.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest


@pytest.fixture
def reference_utc_timestamp() -> datetime:
    """Fixed timezone-aware UTC reference time (2026-11-25T12:00:00Z)."""
    return datetime(2026, 11, 25, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_csv_text() -> str:
    """Schema-neutral synthetic UTF-8 CSV text."""
    return "column_a,column_b\nsynthetic-1,1\nsynthetic-2,2\n"


@pytest.fixture
def sample_csv_file(tmp_path: Path, sample_csv_text: str) -> Path:
    """Write the synthetic CSV text to a temporary UTF-8 file and return its path."""
    path = tmp_path / "sample.csv"
    path.write_text(sample_csv_text, encoding="utf-8")
    return path
