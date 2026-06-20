from __future__ import annotations

from time import perf_counter

from fastapi.testclient import TestClient

from app.contracts import (
    CodeArtifactDTO,
    CompareSolutionsRequestDTO,
    DatasetBuildRequestDTO,
    Difficulty,
    Language,
    PromptResponseArtifactDTO,
    ReasoningArtifactDTO,
)
from app.engine.bug_detection import detect_bug_risks
from app.engine.comparison import compare_solutions_contract
from app.engine.complexity import analyze_complexity_contract
from app.engine.dataset import build_dataset_contract
from app.engine.rubric import DEFAULT_CODE_REVIEW_RUBRIC, apply_rubric
from app.engine.static_analysis import analyze_static
from app.engine.test_generation import generate_test_plan
from app.engine.text_evaluation import evaluate_ai_response_contract, evaluate_reasoning_contract
from app.main import app

client = TestClient(app)


PYTHON_SAMPLE = """
def total_positive(values):
    if values is None:
        return 0
    total = 0
    for value in values:
        if value > 0:
            total += value
    return total
""".strip()


def assert_trust_layer(payload: dict[str, object]) -> None:
    assert isinstance(payload["score"], int | float)
    assert isinstance(payload["confidence"], int | float)
    assert payload["evidence"]
    assert payload["limitations"]
    assert "why" in payload and payload["why"]
    assert "detected_patterns" in payload
    assert "breakdown" in payload


def test_static_analysis_returns_contract_trust_layer() -> None:
    result = analyze_static(CodeArtifactDTO(language=Language.python, source=PYTHON_SAMPLE))

    assert result.evaluation_type.value == "code_review"
    assert result.score > 50
    assert result.evidence
    assert result.limitations
    assert {item.category for item in result.breakdown} >= {"correctness", "quality"}


def test_complexity_detects_nested_growth_with_evidence() -> None:
    source = "for i in range(n):\n    for j in range(n):\n        print(i, j)\n"
    result = analyze_complexity_contract(CodeArtifactDTO(language=Language.python, source=source))

    assert result.evaluation_type.value == "complexity"
    assert any(item.metric_value == "O(n^2)" for item in result.evidence)
    assert result.findings


def test_bug_detection_flags_boundary_with_rule_evidence() -> None:
    source = "for (let i = 0; i <= items.length; i++) console.log(items[i]);"
    result = detect_bug_risks(CodeArtifactDTO(language=Language.javascript, source=source))

    assert any(finding.category == "boundary" for finding in result.findings)
    assert result.score < 100
    assert result.evidence


def test_rubric_engine_reweights_static_result() -> None:
    base = analyze_static(CodeArtifactDTO(language=Language.python, source=PYTHON_SAMPLE))
    rubric_result = apply_rubric(base, DEFAULT_CODE_REVIEW_RUBRIC)

    assert rubric_result.evaluation_type.value == "rubric_score"
    assert rubric_result.rubric_version_id == DEFAULT_CODE_REVIEW_RUBRIC.id
    assert round(sum(item.weight for item in rubric_result.breakdown), 2) == 1


def test_dataset_engine_exports_json_csv_and_parquet_ready_payloads() -> None:
    result = build_dataset_contract(
        DatasetBuildRequestDTO(
            workspace_id="workspace-test",
            topic="Array evaluator benchmark",
            language=Language.python,
            count=3,
            difficulty=Difficulty.mixed,
            rubric_version_id=DEFAULT_CODE_REVIEW_RUBRIC.id,
            tags=["arrays"],
        )
    )

    assert len(result.items) == 3
    assert {"json", "csv", "parquet"} == {key.value for key in result.exports}
    assert result.result.evidence


def test_comparison_engine_is_deterministic_for_same_inputs() -> None:
    request = CompareSolutionsRequestDTO(
        workspace_id="workspace-test",
        language=Language.python,
        solution_a=PYTHON_SAMPLE,
        solution_b="def total_positive(values):\n    return sum(values)\n",
    )
    first = compare_solutions_contract(request)
    second = compare_solutions_contract(request)

    assert first.id == second.id
    assert first.score == second.score
    assert first.detected_patterns[0].name == second.detected_patterns[0].name


def test_test_generation_is_exportable_and_evidence_backed() -> None:
    result, exports = generate_test_plan(
        CodeArtifactDTO(language=Language.python, source=PYTHON_SAMPLE)
    )

    assert result.evaluation_type.value == "test_generation"
    assert "json" in exports
    assert "csv" in exports
    assert len(result.evidence) >= 7


def test_ai_response_and_reasoning_engines_are_contract_shaped() -> None:
    ai_result = evaluate_ai_response_contract(
        PromptResponseArtifactDTO(
            prompt="Write Python code and explain complexity for summing positives.",
            response=(
                "Because the code scans the list once, the complexity is O(n). "
                "```python\ndef f(values): return sum(v for v in values if v > 0)\n```"
            ),
            language=Language.python,
        )
    )
    reasoning_result = evaluate_reasoning_contract(
        ReasoningArtifactDTO(
            problem="Explain why the loop is correct.",
            reasoning=(
                "1. Assume input is a list. "
                "2. Because every item is checked, positives are added."
            ),
        )
    )

    assert ai_result.evidence
    assert reasoning_result.evidence
    assert ai_result.score > 60
    assert reasoning_result.score > 60


def test_contract_api_routes_record_benchmark_events() -> None:
    payload = {
        "workspace_id": "workspace-api",
        "evaluation_type": "code_review",
        "artifact": {"language": "python", "source": PYTHON_SAMPLE},
    }
    response = client.post("/api/analysis/code-review", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert_trust_layer(body)

    benchmark = client.get("/api/benchmarks", params={"workspace_id": "workspace-api"})
    assert benchmark.status_code == 200
    assert benchmark.json()["evaluation_count"] >= 1


def test_single_artifact_analysis_stays_under_500ms() -> None:
    artifact = CodeArtifactDTO(language=Language.python, source=PYTHON_SAMPLE * 30)

    started = perf_counter()
    result = analyze_static(artifact)
    elapsed_ms = (perf_counter() - started) * 1000

    assert result.evidence
    assert elapsed_ms < 500
