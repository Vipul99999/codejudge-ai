from __future__ import annotations

import re

from app.contracts import (
    BaseEvaluationResultDTO,
    CodeArtifactDTO,
    DetectedPattern,
    EvaluationType,
    Finding,
    Probability,
    ScoreBreakdown,
    Severity,
)
from app.engine.confidence import confidence_from_metrics, confidence_why
from app.engine.primitives import (
    base_limitations,
    build_result,
    checksum_text,
    clamp,
    collect_code_metrics,
    evidence_for_metrics,
    metric_evidence,
    stable_id,
)


def analyze_complexity_contract(artifact: CodeArtifactDTO) -> BaseEvaluationResultDTO:
    source = artifact.source
    metrics = collect_code_metrics(source, artifact.language)
    evidence = evidence_for_metrics(metrics)
    findings: list[Finding] = []
    patterns: list[DetectedPattern] = []

    nested_loop = bool(re.search(r"(for|while)[\s\S]{0,240}(for|while)", source))
    sort_call = bool(
        re.search(r"\.sort\(|sorted\(|Collections\.sort|Arrays\.sort|std::sort", source)
    )
    binary_halving = bool(
        re.search(r"(/=\s*2|//=\s*2|>>=\s*1|mid\s*=|binary)", source, re.IGNORECASE)
    )
    recursion = metrics.recursion_count > 0

    if nested_loop:
        growth = "O(n^2)"
        complexity_score = 52
        proof = "Nested iteration is visible, so quadratic growth is the conservative estimate."
    elif sort_call:
        growth = "O(n log n)"
        complexity_score = 68
        proof = "Sorting dominates the visible asymptotic behavior."
    elif binary_halving and metrics.loop_count:
        growth = "O(log n)"
        complexity_score = 91
        proof = "Loop logic appears to repeatedly halve the search space."
    elif metrics.loop_count or recursion:
        growth = "O(n)"
        complexity_score = 81
        proof = "Single-pass iteration or simple recursion is visible."
    else:
        growth = "O(1)"
        complexity_score = 95
        proof = "No input-sized loops, recursion, or sorting patterns were detected."

    allocation_growth = bool(
        re.search(r"new\s+\w+\[|malloc|calloc|\[\]|{}|dict\(|set\(|Map\(|List<|vector<", source)
    )
    space = "O(n)" if allocation_growth or recursion else "O(1)"
    memory_score = 72 if space == "O(n)" else 94

    growth_ev = metric_evidence("complexity.time", "time_complexity", growth)
    space_ev = metric_evidence("complexity.space", "space_complexity", space)
    evidence.extend([growth_ev, space_ev])
    patterns.append(
        DetectedPattern(
            id=stable_id("pattern", "complexity", growth, space),
            name=f"{growth} time / {space} space",
            category="scalability",
            confidence=0.86 if metrics.parse_ok else 0.62,
            evidence_ids=[growth_ev.id, space_ev.id],
        )
    )

    if nested_loop or metrics.cyclomatic_complexity >= 12:
        findings.append(
            Finding(
                id=stable_id(
                    "finding", "complexity.hot_path", growth, metrics.cyclomatic_complexity
                ),
                rule_id="complexity.hot_path",
                title="Potential scalability hot path",
                category="performance",
                severity=Severity.high if nested_loop else Severity.medium,
                probability=Probability.high if nested_loop else Probability.medium,
                score_impact=-max(10, 100 - complexity_score),
                confidence=0.83,
                evidence_ids=[growth_ev.id],
                why=proof,
                recommendation=(
                    "Reduce nested work, pre-index data, or document why input bounds are small."
                ),
            )
        )

    breakdown = [
        ScoreBreakdown(
            category="time_complexity",
            score=complexity_score,
            weight=0.42,
            why=proof,
            evidence_ids=[growth_ev.id],
        ),
        ScoreBreakdown(
            category="space_complexity",
            score=memory_score,
            weight=0.24,
            why=f"Space is estimated as {space} from allocation and recursion patterns.",
            evidence_ids=[space_ev.id],
        ),
        ScoreBreakdown(
            category="control_flow",
            score=clamp(96 - metrics.cyclomatic_complexity * 3 - metrics.nesting_depth * 4),
            weight=0.2,
            why="Derived from cyclomatic complexity and nesting depth.",
            evidence_ids=[
                item.id
                for item in evidence
                if "cyclomatic" in item.rule_id or "nesting" in item.rule_id
            ],
        ),
        ScoreBreakdown(
            category="scalability_confidence",
            score=clamp(
                82
                + (8 if metrics.parse_ok else -18)
                + (8 if nested_loop or sort_call or binary_halving else 0)
            ),
            weight=0.14,
            why="Confidence rises when visible structural patterns explain asymptotic behavior.",
            evidence_ids=[growth_ev.id, space_ev.id],
        ),
    ]
    limits = base_limitations(metrics)
    confidence, drivers, reducers = confidence_from_metrics(metrics, evidence, findings, limits)

    return build_result(
        evaluation_type=EvaluationType.complexity,
        source_key=checksum_text(source),
        score=sum(item.score * item.weight for item in breakdown),
        confidence=confidence,
        evidence=evidence,
        limitations=limits,
        patterns=patterns,
        findings=findings,
        breakdown=breakdown,
        why=f"{proof} {confidence_why(drivers, reducers)}",
    )
