# Architecture

CodeJudge AI uses a two-service architecture.

## Frontend

The Next.js app in `frontend/` provides a single evaluator console with module navigation, Monaco code editing, structured result rendering, export buttons, local history, and benchmark charts.

State is managed with Zustand and persisted in local storage. API payloads are shaped through TypeScript types and Zod schemas for benchmark validation.

## Backend

The FastAPI app in `backend/` exposes REST endpoints under `/api/*`. Each endpoint delegates to a deterministic analyzer in `backend/app/analysis/`.

Python submissions receive deeper AST parsing through the standard `ast` module. Other languages use language-aware token, pattern, nesting, loop, branch, and allocation heuristics. This keeps the system deterministic while supporting Python, JavaScript, TypeScript, Java, and C++.

## Data Flow

1. User selects an evaluator and enters code, prompt text, reasoning text, dataset topic, or rubric JSON.
2. Frontend posts JSON to the matching FastAPI endpoint.
3. Backend validates input with Pydantic.
4. Analyzer returns structured scores, findings, exports, confidence, reason, and limitations.
5. API records a local benchmark event in an in-memory rolling store.
6. Dashboard reads aggregate metrics from `/api/benchmarks`.

## Security Boundary

The backend never imports, compiles, executes, shells out, or sandbox-runs submitted code. The analyzer only reads text and syntax structures.

