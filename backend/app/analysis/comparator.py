from __future__ import annotations

from app.analysis.code_analyzer import analyze_code
from app.analysis.common import LIMITATIONS, category, collect_signals, confidence_from_signals, safe_average
from app.analysis.complexity import analyze_complexity
from app.models import CodeRequest, CompareRequest, ComparisonResponse


def compare_solutions(request: CompareRequest) -> ComparisonResponse:
    analysis_a = analyze_code(CodeRequest(language=request.language, code=request.solution_a))
    analysis_b = analyze_code(CodeRequest(language=request.language, code=request.solution_b))
    complexity_a = analyze_complexity(CodeRequest(language=request.language, code=request.solution_a))
    complexity_b = analyze_complexity(CodeRequest(language=request.language, code=request.solution_b))

    complexity_rank = {"O(1)": 100, "O(log n)": 92, "O(n)": 82, "O(n log n)": 74, "O(n^2)": 58}
    efficiency_a = complexity_rank.get(complexity_a.time_complexity, 60)
    efficiency_b = complexity_rank.get(complexity_b.time_complexity, 60)

    a = safe_average([analysis_a.overall_score, efficiency_a])
    b = safe_average([analysis_b.overall_score, efficiency_b])
    winner = "Tie" if abs(a - b) <= 3 else ("A" if a > b else "B")
    breakdown = [
        category(
            "Correctness Confidence",
            safe_average([analysis_a.category_scores[-1].score, analysis_b.category_scores[-1].score]),
            "Uses edge-case handling signals across both submissions.",
        ),
        category(
            "Readability",
            safe_average([analysis_a.category_scores[0].score, analysis_b.category_scores[0].score]),
            "Compares line length, nesting, and naming clarity.",
        ),
        category(
            "Efficiency",
            safe_average([efficiency_a, efficiency_b]),
            f"A: {complexity_a.time_complexity}; B: {complexity_b.time_complexity}.",
        ),
        category(
            "Maintainability",
            safe_average([analysis_a.category_scores[1].score, analysis_b.category_scores[1].score]),
            "Compares duplication and function shape.",
        ),
        category("Scalability", safe_average([efficiency_a, efficiency_b]), "Based on estimated asymptotic growth."),
    ]
    signals = collect_signals(request.solution_a + "\n" + request.solution_b, request.language)
    confidence, reason, _ = confidence_from_signals(signals, request.language)
    reason_summary = (
        "Scores are close; neither solution is a clear deterministic winner."
        if winner == "Tie"
        else f"Solution {winner} has the stronger combined quality and efficiency profile."
    )
    return ComparisonResponse(
        winner=winner,
        reason_summary=reason_summary,
        score_breakdown=breakdown,
        solution_a_score=a,
        solution_b_score=b,
        confidence=confidence,
        reason=reason,
        limitations=LIMITATIONS,
    )
