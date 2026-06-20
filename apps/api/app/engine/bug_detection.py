from __future__ import annotations

import re
from dataclasses import dataclass

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
    collect_code_metrics,
    evidence_for_metrics,
    find_line,
    line_span,
    metric_evidence,
    stable_id,
)


@dataclass(frozen=True)
class BugRule:
    id: str
    category: str
    title: str
    pattern: str
    severity: Severity
    probability: Probability
    impact: float
    why: str
    recommendation: str


BUG_RULES = [
    BugRule(
        id="bug.boundary.inclusive_length",
        category="boundary",
        title="Inclusive upper bound near length",
        pattern=r"<=\s*len\(|<=\s*\w+\.length|i\s*<=\s*n\b",
        severity=Severity.high,
        probability=Probability.high,
        impact=-18,
        why="Inclusive upper bounds near length-like values often read one item past the range.",
        recommendation="Use a strict upper bound or prove the inclusive endpoint is valid.",
    ),
    BugRule(
        id="bug.null.dereference",
        category="null_access",
        title="Dereference or indexing without visible guard",
        pattern=r"\w+\.\w+\(|\w+\[[^\]]+\]",
        severity=Severity.medium,
        probability=Probability.medium,
        impact=-10,
        why="The analyzer sees dereference/index operations but cannot prove a preceding guard.",
        recommendation="Add explicit null and range validation near the access.",
    ),
    BugRule(
        id="bug.recursion.base_case",
        category="bad_recursion",
        title="Recursive call requires base-case review",
        pattern=r"\breturn\s+\w+\(|\b\w+\([^)]*\)\s*$",
        severity=Severity.medium,
        probability=Probability.medium,
        impact=-12,
        why=(
            "Recursive-looking calls can overflow or fail to terminate if the base case "
            "is incomplete."
        ),
        recommendation="Verify every recursive path reaches a base case and shrinks the input.",
    ),
    BugRule(
        id="bug.loop.unbounded",
        category="blocking_operations",
        title="Unbounded loop",
        pattern=r"while\s+(true|1)|for\s*\(\s*;\s*;",
        severity=Severity.critical,
        probability=Probability.high,
        impact=-28,
        why="An unbounded loop can block analysis workers or user-facing code paths.",
        recommendation="Add a clear exit condition and maximum-iteration guard.",
    ),
    BugRule(
        id="bug.async.missing_await",
        category="async_mistake",
        title="Async flow needs await/error handling review",
        pattern=r"\basync\b(?![\s\S]{0,160}\bawait\b)|\.then\(",
        severity=Severity.medium,
        probability=Probability.medium,
        impact=-11,
        why="Async work without visible awaiting or rejection handling can complete out of order.",
        recommendation="Await async calls and handle rejected promises or exceptions.",
    ),
    BugRule(
        id="bug.resource.leak",
        category="resource_leak",
        title="Resource open without visible close/finally",
        pattern=r"\b(open\(|FileInputStream|new\s+File|fopen|socket\()",
        severity=Severity.high,
        probability=Probability.medium,
        impact=-17,
        why="Resource acquisition without visible close/finally can leak handles.",
        recommendation=(
            "Use context managers, try/finally, or deterministic close/dispose patterns."
        ),
    ),
    BugRule(
        id="bug.overflow.arithmetic",
        category="overflow_risk",
        title="Arithmetic may overflow fixed-width integers",
        pattern=r"\bint\s+\w+|Integer\b|long\s+\w+|\w+\s*\*\s*\w+",
        severity=Severity.medium,
        probability=Probability.low,
        impact=-7,
        why="Fixed-width integer arithmetic can overflow for large input values.",
        recommendation="Validate bounds or use wider numeric types where input size is unbounded.",
    ),
    BugRule(
        id="bug.race.shared_state",
        category="race_condition",
        title="Concurrent primitive with possible shared state",
        pattern=r"\bthread|asyncio|Promise\.all|setTimeout|setInterval|Future|CompletableFuture|mutex",
        severity=Severity.medium,
        probability=Probability.medium,
        impact=-13,
        why="Concurrent primitives can update shared state in nondeterministic order.",
        recommendation="Use synchronization, immutable state, or explicit await/join behavior.",
    ),
]


