"""Immutable report document for generic metric results."""

from dataclasses import dataclass
from datetime import UTC, datetime

from opra.core.config import ConfigSnapshot
from opra.core.exceptions import ModelValidationError
from opra.models.analytics import MetricResult


@dataclass(frozen=True, slots=True)
class ReportDocument:
    """Caller-timestamped report input; contains no KPI or recommendation logic."""

    generated_at_utc: datetime
    engine_version: str
    config: ConfigSnapshot
    metrics: tuple[MetricResult, ...]
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at_utc, datetime):
            raise ModelValidationError("generated_at_utc must be a datetime.")
        try:
            offset = self.generated_at_utc.utcoffset()
            normalized = self.generated_at_utc.astimezone(UTC) if offset is not None else None
        except (OverflowError, ValueError):
            raise ModelValidationError("generated_at_utc cannot be normalized to UTC.") from None
        if normalized is None:
            raise ModelValidationError("generated_at_utc must have an explicit UTC offset.")
        object.__setattr__(self, "generated_at_utc", normalized)
        if not isinstance(self.engine_version, str) or not self.engine_version.strip():
            raise ModelValidationError("engine_version must be a non-empty string.")
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise ModelValidationError("schema_version must be a non-empty string.")
        if not isinstance(self.config, ConfigSnapshot):
            raise ModelValidationError("config must be a ConfigSnapshot.")
        if not isinstance(self.metrics, tuple):
            raise ModelValidationError("metrics must be a tuple.")
        if any(not isinstance(metric, MetricResult) for metric in self.metrics):
            raise ModelValidationError("metrics must contain only MetricResult values.")
