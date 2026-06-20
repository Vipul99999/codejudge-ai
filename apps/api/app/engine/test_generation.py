from __future__ import annotations

from app.contracts import (
    BaseEvaluationResultDTO,
    CodeArtifactDTO,
    DetectedPattern,
    EvaluationType,
    Evidence,
    Limitation,
    ScoreBreakdown,
)
from app.engine.primitives import (
    build_result,
    checksum_text,
    collect_code_metrics,
    serialize_csv,
    serialize_json,
    stable_id,
)


def generate_test_plan(artifact: CodeArtifactDTO) -> tuple[BaseEvaluationResultDTO, dict[str, str]]:
    metrics = collect_code_metrics(artifact.source, artifact.language)
    case_kinds = ["happy_path", "edge", "corner", "stress", "negative", "mutation", "property"]
    tests = []
    evidence: list[Evidence] = []
    for index, kind in enumerate(case_kinds, start=1):
        evidence_item = Evidence(
            id=stable_id(
                "ev", "test.case", kind, artifact.language.value, metrics.cyclomatic_complexity
            ),
            kind="metric",
            message=f"{kind} test generated from static complexity and boundary signals.",
            rule_id=f"test.{kind}",
            metric_name="cyclomatic_complexity",
            metric_value=metrics.cyclomatic_complexity,
        )
        evidence.append(evidence_item)
        tests.append(
            {
                "id": stable_id("test", kind, artifact.language.value, index),
                "kind": kind,
                "description": test_description(kind, metrics),
                "input": test_input(kind),
                "expected_behavior": test_expectation(kind),
                "evidence_ids": [evidence_item.id],
            }
        )

    score = min(100, 50 + len(tests) * 5 + min(20, metrics.guard_clause_count * 4))
    result = build_result(
        evaluation_type=EvaluationType.test_generation,
        source_key=checksum_text(artifact.source),
        score=score,
        confidence=0.78 if metrics.parse_ok else 0.58,
        evidence=evidence,
        limitations=[
            Limitation(
                id="lim-tests-static-only",
                scope="static_analysis",
                message=(
                    "Generated tests are static test ideas and are not executed against "
                    "submitted code."
                ),
            )
        ],
        patterns=[
            DetectedPattern(
                id=stable_id("pattern", "test.coverage", len(tests), metrics.cyclomatic_complexity),
                name="Static test coverage plan",
                category="test_generation",
                confidence=0.8,
                evidence_ids=[item.id for item in evidence],
            )
        ],
        findings=[],
        breakdown=[
            ScoreBreakdown(
                category="coverage_variety",
                score=100,
                weight=0.45,
                why=(
                    "Plan includes happy path, edge, corner, stress, negative, mutation, "
                    "and property checks."
                ),
                evidence_ids=[item.id for item in evidence],
            ),
            ScoreBreakdown(
                category="code_signal_alignment",
                score=score,
                weight=0.35,
                why="Coverage confidence rises with parse quality and visible guard complexity.",
                evidence_ids=[item.id for item in evidence],
            ),
            ScoreBreakdown(
                category="export_readiness",
                score=100,
                weight=0.2,
                why="Test plan is exportable as JSON and CSV.",
                evidence_ids=[item.id for item in evidence],
            ),
        ],
        why=(
            "Test generation uses deterministic templates selected from static complexity "
            "and boundary signals."
        ),
    )
    exports = {
        "json": serialize_json(tests),
        "csv": serialize_csv(
            [
                {
                    "id": test["id"],
                    "kind": test["kind"],
                    "description": test["description"],
                    "input": test["input"],
                    "expected_behavior": test["expected_behavior"],
                }
                for test in tests
            ]
        ),
    }
    return result, exports


def test_description(kind: str, metrics: object) -> str:
    return {
        "happy_path": "Representative valid input exercises the primary behavior.",
        "edge": "Minimum or empty input checks boundary handling.",
        "corner": "Single-item and repeated-value input checks off-by-one risks.",
        "stress": "Large input checks the estimated complexity path.",
        "negative": "Invalid or malformed input checks defensive handling.",
        "mutation": "Small behavioral mutation should change the expected result.",
        "property": "Invariant property should hold across a generated input family.",
    }[kind]


def test_input(kind: str) -> str:
    return {
        "happy_path": "representative valid input",
        "edge": "empty or minimum-sized input",
        "corner": "single item, duplicate item, and boundary value",
        "stress": "maximum documented input size",
        "negative": "null, malformed, or unsupported input",
        "mutation": "valid input with one changed branch-driving value",
        "property": "generated family preserving the same invariant",
    }[kind]


def test_expectation(kind: str) -> str:
    return {
        "happy_path": "returns the documented normal result",
        "edge": "handles the boundary without crash or out-of-range access",
        "corner": "preserves correctness at exact transition points",
        "stress": "preserves semantics within estimated complexity",
        "negative": "rejects or handles invalid input explicitly",
        "mutation": "test fails when the targeted behavior is changed",
        "property": "invariant remains true for the generated input family",
    }[kind]
