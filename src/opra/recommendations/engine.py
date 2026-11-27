"""Fixed recommendation mapping for approved deterministic findings."""

from opra.models.intelligence import Finding, Recommendation

TEXT = {
    "F-001": "Review period scheduling capacity and the open-work queue; compare workflow categories before changing staffing or appointment policy.",
    "F-002": "Review cancellation recording and the workshop's cancellation-reason records for the affected period.",
    "F-003": "Map the service process and inspect waiting stages for completed jobs in the affected period.",
    "F-004": "Check billed-amount completeness and billing-data capture for the affected currency and period.",
}


def recommend(findings: tuple[Finding, ...]) -> tuple[Recommendation, ...]:
    return tuple(
        Recommendation(
            f"R-{finding.finding_id[2:]}",
            finding.finding_id,
            finding.priority_rank,
            TEXT[finding.finding_id],
            finding.limitation_codes,
        )
        for finding in sorted(findings, key=lambda item: (item.priority_rank, item.finding_id))
    )
