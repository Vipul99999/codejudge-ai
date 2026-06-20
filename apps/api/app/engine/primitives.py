from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from app.contracts import (
    BaseEvaluationResultDTO,
    DetectedPattern,
    EvaluationType,
    Evidence,
    Finding,
    Language,
    Limitation,
    ScoreBreakdown,
    SourceSpan,
    SupportTier,
)

ENGINE_VERSION = "phase5.0.1"
ScopeName = Literal["parser", "language", "static_analysis", "rubric", "input", "engine"]

STATIC_LIMITATIONS = [
    Limitation(
        id="lim-static-runtime",
        scope="static_analysis",
        message="Code is parsed and inspected only; runtime correctness is not proven.",
    ),
    Limitation(
        id="lim-cross-file",
        scope="input",
        message="Cross-file dependencies and external library contracts are not resolved.",
    ),
]


@dataclass(frozen=True)
class FunctionSignal:
    name: str
    start_line: int
    end_line: int
    branch_count: int
    loop_count: int
    returns: int
    raises: int

    @property
    def length(self) -> int:
        return max(1, self.end_line - self.start_line + 1)


@dataclass(frozen=True)
class CodeMetrics:
    language: Language
    support_tier: SupportTier
    line_count: int
    non_empty_lines: int
    comment_lines: int
    avg_line_length: float
    max_line_length: int
    function_count: int
    class_count: int
    loop_count: int
    branch_count: int
    nesting_depth: int
    duplicate_lines: int
    long_functions: int
    short_identifier_ratio: float
    descriptive_identifier_ratio: float
    guard_clause_count: int
    error_handling_count: int
    allocation_count: int
    mutation_count: int
    async_count: int
    await_count: int
    recursion_count: int
    parse_ok: bool
    parse_error: str | None
    identifiers: tuple[str, ...]
    functions: tuple[FunctionSignal, ...]

    @property
    def comment_density(self) -> float:
        return self.comment_lines / max(self.non_empty_lines, 1)

    @property
    def cyclomatic_complexity(self) -> int:
        return max(1, 1 + self.branch_count + self.loop_count)

    @property
    def maintainability_index(self) -> float:
        volume_proxy = max(1.0, self.non_empty_lines * math.log2(max(2, len(self.identifiers) + 1)))
        complexity = self.cyclomatic_complexity
        raw = (
            171
            - 5.2 * math.log(volume_proxy)
            - 0.23 * complexity
            - 16.2 * math.log(max(1, self.non_empty_lines))
        )
        return clamp(raw * 100 / 171)


def now_utc() -> datetime:
    return datetime.now(UTC)


