# Test Strategy

This directory is reserved for repo-level contract, integration, e2e, visual, and performance suites that span more than one app or package.

Current Phase 3 and Phase 4 verification lives in:

- `apps/api/tests/test_contracts.py` for backend contract enforcement.
- `packages/contracts/src/index.test.ts` for TypeScript and Zod contract enforcement.
- `apps/api/tests` for existing backend tests.
- `apps/web/tests` and `apps/web/e2e` for existing web tests.

Future phases must add cross-service tests here when backend contracts, frontend clients, and analysis engines are wired together.
