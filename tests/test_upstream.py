"""Provenance checks for the pinned, offline upstream intake."""

import json
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


if __name__ == "__main__":
    unittest.main()
