# API

Base URL: `http://127.0.0.1:8000`

## Health

`GET /health`

Returns service status and confirms static-analysis-only mode.

## Code Analyzer

`POST /api/analyze`

```json
{ "language": "python", "code": "def f(x):\n    return x + 1" }
```

Returns overall score, category scores, suggestions, risks, confidence, reason, and limitations.

## Bug Detector

`POST /api/bugs`

Accepts the same payload as the code analyzer. Returns findings with severity, explanation, likely impact, recommended fix, and line where available.

## Test Case Generator

`POST /api/test-cases`

Returns normal, edge, corner, and stress cases plus JSON and CSV exports.

## Complexity Analyzer

`POST /api/complexity`

Returns time complexity, space complexity, explanation, and confidence score.

## Solution Comparator

`POST /api/compare`

```json
{ "language": "python", "solution_a": "def a(): pass", "solution_b": "def b(): pass" }
```

Returns winner, score breakdown, and summary.

## LLM Code Evaluator

`POST /api/llm-evaluate`

```json
{ "prompt": "Write a parser", "ai_response": "Use a finite-state parser...", "language": "python" }
```

Returns evaluator-style report, hallucination risks, and safety notes.

## Reasoning Reviewer

`POST /api/reasoning`

```json
{ "problem": "Assess two-sum correctness", "reasoning": "1. Assume..." }
```

Returns score, feedback, missing assumptions, and contradictions.

## Dataset Builder

`POST /api/dataset`

```json
{ "topic": "Array evaluation", "language": "python", "count": 5, "difficulty": "mixed", "tags": ["benchmark"] }
```

Returns generated dataset items with JSON and CSV exports.

## Rubric Engine

`POST /api/rubric`

```json
{ "categories": [{ "name": "correctness", "weight": 0.4, "score": 80 }] }
```

Returns normalized weights, weighted score, and interpretation.

## Benchmark Dashboard

`GET /api/benchmarks`

Returns evaluations performed, average score, bug categories, complexity distribution, and module distribution.

