# Contributing

## Principles

CodeJudge AI is deterministic and static-analysis-only. Do not add code execution, remote LLM calls, model-generated judgment, or hidden scoring logic.

Every evaluation result must expose score, confidence, evidence, limitations, detected patterns, findings, breakdown, and why.

## Monorepo

- `apps/api`: FastAPI backend and Python contracts.
- `apps/web`: Next.js web workspace.
- `packages/contracts`: shared TypeScript and Zod contracts.
- `docs`: product, architecture, domain, API, and schema documentation.
- `tests`: repo-level cross-workspace test strategy.
- `tools`: local verification helpers.

## Quality Gate

Run before handing off work:

```powershell
npm run verify
```

This checks linting, formatting, typing, and tests across the API, web app, and shared contracts.

## Security

- Never execute submitted code.
- Never compile or import submitted code.
- Never pass submitted content to a shell.
- Never store secrets in source.
- Keep user input escaped when rendered.
