"""Provenance checks for the pinned, offline upstream intake."""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-upstream.py"
LOCK = ROOT / "upstream/cc-rpi.lock.json"
INVENTORY = ROOT / "upstream/cc-rpi.inventory.json"


def run_check(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class UpstreamCheckerTests(unittest.TestCase):
    def test_offline_default_checks_every_recorded_item(self):
        result = run_check("--lock", LOCK, "--inventory", INVENTORY, "--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("61 components", result.stdout)
        inventory = json.loads(INVENTORY.read_text())
        self.assertEqual(len(inventory["links"]), 36)
        self.assertIn(
            "templates/references/handoff.md",
            {item["path"] for item in inventory["files"]},
        )

    def test_changed_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "upstream", temp / "upstream")
            snapshot = temp / "upstream/snapshots/templates/rules/testing.md"
            snapshot.write_bytes(snapshot.read_bytes() + b"\nchanged\n")
            result = run_check(
                "--lock", temp / "upstream/cc-rpi.lock.json",
                "--inventory", temp / "upstream/cc-rpi.inventory.json", "--check"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("snapshot hash mismatch", result.stdout)

    def test_unknown_upstream_component_needs_explicit_source_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "upstream/snapshots", temp / "source")
            manifest = temp / "source/templates/distribution.json"
            data = json.loads(manifest.read_text())
            data["components"].append({
                "id": "resource:new-item", "kind": "resource",
                "source": "templates/new-item.txt"
            })
            manifest.write_text(json.dumps(data))
            (temp / "source/templates/new-item.txt").write_text("new")
            offline = run_check("--lock", LOCK, "--inventory", INVENTORY, "--check")
            self.assertEqual(offline.returncode, 0, offline.stdout + offline.stderr)
            explicit = run_check(
                "--source", temp / "source", "--content-only", "--lock", LOCK,
                "--inventory", INVENTORY, "--check"
            )
            self.assertNotEqual(explicit.returncode, 0)
            self.assertIn("unknown upstream component: resource:new-item", explicit.stdout)

    def test_missing_disposition_and_duplicate_id_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "upstream", temp / "upstream")
            lock_path = temp / "upstream/cc-rpi.lock.json"
            lock = json.loads(lock_path.read_text())
            lock["components"][0]["disposition"] = ""
            lock["components"][0]["kind"] = "hook"
            lock["components"].append(lock["components"][1])
            lock_path.write_text(json.dumps(lock))
            result = run_check(
                "--lock", lock_path,
                "--inventory", temp / "upstream/cc-rpi.inventory.json", "--check"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid disposition", result.stdout)
            self.assertIn("component kind mismatch", result.stdout)
            self.assertIn("duplicate component id", result.stdout)

    def test_unlisted_snapshot_and_forged_manifest_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "upstream", temp / "upstream")
            (temp / "upstream/snapshots/extra.txt").write_text("unreviewed")
            result = run_check(
                "--lock", temp / "upstream/cc-rpi.lock.json",
                "--inventory", temp / "upstream/cc-rpi.inventory.json", "--check"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unlisted snapshot file: extra.txt", result.stdout)

            manifest = temp / "upstream/snapshots/templates/distribution.json"
            manifest.write_bytes(manifest.read_bytes() + b"\n")
            inventory_path = temp / "upstream/cc-rpi.inventory.json"
            inventory = json.loads(inventory_path.read_text())
            for item in inventory["files"]:
                if item["path"] == "templates/distribution.json":
                    import hashlib
                    item["sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
            inventory_path.write_text(json.dumps(inventory))
            forged = run_check(
                "--lock", temp / "upstream/cc-rpi.lock.json",
                "--inventory", inventory_path, "--check"
            )
            self.assertNotEqual(forged.returncode, 0)
            self.assertIn("pinned source anchor mismatch", forged.stdout)

    def test_changed_destination_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "upstream", temp / "upstream")
            lock_path = temp / "upstream/cc-rpi.lock.json"
            lock = json.loads(lock_path.read_text())
            item = lock["components"][0]
            item["disposition"] = "adapted"
            item["rationale"] = "Test destination verification."
            item["destination"] = "tests/test_upstream.py"
            item["destination_sha256"] = "0" * 64
            lock_path.write_text(json.dumps(lock))
            result = run_check(
                "--lock", lock_path,
                "--inventory", temp / "upstream/cc-rpi.inventory.json", "--check"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("destination hash mismatch", result.stdout)

    def test_explicit_source_detects_changed_file_and_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(ROOT / "upstream/snapshots", source)
            original = (source / "templates/rules/testing.md").read_bytes()
            (source / "templates/rules/testing.md").write_bytes(original + b"\nchanged\n")
            args = ("--source", source, "--content-only", "--lock", LOCK, "--inventory", INVENTORY, "--check")
            changed = run_check(*args)
            self.assertNotEqual(changed.returncode, 0)
            self.assertIn("upstream source hash drift: rule:testing", changed.stdout)
            (source / "templates/rules/testing.md").write_bytes(original)
            repaired = run_check(*args)
            self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
            self.assertIn("content-only", repaired.stdout)

    def test_explicit_source_requires_pinned_git_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(ROOT / "upstream/snapshots", source)
            result = run_check(
                "--source", source, "--lock", LOCK, "--inventory", INVENTORY, "--check"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("supplied source is not a Git checkout", result.stdout)

    def test_schema_requires_component_note_and_catalog_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "upstream", temp / "upstream")
            lock_path = temp / "upstream/cc-rpi.lock.json"
            lock = json.loads(lock_path.read_text())
            del lock["components"][0]["adaptation_note"]
            del lock["catalog"][0]["copilot_ids"]
            lock_path.write_text(json.dumps(lock))
            result = run_check(
                "--lock", lock_path,
                "--inventory", temp / "upstream/cc-rpi.inventory.json", "--check"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("schema violation: components[0].adaptation_note is required", result.stdout)
            self.assertIn("schema violation: catalog[0].copilot_ids is required", result.stdout)

    def test_symlinked_parent_cannot_escape_snapshot_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "upstream", temp / "upstream")
            rules = temp / "upstream/snapshots/templates/rules"
            shutil.rmtree(rules)
            rules.symlink_to(ROOT / "upstream/snapshots/templates/rules", target_is_directory=True)
            result = run_check(
                "--lock", temp / "upstream/cc-rpi.lock.json",
                "--inventory", temp / "upstream/cc-rpi.inventory.json", "--check"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink path component", result.stdout)

    def test_catalog_crosswalk_hash_and_mapping_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "upstream", temp / "upstream")
            lock_path = temp / "upstream/cc-rpi.lock.json"
            lock = json.loads(lock_path.read_text())
            lock["crosswalk"]["sha256"] = "0" * 64
            lock["catalog"][0]["copilot_ids"] = [999]
            lock_path.write_text(json.dumps(lock))
            result = run_check(
                "--lock", lock_path,
                "--inventory", temp / "upstream/cc-rpi.inventory.json", "--check"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("crosswalk hash mismatch", result.stdout)
            self.assertIn("crosswalk copilot_ids mismatch", result.stdout)

    def test_future_intake_requires_decisions_for_new_component_and_changed_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            source = temp / "source"
            shutil.copytree(ROOT / "upstream/snapshots", source)
            manifest = source / "templates/distribution.json"
            data = json.loads(manifest.read_text())
            data["components"].append({"id": "resource:future", "kind": "resource", "source": "templates/future.txt"})
            manifest.write_text(json.dumps(data))
            (source / "templates/future.txt").write_text("new")
            rules = source / "patterns/quick-reference.md"
            rules.write_text(rules.read_text().replace("1. ", "1. Revised ", 1))
            missing = run_check("--compare-source", source, "--content-only", "--check")
            self.assertNotEqual(0, missing.returncode)
            self.assertIn("new component resource:future", missing.stdout)
            self.assertIn("changed catalog rule:1", missing.stdout)
            self.assertIn("missing future intake decision", missing.stdout)
            decisions = temp / "decisions.json"
            change_hash = re.search(r"changes SHA256: ([0-9a-f]{64})", missing.stdout).group(1)
            decisions.write_text(json.dumps({"source_sha": "content-only", "changes_sha256": change_hash, "decisions": [
                {"id": "component:resource:future", "disposition": "deferred", "rationale": "Needs a Copilot adapter."},
                {"id": "component:resource:distribution-manifest", "disposition": "adapted", "rationale": "Review the manifest change."},
                {"id": "catalog:rule:1", "disposition": "adapted", "rationale": "Update the matching Copilot rule."},
            ]}))
            accepted = run_check("--compare-source", source, "--content-only", "--decisions", decisions, "--check")
            self.assertEqual(0, accepted.returncode, accepted.stdout)
            self.assertIn("3 future upstream differences have reviewed decisions", accepted.stdout)
            (source / "templates/future.txt").write_text("changed again")
            stale = run_check("--compare-source", source, "--content-only", "--decisions", decisions, "--check")
            self.assertNotEqual(0, stale.returncode)
            self.assertIn("decision source changed", stale.stdout)

    def test_future_intake_rejects_dirty_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(ROOT / "upstream/snapshots", source)
            subprocess.run(["git", "init", "-q", source], check=True)
            subprocess.run(["git", "-C", source, "add", "."], check=True)
            subprocess.run(["git", "-C", source, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "snapshot"], check=True)
            (source / "templates/distribution.json").write_text((source / "templates/distribution.json").read_text() + "\n")
            result = run_check("--compare-source", source, "--check")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("future source checkout is dirty", result.stdout)

    def test_future_intake_detects_resource_link_target_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(ROOT / "upstream/snapshots", source, symlinks=True)
            inventory = json.loads(INVENTORY.read_text())
            for record in inventory["links"]:
                path = source / record["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(record["target"])
            relative = inventory["links"][0]["path"]
            link = source / relative
            link.unlink()
            link.symlink_to("SKILL.md")
            result = run_check("--compare-source", source, "--content-only", "--check")
            self.assertNotEqual(0, result.returncode)
            self.assertIn(f"changed link {relative}", result.stdout)

    def test_future_intake_empty_diff_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(ROOT / "upstream/snapshots", source)
            result = run_check("--compare-source", source, "--content-only", "--check")
            self.assertEqual(0, result.returncode, result.stdout)
            self.assertIn("no upstream differences", result.stdout)


if __name__ == "__main__":
    unittest.main()
