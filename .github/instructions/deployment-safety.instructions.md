---
description: Apply when changing CI, infrastructure, deployment or release configuration.
applyTo: ".github/workflows/**,deploy/**,infrastructure/**,vercel.json,Dockerfile"
---

# Deployment safety

Inspect the project's actual branch, CI and deployment triggers before a remote action. Complete the applicable local gate and deployment preflight on the final candidate. Preserve each result with the candidate commit; a green check for another commit does not qualify this change.

Keep working branches local. Publish only the completed integration branch when authorized, and inspect every expected workflow at the exact pushed commit. Do not create a Vercel Preview for experimentation. If an integration push would trigger one, stop before pushing and use only a documented, non-destructive bypass.

Production deployment and remote configuration changes require explicit authorization. During an outage, follow the authorized rollback path first, then investigate using existing logs and local or authorized test environments. Do not publish a broken candidate to gather diagnostic evidence. A failed remote workflow remains failed even after a local repair.
