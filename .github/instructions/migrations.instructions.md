---
description: Apply when creating, changing or testing database migrations.
applyTo: "**/migrations/**,**/prisma/migrations/**,**/db/migrate/**"
---

# Migration safety

Inspect the current schema, migration history, affected queries and data volume. Never edit an existing migration that has been applied; create a new migration using the project's naming convention. Choose types, constraints and indexes for actual queries and data. Use staged backfill for a new non-null constraint on existing data.

Run migrations and database tests locally against a disposable instance. Verify both forward application and rollback or a documented recovery path; some data changes cannot be reversed safely. Test RLS and privileges separately when applicable. Record expected duration and lock risk for large tables, using concurrent index or expand-contract techniques only when supported by the database.

Remote database application requires explicit authorization and an exact target. A local test or generated SQL is not evidence that a remote migration succeeded.
