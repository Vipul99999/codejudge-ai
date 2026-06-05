# API

Status: Phase 3 frozen contract summary.

The detailed API contract is maintained in [docs/API_CONTRACTS.md](docs/API_CONTRACTS.md). Runtime endpoints are implemented only after the relevant deterministic engines exist. No route may return fabricated scores or model-generated judgment.

## Base Rules

- CodeJudge AI never executes submitted code.
- CodeJudge AI never calls LLM APIs for evaluation.
- Every evaluation result must include score, confidence, evidence, limitations, detected patterns, findings, breakdown, and why.
- Scores are bounded from 0 to 100 and must come from ASTs, parser trees, static rules, metrics, rubric weights, or deterministic heuristics.
- Confidence is bounded from 0 to 1 and must explain uncertainty.

## Resource Families

- `GET /health`
- `GET /ready`
- `GET /metrics`
- `POST /api/analysis/code-review`
- `POST /api/analysis/bug-risk`
- `POST /api/analysis/test-generation`
- `POST /api/analysis/complexity`
- `POST /api/analysis/compare`
- `POST /api/analysis/ai-response`
- `POST /api/analysis/reasoning`
- `POST /api/rubrics`
- `POST /api/rubrics/{rubric_id}/versions`
- `GET /api/rubrics/{rubric_id}/versions/{version_id}`
- `POST /api/datasets`
- `POST /api/datasets/{dataset_id}/versions`
- `GET /api/datasets/{dataset_id}/versions/{version_id}`
- `GET /api/benchmarks`
- `GET /api/benchmarks/events`
- `POST /api/exports`

## Source Of Truth

- Backend Pydantic contracts: `apps/api/app/contracts.py`
- Shared TypeScript/Zod contracts: `packages/contracts/src/index.ts`
- Domain model: `docs/DOMAIN_MODEL.md`
