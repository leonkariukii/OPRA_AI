"""Immutable domain models shared across pipeline stages."""

from opra.models.records import (
    CanonicalStatus,
    JobRecord,
    JobStatus,
    RawJobRecord,
)

__all__ = [
    "CanonicalStatus",
    "JobRecord",
    "JobStatus",
    "RawJobRecord",
]
