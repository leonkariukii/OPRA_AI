"""Immutable findings and recommendation contracts."""

from dataclasses import dataclass
from enum import Enum

from opra.core.exceptions import ModelValidationError
from opra.models.comparisons import ComparisonResult


class EvidenceTier(str, Enum):
    """Evidence sufficiency categories; these are not statistical confidence levels."""

    LIMITED = "limited"
    MODERATE = "moderate"
    STRONG = "strong"


@dataclass(frozen=True, slots=True)
class Finding:
    """Deterministic threshold finding with metric-level evidence."""

    finding_id: str
    title: str
    priority_rank: int
    comparison: ComparisonResult
    evidence_tier: EvidenceTier
    limitation_codes: tuple[str, ...] = ()
    rule_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not isinstance(self.finding_id, str) or not self.finding_id:
            raise ModelValidationError("finding_id must be a non-empty string.")
        if not isinstance(self.title, str) or not self.title:
            raise ModelValidationError("title must be a non-empty string.")
        if isinstance(self.priority_rank, bool) or not isinstance(self.priority_rank, int) or self.priority_rank < 1:
            raise ModelValidationError("priority_rank must be a positive integer.")
        if not isinstance(self.comparison, ComparisonResult):
            raise ModelValidationError("comparison must be a ComparisonResult.")
        if not isinstance(self.evidence_tier, EvidenceTier):
            raise ModelValidationError("evidence_tier must be an EvidenceTier.")
        if not isinstance(self.limitation_codes, tuple):
            raise ModelValidationError("limitation_codes must be a tuple.")
        if tuple(sorted(set(self.limitation_codes))) != self.limitation_codes:
            raise ModelValidationError("limitation_codes must be unique and sorted.")
        if not isinstance(self.rule_version, str) or not self.rule_version:
            raise ModelValidationError("rule_version must be a non-empty string.")


@dataclass(frozen=True, slots=True)
class Recommendation:
    """Fixed recommendation linked to a finding."""

    recommendation_id: str
    finding_id: str
    priority_rank: int
    text: str
    limitation_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("recommendation_id", self.recommendation_id),
            ("finding_id", self.finding_id),
            ("text", self.text),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ModelValidationError(f"{name} must be a non-empty string.")
        if isinstance(self.priority_rank, bool) or not isinstance(self.priority_rank, int) or self.priority_rank < 1:
            raise ModelValidationError("priority_rank must be a positive integer.")
        if not isinstance(self.limitation_codes, tuple):
            raise ModelValidationError("limitation_codes must be a tuple.")
        if tuple(sorted(set(self.limitation_codes))) != self.limitation_codes:
            raise ModelValidationError("limitation_codes must be unique and sorted.")
