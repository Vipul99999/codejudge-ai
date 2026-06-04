# Contributing

## Development Rules

- Do not add code execution for submitted programs.
- Keep analyzers deterministic and explainable.
- Include confidence, reason, and limitations for new evaluator outputs.
- Add focused tests for every new analysis rule or API endpoint.
- Keep frontend workflows dense, professional, and evaluator-oriented.

## Backend

Add new rules inside `backend/app/analysis/` and keep the FastAPI route thin. Prefer structured Pydantic models over free-form dictionaries.

## Frontend

Add new evaluator modules in `frontend/src/lib/modules.ts`, then wire payload handling in `frontend/src/app/page.tsx`. Use the existing UI primitives in `frontend/src/components/ui/`.

## Testing

Run backend and frontend tests before merging:

```bash
pytest backend
npm --prefix frontend run test
npm --prefix frontend run build
```

