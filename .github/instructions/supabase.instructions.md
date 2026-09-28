---
description: Apply to Supabase schema, SQL, Auth and data-access changes when this domain is selected.
applyTo: "supabase/**,**/*.sql"
---

# Supabase data access

Inspect the current schema, role grants, RLS policies and application queries before a change. Privilege and RLS are separate controls: a policy cannot grant table privilege, and a broad grant does not replace row filtering. Grant only the access the product requires. Do not assume public tables need anonymous SELECT.

Test migrations locally with the project's Supabase CLI and a disposable database. Exercise allowed and denied reads and writes as the relevant roles, plus failure and recovery cases. Verify fallback logs and health checks against actual data access; connectivity alone does not prove tables are usable.

A remote `supabase db push`, Auth change or data mutation requires explicit authorization for the target project. Do not treat local tests as a remote-success receipt. Preserve existing applied migrations and recovery evidence.
