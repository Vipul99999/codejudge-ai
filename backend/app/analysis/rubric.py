from __future__ import annotations

from app.analysis.common import LIMITATIONS
from app.models import Confidence, RubricRequest, RubricResponse


def score_rubric(request: RubricRequest) -> RubricResponse:
    total_weight = sum(item.weight for item in request.categories)
    normalized = []
    weighted = 0.0
    for item in request.categories:
        weight = item.weight / total_weight if total_weight else 1 / len(request.categories)
        normalized_item = item.model_copy(update={"weight": round(weight, 4)})
        normalized.append(normalized_item)
        weighted += normalized_item.score * normalized_item.weight

    if weighted >= 85:
        interpretation = "Excellent evaluation result with only targeted review needed."
    elif weighted >= 70:
        interpretation = "Solid result with visible improvement opportunities."
    elif weighted >= 50:
        interpretation = "Mixed result requiring focused remediation."
    else:
        interpretation = "High-risk result requiring substantial review."

    return RubricResponse(
        weighted_score=round(weighted, 2),
        normalized_categories=normalized,
        interpretation=interpretation,
        confidence=Confidence.high,
        reason="Weighted deterministic rubric calculation",
        limitations=LIMITATIONS,
    )
