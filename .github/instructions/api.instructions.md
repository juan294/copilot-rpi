---
description: Apply when changing API routes, handlers, controllers or response contracts.
applyTo: "**/api/**,**/routes/**,**/controllers/**"
---

# API contracts

Read the existing route conventions and consumers before changing a handler. Keep names, request types and response shapes consistent with the project's published contract. Search all callers and writers when a shared API schema changes.

Apply input validation at the boundary. Apply both authentication and authorization where the route requires them; a valid session does not imply access to every resource. Return stable error codes and useful recovery information without leaking stack traces, secrets or internal database details.

Test success, invalid input, denied access and downstream failure. For paginated endpoints, verify cursor or offset behavior against the actual data contract. Preserve idempotence and retry semantics for writes. Run the relevant local API and consumer checks before integration.
