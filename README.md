# CodeJudge AI

Evaluate code, reasoning, and AI outputs like professional model evaluators.

CodeJudge AI is a deterministic software quality and AI evaluation platform. It is not a chatbot, code execution sandbox, IDE, interview runner, or LeetCode clone. Submitted artifacts are parsed and inspected only.

## Current Phase

- Phase 1 product discovery: complete in `PRODUCT.md`.
- Phase 2 architecture: complete in `ARCHITECTURE.md`.
- Phase 3 domain model and contracts: complete in `docs/DOMAIN_MODEL.md`, `docs/API_CONTRACTS.md`, `docs/SCHEMAS.md`, `apps/api/app/contracts.py`, and `packages/contracts/src/index.ts`.
- Phase 4 monorepo foundation: complete with apps, packages, docs, tests, tools, linting, formatting, typing, and CI.

Core analysis engines are the next phase. No future scoring route should ship unless its score is derived from ASTs, parser trees, static rules, metrics, rubric weights, or deterministic heuristics.

## Repository

```text
apps/
  api/          FastAPI backend workspace
  web/          Next.js web workspace
packages/
  contracts/    Shared TypeScript and Zod contracts
docs/           Domain, API, and schema documentation
tests/          Cross-workspace test strategy and future suites
tools/          Local verification helpers
```

## Verification

```powershell
npm run verify
```

This runs TypeScript and API linting, Prettier and Ruff format checks, TypeScript and Python type checks, and contract, web, and API tests.

## Local Development

```powershell
npm run dev:api
npm run dev:web
```

The API runs at `http://127.0.0.1:8000`. The web app runs at `http://127.0.0.1:3000`.

## Docker

```powershell
docker compose up --build
```

## Safety Model

CodeJudge AI does not execute uploaded code. It does not import, compile, shell out, or run submitted content. Evaluation is deterministic and evidence-first.
