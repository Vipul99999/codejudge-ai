from __future__ import annotations

import json

from app.analysis.common import LIMITATIONS
from app.models import CodeRequest, Confidence, TestCase, TestCaseResponse


def generate_test_cases(request: CodeRequest) -> TestCaseResponse:
    lower = request.code.lower()
    is_array_like = any(token in lower for token in ["array", "list", "vector", "arr", "nums"])
    is_string_like = any(token in lower for token in ["string", "str", "char", "substring"])
    is_graph_like = any(token in lower for token in ["graph", "node", "edge", "dfs", "bfs"])

    if is_graph_like:
        normal_input = "4 4\n1 2\n2 3\n3 4\n1 4"
        expected = "reachable"
        focus = "connected graph traversal"
    elif is_string_like:
        normal_input = "codejudge"
        expected = "valid transformed output"
        focus = "typical non-empty string"
    elif is_array_like:
        normal_input = "[1, 2, 3, 4]"
        expected = "computed result for ordered positives"
        focus = "standard list input"
    else:
        normal_input = "n = 5"
        expected = "result for representative input"
        focus = "representative scalar input"

    cases = [
        TestCase(case_type="normal", input=normal_input, expected_output=expected, reason=f"Covers {focus}."),
        TestCase(
            case_type="edge",
            input='empty input / [] / ""',
            expected_output="graceful empty-result behavior",
            reason="Validates empty collection or missing data handling.",
        ),
        TestCase(
            case_type="corner",
            input="single element / n = 1",
            expected_output="base case result",
            reason="Catches off-by-one and initialization errors.",
        ),
        TestCase(
            case_type="corner",
            input="duplicates, zeros, and negative values",
            expected_output="stable result with repeated and signed values",
            reason="Exposes assumptions about uniqueness and positivity.",
        ),
        TestCase(
            case_type="stress",
            input="maximum documented input size",
            expected_output="same semantics within expected complexity bounds",
            reason="Checks algorithmic scalability without executing code here.",
        ),
    ]
    exported = json.dumps([case.model_dump() for case in cases], indent=2)
    csv = "case_type,input,expected_output,reason\n" + "\n".join(
        f'{case.case_type},"{case.input}","{case.expected_output}","{case.reason}"' for case in cases
    )
    return TestCaseResponse(
        cases=cases,
        export={"json": exported, "csv": csv},
        confidence=Confidence.medium,
        reason="Pattern detected with heuristic test design",
        limitations=LIMITATIONS,
    )