def checksum_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    digest = checksum_text("|".join(str(part) for part in parts))[:16]
    return f"{prefix}-{digest}"


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def clamp_confidence(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def weighted_score(items: Iterable[tuple[float, float]]) -> float:
    weighted_sum = 0.0
    weight_sum = 0.0
    for score, weight in items:
        weighted_sum += score * weight
        weight_sum += weight
    if weight_sum == 0:
        return 0
    return round(clamp(weighted_sum / weight_sum), 2)


def line_span(source: str, line_number: int, rule_id: str) -> Evidence:
    lines = source.splitlines()
    line = lines[line_number - 1] if 0 <= line_number - 1 < len(lines) else ""
    return Evidence(
        id=stable_id("ev", rule_id, line_number, line.strip()),
        kind="token_pattern",
        message=f"Rule {rule_id} matched line {line_number}.",
        rule_id=rule_id,
        span=SourceSpan(
            start_line=line_number,
            start_column=1,
            end_line=line_number,
            end_column=max(1, len(line) + 1),
            snippet=line[:500],
        ),
    )


def metric_evidence(
    rule_id: str, metric_name: str, metric_value: int | float | str | bool
) -> Evidence:
    return Evidence(
        id=stable_id("ev", rule_id, metric_name, metric_value),
        kind="metric",
        message=f"{metric_name.replace('_', ' ')} = {metric_value}.",
        rule_id=rule_id,
        metric_name=metric_name,
        metric_value=metric_value,
    )


def limitation(id_suffix: str, scope: ScopeName, message: str) -> Limitation:
    return Limitation(id=f"lim-{id_suffix}", scope=scope, message=message)


def support_tier_for(language: Language) -> SupportTier:
    if language == Language.python:
        return SupportTier.tier_1
    if language in {Language.javascript, Language.typescript}:
        return SupportTier.tier_2
    return SupportTier.tier_3


LANGUAGE_HINTS: dict[Language, dict[str, str]] = {
    Language.python: {"comment": "#", "function": r"\bdef\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("},
    Language.javascript: {
        "comment": "//",
        "function": r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(|([A-Za-z_$][\w$]*)\s*=\s*\([^)]*\)\s*=>",
    },
    Language.typescript: {
        "comment": "//",
        "function": r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(|([A-Za-z_$][\w$]*)\s*=\s*\([^)]*\)\s*=>",
    },
    Language.java: {
        "comment": "//",
        "function": r"\b(public|private|protected)?\s*(static\s+)?[\w<>\[\]]+\s+(\w+)\s*\(",
    },
    Language.cpp: {"comment": "//", "function": r"\b[\w:<>\*&]+\s+(\w+)\s*\("},
}

KEYWORDS = {
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
    "async",
    "await",
    "switch",
    "case",
    "true",
    "false",
    "null",
    "none",
}


def split_identifiers(source: str) -> tuple[str, ...]:
    tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", source)
    return tuple(token for token in tokens if token.lower() not in KEYWORDS)


def estimate_text_nesting(source: str) -> int:
    max_depth = 0
    brace_depth = 0
    for raw in source.splitlines():
        leading_spaces = len(raw) - len(raw.lstrip(" "))
        indent_depth = leading_spaces // 4
        brace_depth += raw.count("{") - raw.count("}")
        max_depth = max(max_depth, indent_depth, brace_depth)
    return max_depth


def count_regex(pattern: str, source: str, flags: int = re.IGNORECASE) -> int:
    return len(re.findall(pattern, source, flags=flags))


def find_line(pattern: str, source: str, flags: int = re.IGNORECASE) -> int | None:
    compiled = re.compile(pattern, flags)
    for index, line in enumerate(source.splitlines(), start=1):
        if compiled.search(line):
            return index
    return None


def python_ast_metrics(
    source: str,
) -> tuple[
    bool,
    str | None,
    int,
    int,
    int,
    int,
    int,
    int,
    int,
    tuple[str, ...],
    tuple[FunctionSignal, ...],
]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return (
            False,
            f"Python syntax error near line {exc.lineno}: {exc.msg}",
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            (),
            (),
        )

    functions = [
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    loops = [
        node for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While, ast.AsyncFor))
    ]
    branches = [node for node in ast.walk(tree) if isinstance(node, (ast.If, ast.Try, ast.Match))]
    identifiers = tuple(node.id for node in ast.walk(tree) if isinstance(node, ast.Name))

    def depth(node: ast.AST, current: int = 0) -> int:
        children = list(ast.iter_child_nodes(node))
        bump = (
            1 if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)) else 0
        )
        if not children:
            return current + bump
        return max(depth(child, current + bump) for child in children)

    function_signals: list[FunctionSignal] = []
    long_functions = 0
    recursion_count = 0
    for function in functions:
        start = getattr(function, "lineno", 1)
        end = getattr(function, "end_lineno", start)
        body_nodes = list(ast.walk(function))
        branch_count = sum(isinstance(node, (ast.If, ast.Try, ast.Match)) for node in body_nodes)
        loop_count = sum(
            isinstance(node, (ast.For, ast.While, ast.AsyncFor)) for node in body_nodes
        )
        returns = sum(isinstance(node, ast.Return) for node in body_nodes)
        function_raises = sum(isinstance(node, ast.Raise) for node in body_nodes)
        calls = [node for node in body_nodes if isinstance(node, ast.Call)]
        if any(isinstance(call.func, ast.Name) and call.func.id == function.name for call in calls):
            recursion_count += 1
        signal = FunctionSignal(
            name=function.name,
            start_line=start,
            end_line=end,
            branch_count=branch_count,
            loop_count=loop_count,
            returns=returns,
            raises=function_raises,
        )
        function_signals.append(signal)
        if signal.length > 60:
            long_functions += 1

    return (
        True,
        None,
        len(functions),
        len(classes),
        len(loops),
        len(branches),
        depth(tree),
        long_functions,
        recursion_count,
        identifiers,
        tuple(function_signals),
    )


