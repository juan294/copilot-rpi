# Copilot catalog crosswalk to cc-rpi 2.1.0

The [machine-readable crosswalk](upstream-catalog-crosswalk.json) accounts for all 40 Copilot error IDs, 55 Copilot rule IDs, 64 pinned upstream errors, and 92 active upstream rules. The upstream source is cc-rpi commit `aa3ea57fb26ae2e1e167acada4b769e073a417f4`, version 2.1.0. Copilot IDs and cc-rpi IDs are independent; an equal meaning does not renumber Copilot's catalog.

Each local row records its title, upstream meaning match, disposition, and reason. Each upstream row records the reverse link. `adopted` means the meaning is already present; `adapted` means Copilot wording or authority changed; `deferred` means no equivalent observed Copilot catalog item has yet earned a new permanent ID. Deferred upstream items remain visible for future review, including tool, platform, and domain cases. They are not silently discarded or declared fixed. The cc-rpi retired rule IDs 67, 69, and 80 are recorded separately and never reused here.

## Copilot decisions in this phase

- No Copilot error or rule ID is retired. The retirement ledger therefore remains empty for this version. Model improvement by itself is never evidence that a failure mode is fixed.
- Legacy Local prompt and chatmode cases retain their IDs through the optional compatibility profile. Native discovery and retirement need P2/P5 evidence.
- Rule 46 now inherits the interactive owner-selected model and effort. Scheduled jobs may record an owner-selected model; installation does not start inference.
- Rules 5, 9, 16, 29, 30, 33, 34, 45, and 53 use the local integration and remote authority contract. An authorized push is checked at its exact commit. A failed run is diagnosed locally; another remote action needs its own authorization.
- Rule 37 requires a disposition for every confirmed finding. A false positive needs evidence, and a strategic issue needs owner review. A recommendation remains a hypothesis under rule 55 and error 40.

## Future intake

A new upstream item requires a reviewed source identity and an explicit applicability decision. Add a new Copilot ID only for a distinct failure or rule that the product needs. Preserve existing IDs and add a versioned retirement ledger entry only after checking inbound references. The JSON crosswalk is the machine input for the upstream lock; the authored catalog files remain the local source of truth.
