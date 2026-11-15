---
description: Apply before starting, reusing, stopping or removing local stacks, containers, volumes, networks, task services or database tests.
applyTo: "**/Dockerfile*,**/compose*.yml,**/compose*.yaml,**/docker-compose*,supabase/**"
---

# Local resource lifecycle

Apply this before any local stack, container, volume, network, task service or database test, including in a repository without a Dockerfile. Use the project's documented lifecycle commands and its resource contract linked from AGENTS.md. This instruction grants no deletion authority.

Prove ownership before allocation. Classify each environment as disposable (task fixtures with approved disposal), reusable (kept until an explicit finish) or persistent/recovery (protected data). Unknown existing resources are protected; a name, age, stopped state or missing worktree does not prove a resource is disposable. Verify the actual Docker context, project identity and workdir, and record the task, class, exact identities and intended teardown before you start. Keep that record outside any directory that cleanup will remove, and never record credentials. Give concurrently mutable tasks unique project identities: a Git worktree alone does not isolate a database. Delegation briefs name the resource scope and teardown obligation; the coordinator accounts for resources left by interrupted delegates.

Finish the owned lifecycle. Re-inspect the same daemon, identities and consumers before removal, and remove only resources inside the approved scope. A replacement with the same name is not the recorded resource. Never use host-wide prune commands, `supabase stop --all` or prefix and age matching as task teardown. `down --volumes`, `docker volume rm` and Supabase `stop --no-backup` delete data; use them only in an ownership-verified, authorized disposable lifecycle.

Before reporting completion or removing a task worktree, report each resource as removed, retained (with reason, owner and next review or finish action) or cleanup failed (with the remaining identities). A passing test with failed teardown is not a complete lifecycle. Preserve shared, reusable and recovery data.
