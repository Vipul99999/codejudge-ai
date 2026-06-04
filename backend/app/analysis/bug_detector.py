from __future__ import annotations

import re

from app.analysis.common import LIMITATIONS, collect_signals, confidence_from_signals, line_number_for_pattern
from app.models import BugDetectorResponse, CodeRequest, Finding

BUG_PATTERNS: list[tuple[str, str, str, str, str, str]] = [
    (
        "Null safety",
        "high",
        r"\.(\w+)\(|\[\w+\]",
        "Potential dereference or index access without an obvious guard.",
        "Can crash when values are null, undefined, None, or out of range.",
        "Add explicit validation before dereferencing or indexing.",
    ),
    (
        "Boundary issue",
        "medium",
        r"<=\s*len\(|<=\s*\w+\.length|i\s*<=\s*n",
        "Inclusive upper bound detected near length-like value.",
        "May read one element past the valid range.",
        "Use a strict upper bound or document why the inclusive bound is valid.",
    ),
    (
        "Off-by-one",
        "medium",
        r"range\([^,\)]*\+1\)|for\s*\([^;]+<=\s*",
        "Loop boundary may include one extra iteration.",
        "Can produce incorrect totals or out-of-bounds access.",
        "Validate loop start and end with minimum, maximum, and single-item cases.",
    ),
    (
        "Recursion risk",
        "medium",
        r"\breturn\s+\w+\(|\b\w+\([^)]*\)\s*;?\s*$",
        "Recursive-looking call detected.",
        "May overflow the stack if the base case is incomplete.",
        "Ensure every recursive path reaches a base case and consider iterative alternatives.",
    ),
    (
        "Infinite loop",
        "high",
        r"while\s+(true|1)|for\s*\(\s*;\s*;",
        "Unbounded loop detected.",
        "Can hang workers or user interfaces.",
        "Add a clear exit condition and maximum iteration guard.",
    ),
    (
        "Race condition",
        "medium",
        r"\bthread|asyncio|Promise\.all|setTimeout|setInterval|Future|CompletableFuture|mutex",
        "Concurrent or asynchronous primitive detected.",
        "Shared state may update in nondeterministic order.",
        "Use synchronization, immutable state, or explicit await/join behavior.",
    ),
    (
        "Memory risk",
        "medium",
        r"new\s+\w+\[|malloc|calloc|append\(|push\(|while\s+",
        "Allocation or repeated growth detected.",
        "Large inputs may grow memory unexpectedly.",
        "Bound collection growth and stream data where practical.",
    ),
    (
        "Async mistake",
        "medium",
        r"\basync\b(?![\s\S]{0,120}\bawait\b)|\.then\(",
        "Async flow may be missing awaits or error handling.",
        "Failures can be swallowed or work can complete out of order.",
        "Await async calls and handle rejected promises/exceptions.",
    ),
]


def detect_bugs(request: CodeRequest) -> BugDetectorResponse:
    code = request.code
    findings: list[Finding] = []
    for category, severity, pattern, explanation, impact, fix in BUG_PATTERNS:
        if re.search(pattern, code, flags=re.IGNORECASE | re.MULTILINE):
            findings.append(
                Finding(
                    category=category,
                    severity=severity,
                    explanation=explanation,
                    likely_impact=impact,
                    recommended_fix=fix,
                    line=line_number_for_pattern(code, pattern),
                )
            )

    signals = collect_signals(code, request.language)
    if not signals.parse_ok and signals.parse_error:
        findings.insert(
            0,
            Finding(
                category="Syntax",
                severity="critical",
                explanation=signals.parse_error,
                likely_impact="The analyzer cannot fully inspect malformed code.",
                recommended_fix="Fix syntax before relying on deeper static findings.",
            ),
        )

    confidence, reason, _ = confidence_from_signals(signals, request.language)
    summary = (
        "No obvious deterministic bug patterns detected."
        if not findings
        else f"{len(findings)} potential issue(s) detected by static rules."
    )
    return BugDetectorResponse(
        findings=findings, summary=summary, confidence=confidence, reason=reason, limitations=LIMITATIONS
    )