def collect_code_metrics(source: str, language: Language) -> CodeMetrics:
    lines = source.splitlines() or [source]
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
    identifiers = split_identifiers(source)

    function_pattern = LANGUAGE_HINTS[language]["function"]
    function_count = len(re.findall(function_pattern, source))
    class_count = count_regex(r"\bclass\s+\w+", source)
    loop_count = count_regex(r"\b(for|while|do)\b", source)
    branch_count = count_regex(r"\b(if|else if|switch|case|catch|except|match)\b", source)
    nesting_depth = estimate_text_nesting(source)
    long_functions = sum(1 for line in source.split("\n\n") if line.count("\n") > 60)
    recursion_count = 0
    parse_ok = True
    parse_error = None
    functions: tuple[FunctionSignal, ...] = ()

    if language == Language.python:
        (
            parse_ok,
            parse_error,
            function_count,
            class_count,
            loop_count,
            branch_count,
            nesting_depth,
            long_functions,
            recursion_count,
            py_identifiers,
            functions,
        ) = python_ast_metrics(source)
        identifiers = py_identifiers or identifiers
    else:
        recursion_count = estimate_text_recursion(source)

    short_names = sum(1 for identifier in identifiers if len(identifier) <= 2)
    descriptive = sum(1 for identifier in identifiers if len(identifier) >= 4 or "_" in identifier)
    identifier_count = max(1, len(identifiers))

    return CodeMetrics(
        language=language,
        support_tier=support_tier_for(language),
        line_count=len(lines),
        non_empty_lines=len(non_empty),
        comment_lines=comment_lines,
        avg_line_length=avg_len,
        max_line_length=max_len,
        function_count=function_count,
        class_count=class_count,
        loop_count=loop_count,
        branch_count=branch_count,
        nesting_depth=nesting_depth,
        duplicate_lines=duplicate_lines,
        long_functions=long_functions,
        short_identifier_ratio=short_names / identifier_count,
        descriptive_identifier_ratio=descriptive / identifier_count,
        guard_clause_count=count_regex(
            r"\b(if\s+not|if\s*\([^)]*!|return\s+|raise\s+|throw\s+)", source
        ),
        error_handling_count=count_regex(r"\b(try|catch|except|finally|raise|throw)\b", source),
        allocation_count=count_regex(
            r"\b(new|malloc|calloc|append|push|extend|vector|Map|Set|dict|list)\b", source
        ),
        mutation_count=count_regex(
            r"(\+\+|--|\+=|-=|\*=|/=|append\(|push\(|pop\(|remove\()", source
        ),
        async_count=count_regex(
            r"\b(async|Promise|Future|CompletableFuture|Thread|asyncio)\b", source
        ),
        await_count=count_regex(r"\b(await|then|join|get\()\b", source),
        recursion_count=recursion_count,
        parse_ok=parse_ok,
        parse_error=parse_error,
        identifiers=identifiers,
        functions=functions,
    )


def estimate_text_recursion(source: str) -> int:
    names = re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", source)
    names += re.findall(r"\b([A-Za-z_$][\w$]*)\s*=\s*\([^)]*\)\s*=>", source)
    names += re.findall(
        r"\b(public|private|protected)?\s*(?:static\s+)?[\w<>\[\]]+\s+(\w+)\s*\(", source
    )
    flat_names = [name[-1] if isinstance(name, tuple) else name for name in names]
    return sum(1 for name in flat_names if re.search(rf"\b{name}\s*\(", source))


def evidence_for_metrics(metrics: CodeMetrics) -> list[Evidence]:
    return [
        metric_evidence("metric.lines", "non_empty_lines", metrics.non_empty_lines),
        metric_evidence(
            "metric.cyclomatic", "cyclomatic_complexity", metrics.cyclomatic_complexity
        ),
        metric_evidence("metric.nesting", "nesting_depth", metrics.nesting_depth),
        metric_evidence("metric.duplication", "duplicate_lines", metrics.duplicate_lines),
        metric_evidence("metric.functions", "function_count", metrics.function_count),
        metric_evidence(
            "metric.identifier_quality",
            "short_identifier_ratio",
            round(metrics.short_identifier_ratio, 3),
        ),
        metric_evidence(
            "metric.maintainability",
            "maintainability_index",
            round(metrics.maintainability_index, 2),
        ),
    ]


def base_limitations(metrics: CodeMetrics) -> list[Limitation]:
    limits = list(STATIC_LIMITATIONS)
    if not metrics.parse_ok and metrics.parse_error:
        limits.append(limitation("parse-failure", "parser", metrics.parse_error))
    if metrics.support_tier == SupportTier.tier_3:
        limits.append(
            limitation(
                "tier3-language",
                "language",
                "This language uses token and structure heuristics rather than a full AST.",
            )
        )
    return limits


def build_result(
    evaluation_type: EvaluationType,
    source_key: str,
    score: float,
    confidence: float,
    evidence: Sequence[Evidence],
    limitations: Sequence[Limitation],
    patterns: Sequence[DetectedPattern],
    findings: Sequence[Finding],
    breakdown: Sequence[ScoreBreakdown],
    why: str,
    rubric_version_id: str | None = None,
) -> BaseEvaluationResultDTO:
    return BaseEvaluationResultDTO(
        id=stable_id("eval", evaluation_type.value, source_key, ENGINE_VERSION),
        evaluation_type=evaluation_type,
        score=round(clamp(score), 2),
        confidence=clamp_confidence(confidence),
        evidence=list(evidence),
        limitations=list(limitations),
        detected_patterns=list(patterns),
        findings=list(findings),
        breakdown=list(breakdown),
        why=why,
        engine_version=ENGINE_VERSION,
        rubric_version_id=rubric_version_id,
        created_at=now_utc(),
    )


def serialize_json(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def serialize_csv(rows: Sequence[dict[str, object]]) -> str:
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
