from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.contracts import (
    BaseEvaluationResultDTO,
    EvaluationType,
    Evidence,
    Limitation,
    RubricCriterion,
    RubricVersionEntity,
)


def test_evaluation_result_requires_trust_layer_fields() -> None:
    result = BaseEvaluationResultDTO(
        id="eval-1",
        evaluation_type=EvaluationType.code_review,
        score=84,
        confidence=0.72,
        evidence=[
            Evidence(
                id="evidence-1",
                kind="metric",
                message="Cyclomatic complexity is 2.",
                rule_id="complexity.cyclomatic",
                metric_name="cyclomatic_complexity",
                metric_value=2,
            )
        ],
        limitations=[
            Limitation(
                id="limitation-1",
                scope="static_analysis",
                message="Static analysis cannot prove runtime correctness.",
            )
        ],
        detected_patterns=[],
        findings=[],
        breakdown=[],
        why="Score is derived from parser-backed metrics and rule evidence.",
        engine_version="0.1.0",
        created_at=datetime(2026, 6, 5, tzinfo=UTC),
    )

    assert result.evidence
    assert result.limitations
    assert result.why.startswith("Score is derived")


def test_score_and_confidence_bounds_are_enforced() -> None:
    with pytest.raises(ValidationError):
        BaseEvaluationResultDTO(
            id="eval-invalid",
            evaluation_type=EvaluationType.code_review,
            score=101,
            confidence=1.4,
            evidence=[],
            limitations=[],
            detected_patterns=[],
            findings=[],
            breakdown=[],
            why="Invalid bounds should be rejected.",
            engine_version="0.1.0",
            created_at=datetime(2026, 6, 5, tzinfo=UTC),
        )


def test_rubric_version_freezes_weighted_criteria() -> None:
    rubric = RubricVersionEntity(
        id="rubric-version-1",
        rubric_id="rubric-1",
        version=1,
        name="Baseline code review",
        checksum="0123456789abcdef0123456789abcdef",
        created_at=datetime(2026, 6, 5, tzinfo=UTC),
        criteria=[
            RubricCriterion(
                id="maintainability",
                name="Maintainability",
                description="Readable, cohesive, and low-risk implementation structure.",
                weight=1,
                minimum_evidence=1,
            )
        ],
    )

    assert rubric.criteria[0].id == "maintainability"