def detect_bug_risks(artifact: CodeArtifactDTO) -> BaseEvaluationResultDTO:
    metrics = collect_code_metrics(artifact.source, artifact.language)
    evidence = evidence_for_metrics(metrics)
    findings: list[Finding] = []
    patterns: list[DetectedPattern] = []

    for rule in BUG_RULES:
        if not re.search(rule.pattern, artifact.source, re.IGNORECASE | re.MULTILINE):
            continue
        line = find_line(rule.pattern, artifact.source)
        rule_evidence = line_span(artifact.source, line or 1, rule.id)
        evidence.append(rule_evidence)
        findings.append(
            Finding(
                id=stable_id("finding", rule.id, line or 0, artifact.language.value),
                rule_id=rule.id,
                title=rule.title,
                category=rule.category,
                severity=rule.severity,
                probability=rule.probability,
                score_impact=rule.impact,
                confidence=0.86 if line else 0.66,
                evidence_ids=[rule_evidence.id],
                why=rule.why,
                recommendation=rule.recommendation,
            )
        )
        patterns.append(
            DetectedPattern(
                id=stable_id("pattern", rule.category, line or 0),
                name=rule.title,
                category=rule.category,
                confidence=0.82 if line else 0.62,
                evidence_ids=[rule_evidence.id],
            )
        )

    if metrics.parse_error:
        parse_ev = metric_evidence("bug.parse_error", "parse_error", metrics.parse_error)
        evidence.append(parse_ev)
        findings.insert(
            0,
            Finding(
                id=stable_id("finding", "bug.parse_error", metrics.parse_error),
                rule_id="bug.parse_error",
                title="Malformed syntax limits bug detection",
                category="syntax",
                severity=Severity.critical,
                probability=Probability.high,
                score_impact=-35,
                confidence=0.95,
                evidence_ids=[parse_ev.id],
                why=metrics.parse_error,
                recommendation="Fix syntax before relying on deeper static bug analysis.",
            ),
        )

    severity_penalty = sum(abs(finding.score_impact) for finding in findings)
    score = max(0, 100 - severity_penalty)
    limits = base_limitations(metrics)
    confidence, drivers, reducers = confidence_from_metrics(metrics, evidence, findings, limits)
    breakdown = [
        ScoreBreakdown(
            category="bug_risk",
            score=score,
            weight=0.5,
            why="Derived from deterministic bug-rule severity and probability impacts.",
            evidence_ids=[eid for finding in findings for eid in finding.evidence_ids],
        ),
        ScoreBreakdown(
            category="parser_reliability",
            score=94 if metrics.parse_ok else 45,
            weight=0.2,
            why="Bug confidence depends on parser success and language support tier.",
            evidence_ids=[item.id for item in evidence if item.rule_id.startswith("metric.")],
        ),
        ScoreBreakdown(
            category="defensive_code",
            score=min(100, 60 + metrics.guard_clause_count * 7 + metrics.error_handling_count * 8),
            weight=0.3,
            why="Visible guard clauses and error handling reduce static bug risk.",
            evidence_ids=[item.id for item in evidence if item.rule_id == "metric.functions"],
        ),
    ]

    return build_result(
        evaluation_type=EvaluationType.bug_risk,
        source_key=checksum_text(artifact.source),
        score=sum(item.score * item.weight for item in breakdown),
        confidence=confidence,
        evidence=evidence,
        limitations=limits,
        patterns=patterns,
        findings=findings,
        breakdown=breakdown,
        why=(
            "Bug risk score subtracts deterministic rule impacts from the static profile. "
            f"{confidence_why(drivers, reducers)}"
        ),
    )
