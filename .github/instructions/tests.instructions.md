---
description: Apply when writing or reviewing project tests and behavioral changes.
applyTo: "**/*.test.*,**/*.spec.*,**/test_*.py"
---

# Test conventions

Use Red-Green-Refactor for behavioral changes: write a failing test before editing implementation, then make the smallest change that passes it. A bug fix needs a regression case for the reported failure. A refactor needs existing behavior coverage.

Mock only external dependencies that the project does not own, such as a third-party API, clock or hardware. Exercise owned code through its real interface. A test assertion must be able to fail for a concrete incorrect behavior; avoid tautological registration-only checks.

Cover the relevant success, failure and recovery paths without mirroring the implementation. Run focused checks while editing, then every applicable required gate sequentially on the final candidate. Record each exit; a later pass cannot erase an earlier failure. For Python `test_*.py` files outside this path glob, attach this instruction by task relevance.
