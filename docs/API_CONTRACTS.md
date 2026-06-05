# API Contracts

Status: Phase 3 frozen interface artifact.

This document defines the stable resource families and payload shape for CodeJudge AI. Exact route handlers are implemented in later phases, but future implementation must conform to these contracts.

## Global Rules

- API payloads are JSON unless an export route returns file bytes.
- Submitted source, prompts, AI responses, and reasoning are untrusted text.
- The API never executes code and never calls model APIs.
- Every evaluation result returns score, confidence, evidence, limitations, detected patterns, findings, breakdown, and why.
- Error responses use `ApiErrorDTO`.

## Health

### `GET /health`

Returns liveness.

### `GET /ready`

Returns readiness after storage, parser registry, and configuration checks pass.

### `GET /metrics`

Returns Prometheus-compatible metrics.

## Analysis

### `POST /api/analysis/code-review`

Request: `AnalysisRequestDTO` with `evaluation_type = code_review` and `CodeArtifactDTO`.

Response: `BaseEvaluationResultDTO`.

### `POST /api/analysis/bug-risk`

Request: `AnalysisRequestDTO` with `evaluation_type = bug_risk` and `CodeArtifactDTO`.

Response: `BaseEvaluationResultDTO`.

### `POST /api/analysis/test-generation`

Request: `AnalysisRequestDTO` with `evaluation_type = test_generation` and `CodeArtifactDTO`.

Response: `BaseEvaluationResultDTO` plus exportable test artifacts in the later Phase 5 engine-specific extension.

### `POST /api/analysis/complexity`

Request: `AnalysisRequestDTO` with `evaluation_type = complexity` and `CodeArtifactDTO`.

Response: `BaseEvaluationResultDTO`.

### `POST /api/analysis/compare`

Request: `CompareSolutionsRequestDTO`.

Response: `BaseEvaluationResultDTO` with solution comparison findings, tradeoffs, and winner encoded as detected patterns and findings.

### `POST /api/analysis/ai-response`

Request: `AnalysisRequestDTO` with `evaluation_type = ai_response` and `PromptResponseArtifactDTO`.

Response: `BaseEvaluationResultDTO`.

### `POST /api/analysis/reasoning`

Request: `AnalysisRequestDTO` with `evaluation_type = reasoning` and `ReasoningArtifactDTO`.

Response: `BaseEvaluationResultDTO`.

## Rubrics

### `POST /api/rubrics`

Creates a rubric family.

### `POST /api/rubrics/{rubric_id}/versions`

Creates a frozen rubric version. Weights must be normalized before scoring.

### `GET /api/rubrics/{rubric_id}/versions/{version_id}`

Returns `RubricVersionEntity`.

## Datasets

### `POST /api/datasets`

Creates a dataset container.

### `POST /api/datasets/{dataset_id}/versions`

Creates a dataset version from deterministic dataset items.

### `GET /api/datasets/{dataset_id}/versions/{version_id}`

Returns dataset version metadata and items.

## Benchmarks

### `GET /api/benchmarks`

Returns aggregate evaluation counts, score distributions, confidence bands, language trends, and failure categories.

### `GET /api/benchmarks/events`

Returns paginated `BenchmarkEventEntity` records.

## Exports

### `POST /api/exports`

Request: `ExportRequestDTO`.

Supported formats:

- `json`
- `csv`
- `parquet`

Response includes bytes, content type, checksum, and `ExportArtifactEntity` metadata.

## Error Contract

```json
{
  "code": "validation_error",
  "message": "Request body failed schema validation.",
  "request_id": "req_..."
}
```

## Compatibility Rule

Once Phase 3 is approved, a contract change requires one of:

- A backward-compatible field addition.
- A new API version.
- A documented migration.
