# CodeJudge AI

CodeJudge AI is a production-grade full-stack platform for deterministic code evaluation, bug detection, test-case generation, reasoning review, LLM-response evaluation, rubric scoring, dataset creation, and local benchmarking.

It is intentionally not a coding interview runner and not a sandbox. Submitted code is never executed. The system parses and inspects source text with rule-based static analysis only.

## Stack

- Frontend: Next.js, TypeScript, TailwindCSS, shadcn-style components, Zustand, Zod, Recharts, Monaco Editor
- Backend: FastAPI, Python, Pydantic, deterministic analysis engines
- Testing: Vitest, Playwright, Pytest
- Runtime: Docker Compose or local dev servers

## Local Development

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3000`. The API runs at `http://127.0.0.1:8000`.

## Docker

```bash
docker compose up --build
```

## Verification

```bash
cd backend
pytest
ruff check .
```

```bash
cd frontend
npm run test
npm run build
npm run test:e2e
```

## Safety Model

CodeJudge AI does not run uploaded code. It only performs parsing, pattern detection, AST inspection where supported, deterministic scoring, and heuristic confidence reporting.

