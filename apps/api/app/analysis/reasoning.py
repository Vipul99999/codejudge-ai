from __future__ import annotations

import re

from app.analysis.common import LIMITATIONS, clamp
from app.models import Confidence, ReasoningRequest, ReasoningResponse


def review_reasoning(request: ReasoningRequest) -> ReasoningResponse:
    text = request.reasoning
    lower = text.lower()
    steps = len(re.findall(r"(^|\n)\s*(step\s*)?\d+[\).:-]", text, flags=re.IGNORECASE))
    connectors = sum(
        lower.count(word)
        for word in ["because", "therefore", "so", "however", "assume", "if", "then"]
    )
    contradictions = []
    if "always" in lower and "except" in lower:
        contradictions.append(
            "Uses absolute language and an exception in the same reasoning chain."
        )
    if "must" in lower and "might" in lower:
        contradictions.append(
            "Mixes certainty with uncertainty without explaining the condition change."
        )
    missing = []
    if "input" not in lower:
        missing.append("Input constraints are not stated.")
    if "edge" not in lower and "boundary" not in lower:
        missing.append("Boundary or edge cases are not discussed.")
    if "complexity" not in lower and "runtime" not in lower:
        missing.append("Runtime or complexity assumptions are not discussed.")

    score = clamp(
        52
        + min(steps, 6) * 5
        + min(connectors, 10) * 3
        - len(contradictions) * 15
        - len(missing) * 7
    )
    feedback = [
        f"Detected {steps} explicit step marker(s) and {connectors} logical connector(s).",
        "Reasoning is strongest when each conclusion links to a constraint, example, or invariant.",
    ]
    if score < 70:
        feedback.append(
            "Add a clearer assumption-to-conclusion chain and test it against counterexamples."
        )

    return ReasoningResponse(
        score=score,
        feedback=feedback,
        missing_assumptions=missing
        or ["No major missing assumption detected by heuristic review."],
        contradictions=contradictions or ["No direct contradiction pattern detected."],
        confidence=Confidence.medium,
        reason="Heuristic estimate from reasoning structure and contradiction patterns",
        limitations=LIMITATIONS,
    )
