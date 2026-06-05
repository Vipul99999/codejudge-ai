# Schemas

Status: Phase 3 frozen interface artifact.

CodeJudge AI maintains matching Python and TypeScript schemas.

## Python

`apps/api/app/contracts.py` defines Pydantic models for backend validation, persistence boundaries, and API DTOs.

## TypeScript

`packages/contracts/src/index.ts` defines Zod schemas and inferred TypeScript types for frontend validation and contract tests.

## Contract Principles

- Unknown fields are rejected on backend Pydantic contracts.
- Scores are bounded from 0 to 100.
- Confidence is bounded from 0 to 1.
- Evidence is linked through stable `evidence_ids`.
- Rubric versions are immutable and checksum-addressable.
- Export requests are explicit about resource type and format.
