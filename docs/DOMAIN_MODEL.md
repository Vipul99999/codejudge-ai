# Domain Model

Status: Phase 3 frozen interface artifact.

This document defines CodeJudge AI domain entities and value objects. Implementation can evolve, but these interface concepts are the stable vocabulary for backend contracts, frontend schemas, persistence, and tests.

## Score And Confidence

- `score`: number from 0 to 100. Higher is better. Scores must be derived from parser output, static rules, metrics, rubric weights, and deterministic heuristics.
- `confidence`: number from 0 to 1. Higher means the engine has stronger support for the result. Confidence is not a score and must not hide limitations.
- Every result includes score, confidence, evidence, limitations, detected patterns, findings, breakdown, and why.

## Core Value Objects

### SourceSpan

Identifies a region in submitted source or text.

- `start_line`
- `start_column`
- `end_line`
- `end_column`
- `snippet`

### Evidence

Represents one observable reason a result exists.

- `id`
- `kind`: `ast_node`, `token_pattern`, `metric`, `rubric_match`, or `text_pattern`
- `message`
- `rule_id`
- `span`
- `metric_name`
- `metric_value`

### Limitation

States what the platform cannot prove or inspect.

- `id`
- `scope`: `parser`, `language`, `static_analysis`, `rubric`, `input`, or `engine`
- `message`

### DetectedPattern

Groups evidence into an interpretable pattern.

- `id`
- `name`
- `category`
- `confidence`
- `evidence_ids`

### Finding

Represents a risk, quality issue, rubric issue, or evaluation observation.

- `id`
- `rule_id`
- `title`
- `category`
- `severity`
- `probability`
- `score_impact`
- `confidence`
- `evidence_ids`
- `why`
- `recommendation`

### ScoreBreakdown

Explains category-level scoring.

- `category`
- `score`
- `weight`
- `why`
- `evidence_ids`

## Entities

### Workspace

Groups evaluations, rubrics, datasets, benchmark events, exports, and audit events.

### Evaluation

Immutable record of one deterministic evaluation run.

- `id`
- `workspace_id`
- `artifact_ref`
- `evaluation_type`
- `engine_version`
- `rubric_version_id`
- `score`
- `confidence`
- `created_at`

### ArtifactRef

References an input artifact without requiring raw content to be stored in every downstream record.

- `id`
- `input_type`
- `checksum`
- `language`
- `size_bytes`

### RubricVersion

Frozen version of weighted evaluation criteria.

- `id`
- `rubric_id`
- `version`
- `name`
- `criteria`
- `checksum`
- `created_at`

### DatasetItem

Structured benchmark or training item.

- `id`
- `problem`
- `solution`
- `rubric_version_id`
- `difficulty`
- `tags`

### BenchmarkEvent

Analytical fact emitted by an evaluation.

- `id`
- `evaluation_id`
- `workspace_id`
- `evaluation_type`
- `language`
- `score`
- `confidence`
- `latency_ms`
- `failure_categories`
- `engine_version`
- `rubric_version_id`
- `occurred_at`

### ExportArtifact

Audit record for generated exports.

### AuditEvent

Security and compliance event for create, analyze, export, and rubric-version actions.

## Enums

- `Language`: `python`, `javascript`, `typescript`, `java`, `cpp`
- `SupportTier`: `tier_1`, `tier_2`, `tier_3`, `unsupported`
- `InputType`: `source_code`, `prompt_response`, `reasoning_trace`, `rubric`, `dataset_item`, `solution_pair`
- `EvaluationType`: `code_review`, `bug_risk`, `test_generation`, `complexity`, `solution_comparison`, `ai_response`, `reasoning`, `dataset_build`, `rubric_score`, `benchmark_summary`
- `Severity`: `critical`, `high`, `medium`, `low`, `info`
- `Probability`: `high`, `medium`, `low`, `unknown`
- `ExportFormat`: `json`, `csv`, `parquet`
- `Difficulty`: `easy`, `medium`, `hard`, `mixed`

## Source Of Truth

- Python contracts live in `apps/api/app/contracts.py`.
- TypeScript and Zod contracts live in `packages/contracts/src/index.ts`.
- API resource contracts are documented in `docs/API_CONTRACTS.md`.
