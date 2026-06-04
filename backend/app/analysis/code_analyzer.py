from __future__ import annotations

from app.analysis.common import LIMITATIONS, category, clamp, collect_signals, confidence_from_signals, safe_average
from app.models import CodeAnalysisResponse, CodeRequest


def analyze_code(request: CodeRequest) -> CodeAnalysisResponse:
    signals = collect_signals(request.code, request.language)
    comment_ratio = signals.comment_lines / max(signals.non_empty_lines, 1)
    identifier_lengths = [len(item) for item in signals.identifiers]
    short_names = sum(1 for item in signals.identifiers if len(item) <= 2)
    short_name_ratio = short_names / max(len(identifier_lengths), 1)

    readability = clamp(
        92 - max(0, signals.avg_line_length - 80) * 0.45 - signals.nesting_depth * 5 - short_name_ratio * 18
    )
    maintainability = clamp(
        88 - signals.long_functions * 12 - signals.duplicate_lines * 4 - max(0, signals.function_count - 12) * 2
    )
    complexity = clamp(94 - signals.loop_count * 6 - signals.branch_count * 4 - signals.nesting_depth * 7)
    naming = clamp(90 - short_name_ratio * 36 - max(0, 0.05 - comment_ratio) * 70)
    smells = clamp(94 - signals.duplicate_lines * 7 - signals.long_functions * 15 - (0 if signals.parse_ok else 25))
    edge_case = clamp(
        50
        + request.code.lower().count("empty") * 8
        + request.code.lower().count("null") * 5
        + request.code.lower().count("none") * 5
        + request.code.lower().count("boundary") * 8
    )

    categories = [
        category("Readability", readability, "Based on line length, nesting, and identifier clarity."),
        category(
            "Maintainability", maintainability, "Penalizes duplication, long functions, and overly broad modules."
        ),
        category("Complexity", complexity, "Estimates control-flow burden from loops, branches, and nesting."),
        category("Naming Quality", naming, "Looks for descriptive identifiers and useful local documentation signals."),
        category("Code Smells", smells, "Flags duplication, parse failures, and large function bodies."),
        category(
            "Edge Case Coverage", edge_case, "Checks whether boundary and empty-input handling is visible in code."
        ),
    ]
    overall = safe_average(score.score for score in categories)

    suggestions: list[str] = []
    risk_summary: list[str] = []
    if signals.max_line_length > 120:
        suggestions.append("Break very long lines into named intermediate values or helper functions.")
    if signals.nesting_depth >= 4:
        suggestions.append("Reduce nested control flow with guard clauses or smaller functions.")
        risk_summary.append("Deep nesting increases the chance of missed branches.")
    if signals.duplicate_lines:
        suggestions.append("Extract repeated logic into shared helpers or data-driven branches.")
        risk_summary.append("Duplicate logic can drift when only one copy is fixed.")
    if edge_case < 65:
        suggestions.append("Add explicit handling for empty inputs, null values, boundaries, and invalid states.")
        risk_summary.append("Edge-case intent is not clearly represented in the submitted code.")
    if not signals.parse_ok and signals.parse_error:
        risk_summary.append(signals.parse_error)
    if not suggestions:
        suggestions.append("The submission has a clean static profile; focus next on runtime tests and peer review.")

    confidence, reason, _ = confidence_from_signals(signals, request.language)
    return CodeAnalysisResponse(
        overall_score=overall,
        category_scores=categories,
        suggestions=suggestions,
        risk_summary=risk_summary or ["No critical static risks detected."],
        confidence=confidence,
        reason=reason,
        limitations=LIMITATIONS,
        signals=signals.__dict__,
    )
