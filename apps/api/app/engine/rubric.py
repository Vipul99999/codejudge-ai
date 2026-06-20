from __future__ import annotations

from datetime import UTC, datetime

from app.contracts import (
    BaseEvaluationResultDTO,
    DetectedPattern,
    EvaluationType,
    Evidence,
    Limitation,
    RubricCriterion,
    RubricVersionEntity,
    ScoreBreakdown,
)
from app.engine.primitives import build_result, checksum_text, stable_id, weighted_score

DEFAULT_CODE_REVIEW_RUBRIC = RubricVersionEntity(
    id="rubric-version-code-review-default",
    rubric_id="rubric-code-review",
    version=1,
    name="CodeJudge baseline code review",
    checksum="8dd3a3e87dcbca79d20ebc8a73585754d3bc4ff4d1866f9d46c972f9eb6ca773",
    created_at=datetime(2026, 6, 5, tzinfo=UTC),
    criteria=[
        RubricCriterion(
            id="correctness",
            name="Correctness",
            description="Visible evidence of boundary handling and coherent control flow.",
            weight=0.22,
            minimum_evidence=1,
        ),
        RubricCriterion(
            id="quality",
            name="Quality",
            description="Low duplication, low needless complexity, and clear implementation shape.",
            weight=0.22,
            minimum_evidence=1,
        ),
        RubricCriterion(
            id="maintainability",
            name="Maintainability",
            description="Small cohesive units with stable naming and maintainable structure.",
            weight=0.2,
            minimum_evidence=1,
        ),
        RubricCriterion(
            id="clarity",
            name="Clarity",
            description="Readable names, understandable line shape, and inspectable decisions.",
            weight=0.18,
            minimum_evidence=1,
        ),
        RubricCriterion(
            id="safety",
            name="Safety",
            description="Visible guards, error handling, and absence of high-risk patterns.",
            weight=0.18,
            minimum_evidence=1,
        ),
    ],
)


def normalize_rubric(rubric: RubricVersionEntity) -> RubricVersionEntity:
    total = sum(criterion.weight for criterion in rubric.criteria)
    if total <= 0:
        equal = 1 / len(rubric.criteria)
        criteria = [criterion.model_copy(update={"weight": equal}) for criterion in rubric.criteria]
    else:
        criteria = [
            criterion.model_copy(update={"weight": round(criterion.weight / total, 6)})
            for criterion in rubric.criteria
        ]
    return rubric.model_copy(update={"criteria": criteria})


def apply_rubric(
    result: BaseEvaluationResultDTO,
    rubric: RubricVersionEntity = DEFAULT_CODE_REVIEW_RUBRIC,
) -> BaseEvaluationResultDTO:
    normalized = normalize_rubric(rubric)
    breakdown_by_category = {item.category.lower(): item for item in result.breakdown}
    evidence = list(result.evidence)
    limitations = list(result.limitations)
    findings = list(result.findings)
    patterns = list(result.detected_patterns)
    scored_breakdown: list[ScoreBreakdown] = []

    for criterion in normalized.criteria:
        existing = breakdown_by_category.get(criterion.id.lower()) or breakdown_by_category.get(
            criterion.name.lower()
        )
        if existing is None:
            evidence_item = Evidence(
                id=stable_id("ev", "rubric.missing_criterion", criterion.id, result.id),
                kind="rubric_match",
                message=f"Rubric criterion '{criterion.name}' had no direct engine category.",
                rule_id="rubric.missing_criterion",
            )
            evidence.append(evidence_item)
            score = max(0.0, result.score - 12)
            evidence_ids = [evidence_item.id]
            why = (
                f"No direct engine category matched criterion '{criterion.name}', "
                "so the overall score was used with a coverage penalty."
            )
        else:
            evidence_ids = existing.evidence_ids
            score = existing.score
            why = f"Criterion '{criterion.name}' maps to engine category '{existing.category}'."

        if len(evidence_ids) < criterion.minimum_evidence:
            score = max(0.0, score - 8)
            why += " Minimum evidence requirement was not fully met."

        scored_breakdown.append(
            ScoreBreakdown(
                category=criterion.id,
                score=round(score, 2),
                weight=criterion.weight,
                why=why,
                evidence_ids=evidence_ids,
            )
        )

    score = weighted_score((item.score, item.weight) for item in scored_breakdown)
    rubric_evidence = Evidence(
        id=stable_id("ev", "rubric.version", normalized.id, normalized.checksum),
        kind="rubric_match",
        message=f"Applied rubric '{normalized.name}' version {normalized.version}.",
        rule_id="rubric.version",
        metric_name="rubric_checksum",
        metric_value=normalized.checksum,
    )
    evidence.append(rubric_evidence)
    patterns.append(
        DetectedPattern(
            id=stable_id("pattern", "rubric.coverage", normalized.id, len(scored_breakdown)),
            name="Rubric-weighted evaluation",
            category="rubric",
            confidence=min(0.98, result.confidence + 0.04),
            evidence_ids=[rubric_evidence.id],
        )
    )
    limitations.append(
        Limitation(
            id=stable_id("lim", "rubric.static", normalized.id),
            scope="rubric",
            message=(
                "Rubric scoring reweights deterministic engine evidence; "
                "it does not add runtime execution."
            ),
        )
    )

    return build_result(
        evaluation_type=EvaluationType.rubric_score,
        source_key=checksum_text(result.model_dump_json() + normalized.model_dump_json()),
        score=score,
        confidence=max(0.0, min(1.0, result.confidence + 0.02)),
        evidence=evidence,
        limitations=limitations,
        patterns=patterns,
        findings=findings,
        breakdown=scored_breakdown,
        why=(
            f"Rubric score applies normalized criterion weights from '{normalized.name}' "
            "to deterministic engine category scores and evidence coverage."
        ),
        rubric_version_id=normalized.id,
    )
