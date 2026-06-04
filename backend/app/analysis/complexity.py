from __future__ import annotations

import re

from app.analysis.common import LIMITATIONS, collect_signals, confidence_from_signals
from app.models import CodeRequest, ComplexityResponse


def analyze_complexity(request: CodeRequest) -> ComplexityResponse:
    code = request.code
    signals = collect_signals(code, request.language)
    nested_loop = bool(re.search(r"(for|while)[\s\S]{0,220}(for|while)", code))
    sort_call = bool(re.search(r"\.sort\(|sorted\(|Collections\.sort|Arrays\.sort|std::sort", code))
    binary_halving = bool(re.search(r"(/=\s*2|//=\s*2|>>=\s*1|mid\s*=|binary)", code, flags=re.IGNORECASE))
    recursion = bool(re.search(r"\bdef\s+(\w+)[\s\S]*\1\(|function\s+(\w+)[\s\S]*\2\(", code))

    if nested_loop:
        time = "O(n^2)"
        explanation = "Nested iteration is visible, so quadratic growth is the safest estimate."
    elif sort_call:
        time = "O(n log n)"
        explanation = "A sorting routine dominates typical runtime behavior."
    elif binary_halving and signals.loop_count:
        time = "O(log n)"
        explanation = "Loop logic appears to repeatedly halve the search space."
    elif signals.loop_count or recursion:
        time = "O(n)"
        explanation = "Single-pass iteration or simple recursion is visible."
    else:
        time = "O(1)"
        explanation = "No input-sized loops, recursion, or sorting patterns were detected."

    if re.search(r"new\s+\w+\[|malloc|calloc|\[\]|{}|dict\(|set\(|Map\(|List<|vector<", code):
        space = "O(n)"
    elif recursion:
        space = "O(n)"
    else:
        space = "O(1)"

    confidence, reason, confidence_score = confidence_from_signals(signals, request.language)
    if nested_loop or sort_call or binary_halving:
        confidence_score = min(92, confidence_score + 8)

    return ComplexityResponse(
        time_complexity=time,
        space_complexity=space,
        explanation=f"{explanation} Space is estimated as {space} from allocation and recursion patterns.",
        confidence_score=confidence_score,
        confidence=confidence,
        reason=reason,
        limitations=LIMITATIONS,
    )
