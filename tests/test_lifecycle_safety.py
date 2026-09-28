"""Independent filesystem safety fixtures for the public Copilot lifecycle CLI."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "templates/scripts/rpi-distribution.py"
SKILL_PATH = ".github/skills/hello/SKILL.md"
AGENT_PATH = ".github/agents/helper.agent.md"
SKILL = b"---\nname: hello\ndescription: Hello.\n---\n\n# Hello\n"
AGENT = b"---\nname: Helper\ndescription: Help.\ntools: [read]\n---\n\n# Help\n"


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def invoke(*args):
    return subprocess.run(
        [sys.executable, str(CLI), *(str(arg) for arg in args)],
        text=True, capture_output=True, check=False,
    )


def result_json(result):
    return json.loads(result.stdout) if result.stdout.lstrip().startswith("{") else None


def tree_snapshot(root):
    """Capture file bytes and stat identity; a read-only check must preserve both."""
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()
    }


class LifecycleSafetyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="copilot safety ü ")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.target = self.base / "owner project with spaces ü"
        self.package = self.base / "reviewed package ü"
        self.target.mkdir()
        self.package.mkdir()
        subprocess.run(["git", "init", "-q", str(self.target)], check=True, capture_output=True)
        self.files = {SKILL_PATH: ("skill:hello", SKILL), AGENT_PATH: ("agent:helper", AGENT)}
        self.write_package()
        self.plan_number = 0

    def write_package(self):
        records = []
        for path, (component, data) in sorted(self.files.items()):
            write(self.package / path, data)
            records.append({"path": path, "component": component, "sha256": hashlib.sha256(data).hexdigest()})
        receipt = {
            "schema_version": 1, "source_version": "1.0.0", "profile": "cli",
            "managed_root_bytes": 0, "files": records, "preserved": [],
        }
        write(self.package / ".rpi/copilot-render.json", (json.dumps(receipt, indent=2) + "\n").encode())

    def plan(self, *extra, detach=False):
        self.plan_number += 1
        output = self.base / f"review {self.plan_number}.json"
        command = "detach" if detach else "plan"
        result = invoke(command, "--package", self.package, "--target", self.target,
                        "--profile", "cli", "--output", output, *extra)
        payload = json.loads(output.read_text()) if output.is_file() else None
        return result, payload, output

    def apply(self, output, *extra):
        return invoke("apply", "--plan", output, *extra)

    def assert_blocked(self, result):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        message = result.stdout + result.stderr
        self.assertTrue("FIX" in message or "fix" in message, message)

    def test_stale_plan_preserves_owner_bytes_then_replan_succeeds(self):
        planned, preview, output = self.plan()
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertEqual(preview["status"], "ready")
        destination = self.target / SKILL_PATH
        write(destination, b"owner edit after review\n")
        before = tree_snapshot(self.target)
        refused = self.apply(output)
        self.assert_blocked(refused)
        self.assertIn("new plan", refused.stdout + refused.stderr)
        self.assertEqual(tree_snapshot(self.target), before)
        destination.unlink()
        replanned, ready, replacement = self.plan()
        self.assertEqual(replanned.returncode, 0, replanned.stdout + replanned.stderr)
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(self.apply(replacement).returncode, 0)
        self.assertEqual(destination.read_bytes(), SKILL)

    def test_equal_existing_bytes_require_reviewed_adoption(self):
        destination = self.target / SKILL_PATH
        write(destination, SKILL)
        original = destination.read_bytes()
        refused, preview, output = self.plan()
        self.assert_blocked(refused)
        self.assertEqual(preview["status"], "conflict")
        self.assertIn(SKILL_PATH, json.dumps(preview["conflicts"]))
        self.assertEqual(destination.read_bytes(), original)
        self.assertFalse((self.target / ".rpi/copilot/manifest.json").exists())
        self.assert_blocked(self.apply(output))
        self.assertEqual(destination.read_bytes(), original)
        reviewed, ready, replacement = self.plan("--adopt-exact", "skill:hello")
        self.assertEqual(reviewed.returncode, 0, reviewed.stdout + reviewed.stderr)
        self.assertFalse(ready["conflicts"])
        self.assertEqual(self.apply(replacement).returncode, 0)
        manifest = json.loads((self.target / ".rpi/copilot/manifest.json").read_text())
        self.assertIn(SKILL_PATH, {item["destination"] for item in manifest["entries"]})
        self.assertEqual(destination.read_bytes(), original)

    def test_symlinked_manifest_refuses_without_following_it(self):
        outside = self.base / "owner manifest.json"
        write(outside, b'{"owner":"outside"}\n')
        manifest = self.target / ".rpi/copilot/manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.symlink_to(outside)
        refused, _, _ = self.plan()
        self.assert_blocked(refused)
        self.assertEqual(outside.read_bytes(), b'{"owner":"outside"}\n')
        self.assertTrue(manifest.is_symlink())
        manifest.unlink()
        replanned, ready, output = self.plan()
        self.assertEqual(replanned.returncode, 0, replanned.stdout + replanned.stderr)
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(self.apply(output).returncode, 0)

    def test_malformed_manifest_entry_has_recovery_diagnostic(self):
        manifest = self.target / ".rpi/copilot/manifest.json"
        malformed = b'{"schema_version":1,"ownership":"copilot-rpi","entries":[null]}\n'
        write(manifest, malformed)
        refused, _, _ = self.plan()
        self.assert_blocked(refused)
        self.assertIn("BLOCKED", refused.stdout + refused.stderr)
        self.assertEqual(manifest.read_bytes(), malformed)
        self.assertFalse((self.target / SKILL_PATH).exists())
        manifest.unlink()
        repaired, preview, output = self.plan()
        self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
        self.assertEqual(preview["status"], "ready")
        self.assertEqual(self.apply(output).returncode, 0)

    def test_forged_manifest_entry_cannot_claim_unrelated_skill(self):
        planned, _, output = self.plan()
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertEqual(self.apply(output).returncode, 0)
        manifest = self.target / ".rpi/copilot/manifest.json"
        document = json.loads(manifest.read_text())
        forged_path = ".github/skills/custom/SKILL.md"
        # Matching the forged baseline makes an untrusted entry destructive.
        owner_bytes = SKILL
        write(self.target / forged_path, owner_bytes)
        document["entries"].append({
            "destination": forged_path, "component_id": "skill:hello",
            "base_hash": document["entries"][0]["base_hash"], "status": "clean",
        })
        manifest.write_text(json.dumps(document))
        before = tree_snapshot(self.target)
        refused, _, _ = self.plan(detach=True)
        self.assert_blocked(refused)
        self.assertEqual(tree_snapshot(self.target), before)
        self.assertEqual((self.target / forged_path).read_bytes(), owner_bytes)
        document["entries"] = [entry for entry in document["entries"]
                               if entry["destination"] != forged_path]
        manifest.write_text(json.dumps(document))
        repaired, _, _ = self.plan(detach=True)
        self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)

    def test_forged_configuration_record_cannot_claim_owner_setting(self):
        settings = self.target / ".vscode/settings.json"
        write(settings, b'{\n  "editor.fontSize": 15\n}\n')
        planned, _, output = self.plan("--capability", "vscode-settings",
                                       "--allow-capabilities", "vscode-settings")
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertEqual(self.apply(output).returncode, 0)
        manifest = self.target / ".rpi/copilot/manifest.json"
        document = json.loads(manifest.read_text())
        self.assertTrue(document["config_entries"])
        forged = {
            "destination": ".vscode/settings.json",
            "base_hash": document["config_entries"][0]["base_hash"],
            "record": {"id": "vscode.owner-font", "pointer": ["editor.fontSize"],
                       "mode": "value", "value": 15},
        }
        document["config_entries"].append(forged)
        manifest.write_text(json.dumps(document))
        before = tree_snapshot(self.target)
        refused, _, _ = self.plan(detach=True)
        self.assert_blocked(refused)
        self.assertEqual(tree_snapshot(self.target), before)
        self.assertIn(b'"editor.fontSize": 15', settings.read_bytes())
        document["config_entries"].remove(forged)
        manifest.write_text(json.dumps(document))
        repaired, _, _ = self.plan(detach=True)
        self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)

    def test_symlinked_destination_parent_and_package_escape_refuse(self):
        outside = self.base / "outside skills"
        outside.mkdir()
        write(outside / "sentinel", b"owner bytes\n")
        link = self.target / ".github/skills"
        link.parent.mkdir(parents=True)
        link.symlink_to(outside, target_is_directory=True)
        refused, _, _ = self.plan()
        self.assert_blocked(refused)
        self.assertEqual((outside / "sentinel").read_bytes(), b"owner bytes\n")
        self.assertFalse((outside / "hello/SKILL.md").exists())
        link.unlink()

        receipt = self.package / ".rpi/copilot-render.json"
        original_receipt = receipt.read_bytes()
        value = json.loads(original_receipt)
        value["files"][0]["path"] = "../outside"
        receipt.write_text(json.dumps(value))
        escape, _, _ = self.plan()
        self.assert_blocked(escape)
        self.assertEqual((outside / "sentinel").read_bytes(), b"owner bytes\n")
        receipt.write_bytes(original_receipt)
        repaired, ready, output = self.plan()
        self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(self.apply(output).returncode, 0)

    def test_interrupted_transaction_rolls_back_then_replans(self):
        planned, _, output = self.plan()
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        interrupted = self.apply(output, "--fail-after", "1")
        self.assert_blocked(interrupted)
        self.assertIn("rollback --journal", interrupted.stdout + interrupted.stderr)
        journals = list((self.target / ".rpi/local/copilot/transactions").glob("*/journal.json"))
        self.assertEqual(len(journals), 1)
        self.assertEqual(json.loads(journals[0].read_text())["status"], "applying")
        before = tree_snapshot(self.target)
        blocked, _, _ = self.plan()
        self.assert_blocked(blocked)
        self.assertEqual(tree_snapshot(self.target), before)
        rollback = invoke("rollback", "--journal", journals[0])
        self.assertEqual(rollback.returncode, 0, rollback.stdout + rollback.stderr)
        self.assertFalse((self.target / SKILL_PATH).exists())
        self.assertFalse((self.target / AGENT_PATH).exists())
        replanned, ready, replacement = self.plan()
        self.assertEqual(replanned.returncode, 0, replanned.stdout + replanned.stderr)
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(self.apply(replacement).returncode, 0)

    def test_rollback_refuses_newer_edit_then_restores_exact_postimage(self):
        planned, _, output = self.plan()
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        applied = self.apply(output)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        journal = result_json(applied)["journal"]
        destination = self.target / SKILL_PATH
        write(destination, b"newer owner edit\n")
        before = tree_snapshot(self.target)
        refused = invoke("rollback", "--journal", journal)
        self.assert_blocked(refused)
        self.assertEqual(tree_snapshot(self.target), before)
        write(destination, SKILL)
        restored = invoke("rollback", "--journal", journal)
        self.assertEqual(restored.returncode, 0, restored.stdout + restored.stderr)
        self.assertFalse(destination.exists())

    def test_detach_and_re_adopt_preserve_owner_file(self):
        owner = self.target / "docs/notes ü.md"
        write(owner, "Owner research ü\n".encode())
        planned, _, output = self.plan()
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertEqual(self.apply(output).returncode, 0)
        detached, preview, removal = self.plan(detach=True)
        self.assertEqual(detached.returncode, 0, detached.stdout + detached.stderr)
        self.assertEqual(preview["status"], "ready")
        self.assertEqual(self.apply(removal).returncode, 0)
        self.assertFalse((self.target / SKILL_PATH).exists())
        self.assertFalse((self.target / AGENT_PATH).exists())
        self.assertEqual(owner.read_bytes(), "Owner research ü\n".encode())
        renewed, ready, replacement = self.plan()
        self.assertEqual(renewed.returncode, 0, renewed.stdout + renewed.stderr)
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(self.apply(replacement).returncode, 0)
        self.assertEqual(owner.read_bytes(), "Owner research ü\n".encode())

    def test_check_is_read_only_before_and_after_install(self):
        before = tree_snapshot(self.target)
        needed = invoke("check", "--package", self.package, "--target", self.target, "--profile", "cli")
        self.assertEqual(needed.returncode, 2, needed.stdout + needed.stderr)
        self.assertEqual(result_json(needed)["status"], "action-needed")
        self.assertEqual(tree_snapshot(self.target), before)
        planned, _, output = self.plan()
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertEqual(self.apply(output).returncode, 0)
        installed = tree_snapshot(self.target)
        healthy = invoke("check", "--package", self.package, "--target", self.target, "--profile", "cli")
        self.assertEqual(healthy.returncode, 0, healthy.stdout + healthy.stderr)
        self.assertEqual(result_json(healthy)["status"], "healthy")
        self.assertEqual(tree_snapshot(self.target), installed)

    def test_edited_owned_capability_is_inactive_without_losing_owner_bytes(self):
        settings = self.target / ".vscode/settings.json"
        write(settings, b'{\n  // team setting\n  "editor.fontSize": 15,\n}\n')
        planned, preview, output = self.plan("--capability", "vscode-settings",
                                             "--allow-capabilities", "vscode-settings")
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertEqual(preview["status"], "ready")
        self.assertEqual(self.apply(output).returncode, 0)
        modified = settings.read_bytes().replace(b'"chat.useAgentsMdFile": true',
                                                 b'"chat.useAgentsMdFile": false')
        self.assertIn(b'"chat.useAgentsMdFile": false', modified)
        settings.write_bytes(modified)
        before = tree_snapshot(self.target)
        inactive = invoke("check", "--package", self.package, "--target", self.target,
                          "--profile", "cli")
        self.assertEqual(inactive.returncode, 2, inactive.stdout + inactive.stderr)
        report = result_json(inactive)
        self.assertEqual(report["status"], "action-needed")
        self.assertIn("vscode.agents-md", json.dumps(report["retained"]))
        self.assertEqual(tree_snapshot(self.target), before)
        settings.write_bytes(modified.replace(b'"chat.useAgentsMdFile": false',
                                              b'"chat.useAgentsMdFile": true'))
        healthy = invoke("check", "--package", self.package, "--target", self.target,
                         "--profile", "cli")
        self.assertEqual(healthy.returncode, 0, healthy.stdout + healthy.stderr)
        self.assertEqual(result_json(healthy)["status"], "healthy")

    def test_active_mcp_and_hook_receipt_entries_are_rejected(self):
        receipt = self.package / ".rpi/copilot-render.json"
        original_receipt = receipt.read_bytes()
        for path, component, data in (
            (".github/mcp.json", "example:cli-mcp", b'{"mcpServers":{}}\n'),
            (".github/hooks/hooks.json", "example:hooks", b'{"hooks":[]}\n'),
        ):
            with self.subTest(path=path):
                write(self.package / path, data)
                record = json.loads(original_receipt)
                record["files"].append({"path": path, "component": component,
                                        "sha256": hashlib.sha256(data).hexdigest()})
                receipt.write_text(json.dumps(record))
                before = tree_snapshot(self.target)
                refused, _, _ = self.plan()
                self.assert_blocked(refused)
                self.assertEqual(tree_snapshot(self.target), before)
                self.assertFalse((self.target / path).exists())
                receipt.write_bytes(original_receipt)
                (self.package / path).unlink()

        inert = ".github/mcp.example.json"
        content = b'{"mcpServers":{}}\n'
        write(self.package / inert, content)
        record = json.loads(original_receipt)
        record["files"].append({"path": inert, "component": "example:cli-mcp",
                                "sha256": hashlib.sha256(content).hexdigest()})
        receipt.write_text(json.dumps(record))
        repaired, preview, output = self.plan()
        self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
        self.assertEqual(preview["status"], "ready")
        self.assertEqual(self.apply(output).returncode, 0)
        self.assertEqual((self.target / inert).read_bytes(), content)
        self.assertFalse((self.target / ".github/mcp.json").exists())

    def test_jsonc_trailing_comma_and_inline_comment_survive_owned_key(self):
        settings = self.target / ".vscode/settings.json"
        original = b'{\n  "editor.fontSize": 15, // owner trailing comment\n}\n'
        write(settings, original)
        planned, preview, output = self.plan("--capability", "vscode-settings",
                                             "--allow-capabilities", "vscode-settings")
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertEqual(preview["status"], "ready")
        self.assertEqual(self.apply(output).returncode, 0)
        added = settings.read_bytes()
        self.assertIn(b"// owner trailing comment", added)
        self.assertIn(b'"editor.fontSize": 15,', added)
        self.assertIn(b'"chat.useAgentsMdFile": true', added)
        healthy = invoke("check", "--package", self.package, "--target", self.target,
                         "--profile", "cli")
        self.assertEqual(healthy.returncode, 0, healthy.stdout + healthy.stderr)
        self.assertEqual(result_json(healthy)["status"], "healthy")
        detached, _, removal = self.plan(detach=True)
        self.assertEqual(detached.returncode, 0, detached.stdout + detached.stderr)
        self.assertEqual(self.apply(removal).returncode, 0)
        restored = settings.read_bytes()
        self.assertIn(b"// owner trailing comment", restored)
        self.assertIn(b'"editor.fontSize": 15', restored)
        self.assertNotIn(b'"chat.useAgentsMdFile"', restored)

    def test_two_new_jsonc_keys_produce_valid_object(self):
        source = ROOT / "templates/scripts/rpi-config.py"
        spec = importlib.util.spec_from_file_location("safety_rpi_config", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = b'{\n  // owner comment\n}\n'
        changed = module.patch_top_level_jsonc(original, {}, {"first": True, "second": 2})
        self.assertEqual(module.jsonc_loads(changed), {"first": True, "second": 2})
        self.assertIn(b"// owner comment", changed)

    def test_symlinked_legacy_prompt_directory_cannot_hide_command_collision(self):
        outside = self.base / "owner prompt directory"
        prompt = outside / "hello.prompt.md"
        write(prompt, b"---\nagent: agent\ndescription: Existing Hello command.\n---\n\n# Hello\n")
        link = self.target / ".github/prompts"
        link.parent.mkdir(parents=True)
        link.symlink_to(outside, target_is_directory=True)
        original = prompt.read_bytes()
        refused, _, _ = self.plan()
        self.assert_blocked(refused)
        self.assertEqual(prompt.read_bytes(), original)
        self.assertTrue(link.is_symlink())
        self.assertFalse((self.target / SKILL_PATH).exists())
        link.unlink()
        repaired, preview, output = self.plan()
        self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
        self.assertEqual(preview["status"], "ready")
        self.assertEqual(self.apply(output).returncode, 0)
        self.assertEqual(prompt.read_bytes(), original)

    def test_nested_legacy_prompt_cannot_hide_command_collision(self):
        prompt = self.target / ".github/prompts/custom/hello.prompt.md"
        owner_bytes = b"---\nname: hello\ndescription: Owner command.\n---\n\n# Hello\n"
        write(prompt, owner_bytes)
        before = tree_snapshot(self.target)
        refused, _, _ = self.plan()
        self.assert_blocked(refused)
        self.assertEqual(tree_snapshot(self.target), before)
        self.assertEqual(prompt.read_bytes(), owner_bytes)
        prompt.unlink()
        repaired, ready, output = self.plan()
        self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(self.apply(output).returncode, 0)


if __name__ == "__main__":
    unittest.main()
