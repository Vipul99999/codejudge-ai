from app.analysis.bug_detector import detect_bugs
from app.analysis.code_analyzer import analyze_code
from app.analysis.complexity import analyze_complexity
from app.analysis.rubric import score_rubric
from app.models import CodeRequest, Language, RubricCategory, RubricRequest


def test_code_analyzer_scores_python_code() -> None:
    response = analyze_code(CodeRequest(language=Language.python, code="def add(nums):\n    return sum(nums)\n"))
    assert response.overall_score > 60
    assert response.confidence.value in {"High", "Medium", "Low"}


def test_bug_detector_flags_inclusive_boundary() -> None:
    response = detect_bugs(
        CodeRequest(language=Language.javascript, code="for (let i = 0; i <= items.length; i++) console.log(items[i]);")
    )
    assert any(finding.category == "Boundary issue" for finding in response.findings)


def test_complexity_detects_nested_loop() -> None:
    code = "for i in range(n):\n    for j in range(n):\n        print(i, j)\n"
    response = analyze_complexity(CodeRequest(language=Language.python, code=code))
    assert response.time_complexity == "O(n^2)"


def test_rubric_normalizes_weights() -> None:
    response = score_rubric(
        RubricRequest(
            categories=[
                RubricCategory(name="correctness", weight=2, score=80),
                RubricCategory(name="clarity", weight=1, score=50),
            ]
        )
    )
    assert round(sum(item.weight for item in response.normalized_categories), 2) == 1
    assert response.weighted_score > 0
