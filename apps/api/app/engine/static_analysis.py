from __future__ import annotations

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
    find_line,
    line_span,
    metric_evidence,
    stable_id,
    weighted_score,
)


def analyze_static(
    artifact: CodeArtifactDTO, rubric_version_id: str | None = None
) -> BaseEvaluationResultDTO:
    metrics = collect_code_metrics(artifact.source, artifact.language)
    evidence = evidence_for_metrics(metrics)
    findings: list[Finding] = []
    patterns: list[DetectedPattern] = []

    readability = clamp(
        96
        - max(0, metrics.avg_line_length - 84) * 0.55
        - metrics.nesting_depth * 4.5
        - metrics.short_identifier_ratio * 22
    )
    quality = clamp(
        94
        - metrics.duplicate_lines * 4
        - metrics.long_functions * 12
        - max(0, metrics.cyclomatic_complexity - 8) * 3
    )
    maintainability = clamp(
        metrics.maintainability_index
        - metrics.duplicate_lines * 2
        - max(0, metrics.function_count - 12) * 1.5
    )
    clarity = clamp(88 + metrics.comment_density * 28 - metrics.short_identifier_ratio * 35)
    safety = clamp(72 + metrics.error_handling_count * 5 + metrics.guard_clause_count * 3)
    correctness_signal = clamp(
        62
        + metrics.guard_clause_count * 5
        + metrics.error_handling_count * 4
        - metrics.nesting_depth * 4
        - max(0, metrics.cyclomatic_complexity - 10) * 3
    )

    if metrics.duplicate_lines:
        evidence_item = metric_evidence(
            "static.duplication", "duplicate_lines", metrics.duplicate_lines
        )
        evidence.append(evidence_item)
        findings.append(
            Finding(
                id=stable_id("finding", "static.duplication", metrics.duplicate_lines),
                rule_id="static.duplication",
                title="Repeated implementation lines",
                category="maintainability",
                severity=Severity.medium,
                probability=Probability.high,
                score_impact=-min(25, metrics.duplicate_lines * 4),
                confidence=0.82,
                evidence_ids=[evidence_item.id],
                why="Duplicate normalized source lines increase maintenance drift risk.",
                recommendation="Extract repeated logic into a shared helper or data-driven branch.",
            )
        )

    if metrics.long_functions:
        evidence_item = metric_evidence(
            "static.long_function", "long_functions", metrics.long_functions
        )
        evidence.append(evidence_item)
        findings.append(
            Finding(
                id=stable_id("finding", "static.long_function", metrics.long_functions),
                rule_id="static.long_function",
                title="Large function body",
                category="maintainability",
                severity=Severity.medium,
                probability=Probability.medium,
                score_impact=-min(20, metrics.long_functions * 10),
                confidence=0.78,
                evidence_ids=[evidence_item.id],
                why="Long functions concentrate unrelated decisions and are harder to review.",
                recommendation=(
                    "Split large functions around validation, transformation, and output steps."
                ),
            )
        )

    if metrics.nesting_depth >= 4:
        evidence_item = metric_evidence(
            "static.deep_nesting", "nesting_depth", metrics.nesting_depth
        )
        evidence.append(evidence_item)
        findings.append(
            Finding(
                id=stable_id("finding", "static.deep_nesting", metrics.nesting_depth),
                rule_id="static.deep_nesting",
                title="Deep control-flow nesting",
                category="clarity",
                severity=Severity.medium,
                probability=Probability.medium,
                score_impact=-min(25, metrics.nesting_depth * 4),
                confidence=0.8,
                evidence_ids=[evidence_item.id],
                why="Nested branches increase the number of paths an evaluator must inspect.",
                recommendation="Prefer guard clauses, extracted predicates, or smaller functions.",
            )
        )

    if metrics.parse_error:
        findings.append(
            Finding(
                id=stable_id("finding", "static.parse_error", metrics.parse_error),
                rule_id="static.parse_error",
                title="Parser could not build a complete syntax tree",
                category="correctness",
                severity=Severity.critical,
                probability=Probability.high,
                score_impact=-35,
                confidence=0.94,
                evidence_ids=[],
                why=metrics.parse_error,
                recommendation="Fix syntax before trusting deeper static analysis.",
            )
        )

    for pattern_name, category, confidence, metric_name, metric_value in [
        (
            "Readable structure",
            "clarity",
            clarity / 100,
            "avg_line_length",
            round(metrics.avg_line_length, 2),
        ),
        (
            "Maintainability profile",
            "maintainability",
            maintainability / 100,
            "maintainability_index",
            round(metrics.maintainability_index, 2),
        ),
        (
            "Control-flow burden",
            "quality",
            max(0.1, 1 - metrics.cyclomatic_complexity / 30),
            "cyclomatic_complexity",
            metrics.cyclomatic_complexity,
        ),
    ]:
        ev = metric_evidence(f"static.pattern.{category}", metric_name, metric_value)
        evidence.append(ev)
        patterns.append(
            DetectedPattern(
                id=stable_id("pattern", pattern_name, metric_value),
                name=pattern_name,
                category=category,
                confidence=round(confidence, 3),
                evidence_ids=[ev.id],
            )
        )

    breakdown = [
        ScoreBreakdown(
            category="correctness",
            score=round(correctness_signal, 2),
            weight=0.22,
            why="Derived from visible guard clauses, error handling, nesting, and path count.",
            evidence_ids=[item.id for item in evidence if item.rule_id.startswith("metric.")][:4],
        ),
        ScoreBreakdown(
            category="quality",
            score=round(quality, 2),
            weight=0.22,
            why="Derived from duplication, function size, and cyclomatic complexity.",
            evidence_ids=[
                item.id
                for item in evidence
                if "cyclomatic" in item.rule_id or "duplication" in item.rule_id
            ],
        ),
        ScoreBreakdown(
            category="maintainability",
            score=round(maintainability, 2),
            weight=0.2,
            why=(
                "Derived from maintainability index, function count, duplication, "
                "and long functions."
            ),
            evidence_ids=[
                item.id
                for item in evidence
                if "maintainability" in item.rule_id or "functions" in item.rule_id
            ],
        ),
        ScoreBreakdown(
            category="clarity",
            score=round((readability + clarity) / 2, 2),
            weight=0.18,
            why="Derived from line length, naming quality, comments, and nesting.",
            evidence_ids=[
                item.id
                for item in evidence
                if "identifier" in item.rule_id or "nesting" in item.rule_id
            ],
        ),
        ScoreBreakdown(
            category="safety",
            score=round(safety, 2),
            weight=0.18,
            why="Derived from visible error handling and defensive guards.",
            evidence_ids=[
                item.id for item in evidence if item.rule_id in {"metric.lines", "metric.functions"}
            ],
        ),
    ]
    score = weighted_score((item.score, item.weight) for item in breakdown)

    limits = base_limitations(metrics)
    confidence, drivers, reducers = confidence_from_metrics(metrics, evidence, findings, limits)
    source_key = checksum_text(artifact.source)
    why = (
        "Static analysis score is a weighted blend of correctness, quality, maintainability, "
        "clarity, and safety metrics. " + confidence_why(drivers, reducers)
    )

    if line := find_line(r"\b(pass|TODO|FIXME)\b", artifact.source, flags=0):
        evidence.append(line_span(artifact.source, line, "static.incomplete_marker"))

    return build_result(
        evaluation_type=EvaluationType.code_review,
        source_key=source_key,
        score=score,
        confidence=confidence,
        evidence=evidence,
        limitations=limits,
        patterns=patterns,
        findings=findings,
        breakdown=breakdown,
        why=why,
        rubric_version_id=rubric_version_id,
    )
