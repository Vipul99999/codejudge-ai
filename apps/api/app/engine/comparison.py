from __future__ import annotations

from app.contracts import (
    BaseEvaluationResultDTO,
    CodeArtifactDTO,
    CompareSolutionsRequestDTO,
    DetectedPattern,
    EvaluationType,
    Evidence,
    Finding,
    Probability,
    ScoreBreakdown,
    Severity,
)
from app.engine.bug_detection import detect_bug_risks
from app.engine.complexity import analyze_complexity_contract
from app.engine.primitives import build_result, checksum_text, stable_id, weighted_score
from app.engine.static_analysis import analyze_static


def compare_solutions_contract(request: CompareSolutionsRequestDTO) -> BaseEvaluationResultDTO:
    left_key = checksum_text(request.solution_a)
    right_key = checksum_text(request.solution_b)
    left_artifact = CodeArtifactDTO(language=request.language, source=request.solution_a)
    right_artifact = CodeArtifactDTO(language=request.language, source=request.solution_b)
    left_static = analyze_static(left_artifact)
    right_static = analyze_static(right_artifact)
    left_complexity = analyze_complexity_contract(left_artifact)
    right_complexity = analyze_complexity_contract(right_artifact)
    left_bugs = detect_bug_risks(left_artifact)
    right_bugs = detect_bug_risks(right_artifact)

    left_score = weighted_score(
        [
            (left_static.score, 0.45),
            (left_complexity.score, 0.3),
            (left_bugs.score, 0.25),
        ]
    )
    right_score = weighted_score(
        [
            (right_static.score, 0.45),
            (right_complexity.score, 0.3),
            (right_bugs.score, 0.25),
        ]
    )
    delta = round(left_score - right_score, 2)
    winner = "A" if delta > 2 else "B" if delta < -2 else "Tie"
    confidence = min(
        0.96,
        (
            left_static.confidence
            + right_static.confidence
            + left_complexity.confidence
            + right_complexity.confidence
        )
        / 4
        + min(0.12, abs(delta) / 100),
    )

    winner_evidence = Evidence(
        id=stable_id("ev", "compare.delta", left_key, right_key),
        kind="metric",
        message=f"Solution score delta A-B = {delta}.",
        rule_id="compare.delta",
        metric_name="score_delta",
        metric_value=delta,
    )
    evidence = [
        winner_evidence,
        *left_static.evidence[:8],
        *right_static.evidence[:8],
        *left_complexity.evidence[:4],
        *right_complexity.evidence[:4],
    ]
    patterns = [
        DetectedPattern(
            id=stable_id("pattern", "compare.winner", winner, delta),
            name=f"Winner: {winner}",
            category="comparison",
            confidence=round(confidence, 3),
            evidence_ids=[winner_evidence.id],
        )
    ]
    findings: list[Finding] = []
    if winner != "Tie":
        findings.append(
            Finding(
                id=stable_id("finding", "compare.winner", winner, delta),
                rule_id="compare.winner",
                title=f"Solution {winner} has the stronger deterministic profile",
                category="comparison",
                severity=Severity.info,
                probability=Probability.high if abs(delta) >= 10 else Probability.medium,
                score_impact=delta,
                confidence=round(confidence, 3),
                evidence_ids=[winner_evidence.id],
                why="Winner is derived from static quality, complexity, and bug-risk scores.",
                recommendation="Review the tradeoffs before treating a close score as decisive.",
            )
        )

    breakdown = [
        ScoreBreakdown(
            category="solution_a",
            score=left_score,
            weight=0.5,
            why="Weighted blend of solution A static quality, complexity, and bug-risk scores.",
            evidence_ids=[winner_evidence.id],
        ),
        ScoreBreakdown(
            category="solution_b",
            score=right_score,
            weight=0.5,
            why="Weighted blend of solution B static quality, complexity, and bug-risk scores.",
            evidence_ids=[winner_evidence.id],
        ),
    ]

    return build_result(
        evaluation_type=EvaluationType.solution_comparison,
        source_key=checksum_text(request.solution_a + "\n---\n" + request.solution_b),
        score=max(left_score, right_score) if winner != "Tie" else (left_score + right_score) / 2,
        confidence=confidence,
        evidence=evidence,
        limitations=[*left_static.limitations, *right_static.limitations],
        patterns=patterns,
        findings=findings,
        breakdown=breakdown,
        why=(
            f"Solution comparison chose {winner} from deterministic static, complexity, "
            "and bug-risk signals."
        ),
        rubric_version_id=request.rubric_version_id,
    )
