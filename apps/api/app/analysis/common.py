from __future__ import annotations

import ast
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from app.models import CategoryScore, Confidence, Language

LIMITATIONS = [
    "Code is parsed and inspected, never executed.",
    "Findings are deterministic heuristics and may miss runtime-only behavior.",
    "Cross-file dependencies and external library contracts are not resolved.",
]


LANGUAGE_HINTS: dict[Language, dict[str, str]] = {
    Language.python: {"comment": "#", "function": r"\bdef\s+\w+\s*\("},
    Language.javascript: {"comment": "//", "function": r"\bfunction\s+\w+\s*\(|=>"},
    Language.typescript: {"comment": "//", "function": r"\bfunction\s+\w+\s*\(|=>"},
    Language.java: {
        "comment": "//",
        "function": r"\b(public|private|protected)?\s*(static\s+)?[\w<>\[\]]+\s+\w+\s*\(",
    },
    Language.cpp: {"comment": "//", "function": r"\b[\w:<>\*&]+\s+\w+\s*\("},
}


@dataclass(frozen=True)
class CodeSignals:
    line_count: int
    non_empty_lines: int
    comment_lines: int
    avg_line_length: float
    max_line_length: int
    function_count: int
    loop_count: int
    branch_count: int
    nesting_depth: int
    duplicate_lines: int
    long_functions: int
    parse_ok: bool
    parse_error: str | None
    identifiers: list[str]


def clamp(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, round(value)))


def line_number_for_pattern(code: str, pattern: str) -> int | None:
    compiled = re.compile(pattern)
    for index, line in enumerate(code.splitlines(), start=1):
        if compiled.search(line):
            return index
    return None


def split_identifiers(code: str) -> list[str]:
    tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code)
    keywords = {
        "if",
        "else",
        "for",
        "while",
        "return",
        "class",
        "def",
        "function",
        "const",
        "let",
        "var",
        "public",
        "private",
        "static",
        "void",
        "int",
        "float",
        "double",
        "string",
        "new",
        "try",
        "catch",
        "except",
        "import",
        "from",
    }
    return [token for token in tokens if token.lower() not in keywords]


def python_ast_signals(code: str) -> tuple[bool, str | None, int, int, int, int, list[str], int]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"Python syntax error near line {exc.lineno}: {exc.msg}", 0, 0, 0, 0, [], 0

    functions = [
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    loops = [
        node for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While, ast.AsyncFor))
    ]
    branches = [node for node in ast.walk(tree) if isinstance(node, (ast.If, ast.Try, ast.Match))]
    identifiers = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]

    def depth(node: ast.AST, current: int = 0) -> int:
        children = list(ast.iter_child_nodes(node))
        bump = (
            1 if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)) else 0
        )
        if not children:
            return current + bump
        return max(depth(child, current + bump) for child in children)

    long_functions = 0
    for function in functions:
        start = getattr(function, "lineno", 0)
        end = getattr(function, "end_lineno", start)
        if end - start + 1 > 60:
            long_functions += 1

    return (
        True,
        None,
        len(functions),
        len(loops),
        len(branches),
        depth(tree),
        identifiers,
        long_functions,
    )


def collect_signals(code: str, language: Language) -> CodeSignals:
    lines = code.splitlines() or [code]
    stripped = [line.strip() for line in lines]
    non_empty = [line for line in stripped if line]
    comment_prefix = LANGUAGE_HINTS[language]["comment"]
    comment_lines = sum(1 for line in non_empty if line.startswith(comment_prefix))
    normalized = [
        line for line in non_empty if not line.startswith(comment_prefix) and len(line) > 6
    ]
    duplicate_lines = sum(count - 1 for count in Counter(normalized).values() if count > 1)
    avg_len = sum(len(line) for line in lines) / max(len(lines), 1)
    max_len = max((len(line) for line in lines), default=0)

    parse_ok = True
    parse_error = None
    function_pattern = LANGUAGE_HINTS[language]["function"]
    function_count = len(re.findall(function_pattern, code))
    loop_count = len(re.findall(r"\b(for|while|do)\b", code))
    branch_count = len(re.findall(r"\b(if|else if|switch|case|catch|except|match)\b", code))
    nesting_depth = estimate_text_nesting(code)
    identifiers = split_identifiers(code)
    long_functions = 0

    if language == Language.python:
        py = python_ast_signals(code)
        (
            parse_ok,
            parse_error,
            function_count,
            loop_count,
            branch_count,
            nesting_depth,
            py_ids,
            long_functions,
        ) = py
        identifiers = py_ids or identifiers

    return CodeSignals(
        line_count=len(lines),
        non_empty_lines=len(non_empty),
        comment_lines=comment_lines,
        avg_line_length=avg_len,
        max_line_length=max_len,
        function_count=function_count,
        loop_count=loop_count,
        branch_count=branch_count,
        nesting_depth=nesting_depth,
        duplicate_lines=duplicate_lines,
        long_functions=long_functions,
        parse_ok=parse_ok,
        parse_error=parse_error,
        identifiers=identifiers,
    )


def estimate_text_nesting(code: str) -> int:
    max_depth = 0
    brace_depth = 0
    for raw in code.splitlines():
        leading_spaces = len(raw) - len(raw.lstrip(" "))
        indent_depth = leading_spaces // 4
        brace_depth += raw.count("{") - raw.count("}")
        max_depth = max(max_depth, indent_depth, brace_depth)
    return max_depth


def score_from_penalties(base: int, penalties: Iterable[float]) -> int:
    return clamp(base - sum(penalties))


def confidence_from_signals(
    signals: CodeSignals, language: Language
) -> tuple[Confidence, str, int]:
    if language == Language.python and signals.parse_ok and signals.non_empty_lines > 6:
        return Confidence.high, "Python AST parsed successfully with static heuristics", 88
    if signals.non_empty_lines > 20 and signals.function_count > 0:
        return Confidence.medium, "Pattern detected with language-aware heuristics", 72
    return Confidence.low, "Heuristic estimate from limited static signals", 48


def category(name: str, score: int, rationale: str) -> CategoryScore:
    return CategoryScore(name=name, score=clamp(score), rationale=rationale)


def safe_average(values: Iterable[int]) -> int:
    numbers = list(values)
    if not numbers:
        return 0
    return clamp(sum(numbers) / len(numbers))


def csv_escape(value: str) -> str:
    escaped = value.replace('"', '""')
    return f'"{escaped}"'


def stable_hash_score(text: str, minimum: int = 0, maximum: int = 100) -> int:
    total = sum((index + 1) * ord(char) for index, char in enumerate(text))
    return minimum + (total % (maximum - minimum + 1))
