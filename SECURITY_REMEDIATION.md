# Isolated security remediation status

This file records release blockers for the isolated remediation branch only.

## Confirmed
- The default branch contained a tracked SQLite database with a user credential hash and associated workspace record.
- Backend startup calls init_db() and the configured SQLite path defaults to ./trendly_ai.db.
- The local startup script changes into backend/ before launching Uvicorn, so the committed backend/trendly_ai.db matches the local development path.
- The repository security guidance says production should use PostgreSQL, but the current backend code has no PostgreSQL adapter.
- The production hosting project/build configuration is not available in the currently connected hosting account. Whether the public SQLite file is the live service's data source is therefore unverified.

## Branch-only actions
- Removed the committed SQLite file from this remediation branch.
- Added ignore rules for future local database files.
- Added a production configuration guard that rejects this SQLite-only backend when APP_ENV=production.
- Added tests for the production guard.

## Release blockers
Do not merge or deploy this branch until all of the following are complete:
1. Identify and verify the actual production hosting project, build root, runtime working directory, and configured environment.
2. Determine whether the exposed SQLite file is used by the deployed service.
3. If it is live data, migrate it securely to a managed persistent database without losing records; test persistence across restart/redeploy.
4. Add and test a supported managed-database adapter and schema migration.
5. Complete account credential/session remediation under a separately approved credential-rotation plan.
6. Review the complete diff and authorize any merge or deployment separately.

No production database was changed. No credential was rotated. No Git history was rewritten. The default branch remains unchanged; removal from this branch does not remove copies from existing Git history.
