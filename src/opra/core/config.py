"""Centralized, validated configuration for OPRA.AI.

``OpraConfig`` holds the operational limits; ``ConfigSnapshot`` is the immutable effective
configuration captured for one processing run. Both validate fail-fast and raise
:class:`~opra.core.exceptions.ConfigurationError` on invalid values; values are never
clamped, coerced or replaced with defaults.

This module intentionally does not read environment variables or files.
"""

from dataclasses import dataclass
from typing import Final

from opra.core.exceptions import ConfigurationError

DEFAULT_MAX_UPLOAD_BYTES: Final[int] = 10 * 1024 * 1024
DEFAULT_MAX_ROWS: Final[int] = 100_000
DEFAULT_MATURITY_BUFFER_DAYS: Final[int] = 3
DEFAULT_MIN_SAMPLE_SIZE: Final[int] = 10


def _require_int(name: str, value: object, *, minimum: int) -> None:
    """Require ``value`` to be a true ``int`` (not ``bool``) that is ``>= minimum``."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(f"{name} must be an integer, got {type(value).__name__}.")
    if value < minimum:
        raise ConfigurationError(f"{name} must be >= {minimum}, got {value}.")


def _validate_settings(
    *,
    max_upload_bytes: object,
    max_rows: object,
    maturity_buffer_days: object,
    min_sample_size: object,
) -> None:
    """Validate all four approved settings (``> 0`` means ``>= 1`` for integers)."""
    _require_int("max_upload_bytes", max_upload_bytes, minimum=1)
    _require_int("max_rows", max_rows, minimum=1)
    _require_int("maturity_buffer_days", maturity_buffer_days, minimum=0)
    _require_int("min_sample_size", min_sample_size, minimum=1)


@dataclass(frozen=True, slots=True)
class ConfigSnapshot:
    """Immutable effective configuration captured for one processing run.

    Constructing a snapshot validates every value, so an invalid snapshot cannot exist.
    """

    max_upload_bytes: int
    max_rows: int
    maturity_buffer_days: int
    min_sample_size: int

    def __post_init__(self) -> None:
        _validate_settings(
            max_upload_bytes=self.max_upload_bytes,
            max_rows=self.max_rows,
            maturity_buffer_days=self.maturity_buffer_days,
            min_sample_size=self.min_sample_size,
        )


@dataclass(frozen=True, slots=True)
class OpraConfig:
    """Validated operational limits with approved defaults.

    Attributes:
        max_upload_bytes: Maximum accepted upload size in bytes (``> 0``).
        max_rows: Maximum accepted number of data rows (``> 0``).
        maturity_buffer_days: Non-negative maturity buffer in days (``>= 0``).
        min_sample_size: Minimum sample size for confidence evaluation (``> 0``).
    """

    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES
    max_rows: int = DEFAULT_MAX_ROWS
    maturity_buffer_days: int = DEFAULT_MATURITY_BUFFER_DAYS
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE

    def __post_init__(self) -> None:
        _validate_settings(
            max_upload_bytes=self.max_upload_bytes,
            max_rows=self.max_rows,
            maturity_buffer_days=self.maturity_buffer_days,
            min_sample_size=self.min_sample_size,
        )

    def snapshot(self) -> ConfigSnapshot:
        """Return the immutable effective configuration for a processing run."""
        return ConfigSnapshot(
            max_upload_bytes=self.max_upload_bytes,
            max_rows=self.max_rows,
            maturity_buffer_days=self.maturity_buffer_days,
            min_sample_size=self.min_sample_size,
        )
