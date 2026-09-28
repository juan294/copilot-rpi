# Review an upstream cc-rpi intake

`upstream/cc-rpi.lock.json` pins the reviewed cc-rpi source commit and maps
its components and catalog entries to Copilot dispositions. The inventory and
imported snapshots let the default check run offline. A passing default check
proves consistency with this pin; it does not discover newer upstream releases.
Copilot workflow bodies, native metadata and lifecycle adapters live in this
repository and have no runtime dependency on a sibling checkout.

Run the local consistency check during normal verification:

```bash
uv run --locked python scripts/check-upstream.py \
  --lock upstream/cc-rpi.lock.json \
  --inventory upstream/cc-rpi.inventory.json --check
```

For an explicit maintainer intake, supply an actual clean cc-rpi Git checkout
at the future source SHA. The root must be the checkout root and `git status
--porcelain --untracked-files=all` must be empty. The comparison reports
changed, new and removed components, catalog items and links against the
pinned map. It does not apply a change, create an issue or publish a branch.
Run the comparison first without decisions. For a real delta it exits nonzero
and prints the exact upstream SHA, changes SHA-256 and decision IDs:

```bash
uv run --locked python scripts/check-upstream.py \
  --compare-source "$cc_rpi_dir" --lock upstream/cc-rpi.lock.json \
  --inventory upstream/cc-rpi.inventory.json --check
```

Review each reported item by meaning. Write a JSON decision file whose top
level has `source_sha` equal to the printed Git SHA, `changes_sha256` equal to
the printed digest, and `decisions` containing one object per printed ID.
Each object has `id`, `disposition` (`adopted`, `adapted`, `deferred` or
`inapplicable`) and a nonempty `rationale`. The file must contain no stale
IDs. Then rerun against the same clean checkout:

```bash
uv run --locked python scripts/check-upstream.py \
  --compare-source "$cc_rpi_dir" --lock upstream/cc-rpi.lock.json \
  --inventory upstream/cc-rpi.inventory.json \
  --decisions "$decisions_file" --check
```

The checker rejects a changed SHA or digest, missing/duplicate decisions and
an invalid disposition. An unchanged future checkout is a no-op with no
decision file. Preserve Copilot rule and error IDs; upstream numbers are
separate identities. After adapting accepted items, update the pinned lock,
snapshots, destination hashes and affected Copilot code/docs, then run
`bash scripts/verify-local.sh` and review the candidate receipt. See the
[catalog crosswalk](upstream-catalog-crosswalk.md) and
[contribution rules](../CONTRIBUTING.md).
