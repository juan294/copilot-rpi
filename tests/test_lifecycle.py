"""Filesystem contract for the standalone Copilot lifecycle runtime."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

try:
    from .lifecycle_support import load_lifecycle, overlay_tree
except ImportError:  # unittest discover -s tests imports test modules at top level.
    from lifecycle_support import load_lifecycle, overlay_tree


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "templates/scripts/rpi-lifecycle.py"


def encoded_json(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


class LifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="copilot lifecycle ü ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / "package with spaces"
        self.target = self.root / "target ü"
        self.package.mkdir()
        self.target.mkdir()
        self.plan_path = self.root / "review.json"
        self.set_package(b"---\nname: hello\ndescription: Hello\n---\n\noriginal\nline two\nline three\nline four\nfooter\n")

    def set_package(self, content, authored=None, extra=()):
        destination = ".github/skills/hello/SKILL.md"
        file = self.package / destination
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
        record = {"path": destination, "component": "skill:hello", "sha256": hashlib.sha256(content).hexdigest()}
        if authored is not None:
            record["authored_sha256"] = authored
        receipt = {
            "schema_version": 1, "source_version": "1.0.0", "profile": "cli",
            "managed_root_bytes": 0,
            "files": [record, *extra],
            "preserved": [],
        }
        output = self.package / ".rpi/copilot-render.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(encoded_json(receipt))

    def run_cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(RUNTIME), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
        return json.loads(result.stdout) if result.stdout.strip().startswith("{") else result

    def plan(self, action="update", expected=0, **kwargs):
        cmd = ["detach" if action == "detach" else "plan", "--package", self.package,
               "--target", self.target, "--profile", "cli", "--output", self.plan_path]
        if action != "detach":
            cmd += ["--action", action]
        for key, value in kwargs.items():
            cmd += ["--" + key.replace("_", "-"), value]
        return self.run_cli(*cmd, expected=expected)

    def apply(self, expected=0):
        return self.run_cli("apply", "--plan", self.plan_path, expected=expected)

    def test_fresh_noop_update_detach_and_read_only_check(self):
        first = self.plan()
        self.assertEqual("ready", first["status"])
        self.assertIn("create", {item["action"] for item in first["actions"]})
        applied = self.apply()
        self.assertEqual("applied", applied["status"])
        self.assertTrue((self.target / ".rpi/copilot/manifest.json").is_file())
        self.assertFalse((self.target / ".rpi/manifest.json").exists())
        before = sorted((path.relative_to(self.target).as_posix(), path.read_bytes()) for path in self.target.rglob("*") if path.is_file())
        check = self.run_cli("check", "--package", self.package, "--target", self.target, "--profile", "cli")
        self.assertEqual("healthy", check["status"])
        after = sorted((path.relative_to(self.target).as_posix(), path.read_bytes()) for path in self.target.rglob("*") if path.is_file())
        self.assertEqual(before, after)
        self.plan_path.unlink()
        self.assertEqual("noop", self.plan()["status"])
        self.assertEqual("noop", self.apply()["status"])
        self.plan_path.unlink()
        self.assertEqual("ready", self.plan("detach")["status"])
        self.apply()
        self.assertFalse((self.target / ".github/skills/hello/SKILL.md").exists())

    def test_unknown_destination_conflicts_without_overwrite(self):
        destination = self.target / ".github/skills/hello/SKILL.md"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"owner")
        result = self.plan(expected=2)
        self.assertEqual("conflict", result["status"])
        self.assertEqual(b"owner", destination.read_bytes())
        self.assertIn("FIX", result["fix"])
        destination.unlink()
        self.plan_path.unlink()
        self.assertEqual("ready", self.plan()["status"])

    def test_stale_plan_refuses_and_replan_progresses(self):
        self.plan()
        owner = self.target / ".github/skills/hello/SKILL.md"
        owner.parent.mkdir(parents=True)
        owner.write_bytes(b"changed after plan")
        result = self.apply(expected=2)
        self.assertIn("BLOCKED / WHY", result.stderr)
        self.assertEqual(b"changed after plan", owner.read_bytes())
        owner.unlink()
        self.plan_path.unlink()
        self.assertEqual("ready", self.plan()["status"])
        self.apply()

    def test_rollback_preserves_newer_edit(self):
        self.plan()
        receipt = self.apply()
        destination = self.target / ".github/skills/hello/SKILL.md"
        destination.write_bytes(b"newer owner edit")
        result = self.run_cli("rollback", "--journal", receipt["journal"], expected=2)
        self.assertIn("BLOCKED / WHY", result.stderr)
        self.assertEqual(b"newer owner edit", destination.read_bytes())
        destination.write_bytes((self.package / ".github/skills/hello/SKILL.md").read_bytes())
        self.assertEqual("rolled-back", self.run_cli("rollback", "--journal", receipt["journal"])["status"])

    def test_clean_update_owner_only_edit_and_overlapping_edit(self):
        self.plan()
        self.apply()
        destination = self.target / ".github/skills/hello/SKILL.md"
        updated = destination.read_bytes().replace(b"original", b"upstream")
        self.set_package(updated)
        self.plan_path.unlink()
        self.assertIn("update", {item["action"] for item in self.plan()["actions"]})
        self.apply()
        self.assertEqual(updated, destination.read_bytes())
        destination.write_bytes(updated + b"\n# Owner note\n")
        self.plan_path.unlink()
        self.assertEqual("noop", self.plan()["status"])
        self.assertEqual(updated + b"\n# Owner note\n", destination.read_bytes())
        self.set_package(updated.replace(b"upstream", b"upstream-v2"))
        self.plan_path.unlink()
        result = self.plan(expected=0)
        self.assertEqual("ready", result["status"])
        self.apply()
        self.assertIn(b"upstream-v2", destination.read_bytes())
        self.assertIn(b"Owner note", destination.read_bytes())
        local = destination.read_bytes().replace(b"upstream-v2", b"owner rewrite")
        destination.write_bytes(local)
        self.set_package(updated.replace(b"upstream", b"upstream-v3"))
        self.plan_path.unlink()
        result = self.plan(expected=2)
        self.assertEqual("conflict", result["status"])
        self.assertEqual(local, destination.read_bytes())
        destination.write_bytes(updated.replace(b"upstream", b"upstream-v2") + b"\n# Owner note\n")
        self.plan_path.unlink()
        self.assertEqual("ready", self.plan()["status"])

    def install_with_retired_skill(self):
        retired = b"---\nname: process-errors\ndescription: Old\n---\n\nold maintenance skill\n"
        destination = ".github/skills/process-errors/SKILL.md"
        (self.package / destination).parent.mkdir(parents=True, exist_ok=True)
        (self.package / destination).write_bytes(retired)
        hello = (self.package / ".github/skills/hello/SKILL.md").read_bytes()
        self.set_package(hello, extra=[{"path": destination, "component": "skill:process-errors",
                                        "sha256": hashlib.sha256(retired).hexdigest()}])
        self.plan()
        self.apply()
        shutil.rmtree(self.package / ".github/skills/process-errors")
        self.set_package(hello)
        self.plan_path.unlink()
        return self.target / destination, retired

    def test_retired_component_needs_review_and_removes_only_unchanged_bytes(self):
        installed, retired = self.install_with_retired_skill()
        blocked = self.plan(expected=2)
        self.assertIn("absent from this package: skill:process-errors", blocked.stderr)
        self.assertIn("--retired-component skill:process-errors", blocked.stderr)
        self.assertEqual(retired, installed.read_bytes())
        self.assertFalse(self.plan_path.exists())
        result = self.plan(retired_component="skill:process-errors")
        self.assertEqual("ready", result["status"])
        self.assertIn({"destination": ".github/skills/process-errors/SKILL.md",
                       "component_id": "skill:process-errors", "action": "remove"}, result["actions"])
        self.apply()
        self.assertFalse(installed.exists())
        manifest = json.loads((self.target / ".rpi/copilot/manifest.json").read_text())
        self.assertNotIn("skill:process-errors", {entry["component_id"] for entry in manifest["entries"]})
        self.plan_path.unlink()
        self.assertEqual("noop", self.plan()["status"])

    def test_retired_component_keeps_owner_edited_bytes(self):
        installed, retired = self.install_with_retired_skill()
        edited = retired + b"\n# Owner note\n"
        installed.write_bytes(edited)
        result = self.plan(retired_component="skill:process-errors")
        self.assertEqual("ready", result["status"])
        self.assertIn({"destination": ".github/skills/process-errors/SKILL.md",
                       "component_id": "skill:process-errors",
                       "reason": "modified owned content retained on removal"}, result["retained"])
        self.apply()
        self.assertEqual(edited, installed.read_bytes())

    def test_retirement_fix_keeps_command_and_flags(self):
        self.install_with_retired_skill()
        blocked = self.plan(expected=2, component="skill:hello")
        self.assertIn("plan --package", blocked.stderr)
        self.assertIn("--component skill:hello", blocked.stderr)
        self.assertIn("--retired-component skill:process-errors", blocked.stderr)
        detach = self.run_cli("detach", "--package", self.package, "--target", self.target,
                              "--profile", "cli", "--output", self.plan_path, expected=2)
        fix = detach.stderr.partition("FIX:")[2]
        self.assertIn("rpi-lifecycle.py detach --package", fix)
        self.assertNotIn(" plan ", fix)
        self.assertIn("--retired-component skill:process-errors", fix)

    def test_invalid_retired_component_is_named_and_dropped_from_fix(self):
        self.install_with_retired_skill()
        for bogus, reason in (("skill:bogus", "names no recorded component: skill:bogus"),
                              ("skill:hello", "names a component still in this package: skill:hello")):
            with self.subTest(bogus=bogus):
                result = self.run_cli("plan", "--package", self.package, "--target", self.target, "--profile", "cli",
                                      "--output", self.plan_path, "--retired-component", bogus,
                                      "--retired-component", "skill:process-errors", expected=2)
                why, _, fix = result.stderr.partition("FIX:")
                self.assertIn(reason, why)
                self.assertNotIn(bogus, fix)
                self.assertIn("--retired-component skill:process-errors", fix)

    def test_deleted_retired_file_is_not_reported_as_retained(self):
        installed, _ = self.install_with_retired_skill()
        installed.unlink()
        result = self.plan(retired_component="skill:process-errors")
        self.assertEqual("ready", result["status"])
        self.assertEqual([], [item for item in result["retained"] if "process-errors" in item["destination"]])
        self.assertEqual([], [item for item in result["actions"] if "process-errors" in item["destination"]])

    def test_detach_with_other_profile_package_names_the_profile(self):
        self.plan()
        self.apply()
        receipt_path = self.package / ".rpi/copilot-render.json"
        receipt = json.loads(receipt_path.read_text())
        prompt = b"---\nname: hello\ndescription: Hello\n---\n\nprompt\n"
        (self.package / ".github/prompts").mkdir(parents=True)
        (self.package / ".github/prompts/hello.prompt.md").write_bytes(prompt)
        receipt["profile"] = "vscode-local"
        receipt["files"] = [{"path": ".github/prompts/hello.prompt.md", "component": "prompt:hello",
                             "sha256": hashlib.sha256(prompt).hexdigest()}]
        receipt_path.write_bytes(encoded_json(receipt))
        self.plan_path.unlink()
        result = self.run_cli("detach", "--package", self.package, "--target", self.target,
                              "--profile", "vscode-local", "--output", self.plan_path, expected=2)
        self.assertIn("recorded profile cli differs from package profile vscode-local", result.stderr)
        self.assertNotIn("--retired-component", result.stderr)

    def test_interrupted_apply_requires_rollback_then_replan(self):
        self.plan()
        result = self.run_cli("apply", "--plan", self.plan_path, "--fail-after", "1", expected=2)
        self.assertIn("rollback --journal", result.stderr)
        journals = list((self.target / ".rpi/local/copilot/transactions").glob("*/journal.json"))
        self.assertEqual(1, len(journals))
        blocked = self.run_cli("check", "--package", self.package, "--target", self.target, expected=2)
        self.assertIn("rollback --journal", blocked.stderr)
        self.assertEqual("rolled-back", self.run_cli("rollback", "--journal", journals[0])["status"])
        self.plan_path.unlink()
        self.assertEqual("ready", self.plan()["status"])
        self.apply()

    def test_exact_existing_bytes_need_explicit_review(self):
        destination = self.target / ".github/skills/hello/SKILL.md"
        destination.parent.mkdir(parents=True)
        original = (self.package / ".github/skills/hello/SKILL.md").read_bytes()
        destination.write_bytes(original)
        self.assertEqual("conflict", self.plan(expected=2)["status"])
        self.assertEqual(original, destination.read_bytes())
        self.plan_path.unlink()
        self.assertEqual("ready", self.plan(adopt_exact="skill:hello")["status"])
        self.apply()
        state = json.loads((self.target / ".rpi/copilot/manifest.json").read_text())
        self.assertEqual("skill:hello", state["entries"][0]["component_id"])

    def test_jsonc_capability_preserves_comments_and_unrelated_fields(self):
        settings = self.target / ".vscode/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_bytes(b'{\n  // owner comment\n  "editor.fontSize": 15,\n  "owner.literal": "literal,}", // owner trailing comment\n}\n')
        self.assertEqual("ready", self.plan(capability="vscode-settings", allow_capabilities="vscode-settings")["status"])
        self.apply()
        data = settings.read_bytes()
        self.assertIn(b"// owner comment", data)
        self.assertIn(b'"editor.fontSize": 15', data)
        self.assertIn(b'"owner.literal": "literal,}"', data)
        self.assertIn(b"// owner trailing comment", data)
        self.assertIn(b'"chat.useAgentsMdFile": true', data)
        healthy = self.run_cli("check", "--package", self.package, "--target", self.target, "--profile", "cli")
        self.assertEqual("healthy", healthy["status"])
        self.plan_path.unlink()
        self.plan("detach")
        self.apply()
        data = settings.read_bytes()
        self.assertIn(b"// owner comment", data)
        self.assertIn(b'"editor.fontSize": 15', data)
        self.assertIn(b'"owner.literal": "literal,}"', data)
        self.assertNotIn(b'"chat.useAgentsMdFile"', data)

    def test_rendered_package_runs_without_pyyaml(self):
        rendered = self.root / "standalone package"
        result = subprocess.run([sys.executable, str(ROOT / "templates/scripts/rpi-distribution.py"),
                                 "render", "--source", str(ROOT), "--profile", "cli", "--target", str(rendered)],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        runtime = rendered / ".rpi/copilot/runtime/rpi-distribution.py"
        self.assertTrue(runtime.is_file())
        for name in (
            "rpi-lifecycle.py", "rpi-config.py", "rpi-candidate.py",
            "rpi-verify.py", "validate-findings.py", "rpi-hook.py",
            "rpi-prepush.py", "rpi-automation.py",
        ):
            self.assertTrue((rendered / ".rpi/copilot/runtime" / name).is_file(), name)
        automation = rendered / ".rpi/copilot/runtime/rpi-automation.py"
        preview = subprocess.run(
            [sys.executable, "-S", str(automation), "schedule-preview", "--job", "triage",
             "--project", str(self.target)], capture_output=True, text=True,
        )
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        self.assertIn(str(automation.resolve()), preview.stdout)
        self.assertNotIn("morning-triage.sh", preview.stdout)
        standalone_plan = self.root / "standalone-plan.json"
        result = subprocess.run([sys.executable, "-S", str(runtime), "plan", "--package", str(rendered),
                                 "--target", str(self.target), "--profile", "cli", "--output", str(standalone_plan)],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(standalone_plan.is_file())

    def test_check_reports_inactive_owned_setting_without_rewriting_it(self):
        self.plan(capability="vscode-settings", allow_capabilities="vscode-settings")
        self.apply()
        settings = self.target / ".vscode/settings.json"
        owner = settings.read_bytes().replace(b"true", b"false")
        settings.write_bytes(owner)
        result = self.run_cli("check", "--package", self.package, "--target", self.target,
                              "--profile", "cli", expected=2)
        self.assertEqual("action-needed", result["status"])
        self.assertTrue(any(item.get("in_effect") is False for item in result["retained"]))
        self.assertEqual(owner, settings.read_bytes())

    def test_receipt_cannot_activate_mcp_without_capability_route(self):
        active = self.package / ".github/mcp.json"
        active.parent.mkdir(parents=True, exist_ok=True)
        active.write_bytes(b'{"mcpServers":{"unsafe":{}}}\n')
        receipt_path = self.package / ".rpi/copilot-render.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["files"].append({"path": ".github/mcp.json", "component": "example:cli-mcp",
                                 "sha256": hashlib.sha256(active.read_bytes()).hexdigest()})
        receipt_path.write_bytes(encoded_json(receipt))
        result = self.plan(expected=2)
        self.assertIn("undeclared active or capability destination", result.stderr)
        self.assertFalse((self.target / ".github/mcp.json").exists())
        receipt["files"].pop()
        receipt_path.write_bytes(encoded_json(receipt))
        self.assertEqual("ready", self.plan()["status"])

    def test_damaged_baseline_and_malformed_manifest_refuse_without_writes(self):
        self.plan()
        self.apply()
        destination = self.target / ".github/skills/hello/SKILL.md"
        original = destination.read_bytes()
        state = self.target / ".rpi/copilot/manifest.json"
        valid_manifest = state.read_bytes()
        state.write_bytes(b'{"schema_version":1,"ownership":"copilot-rpi","entries":[null]}')
        self.plan_path.unlink()
        refused = self.plan(expected=2)
        self.assertIn("BLOCKED / WHY", refused.stderr)
        self.assertIn("FIX", refused.stderr)
        self.assertEqual(original, destination.read_bytes())
        state.write_bytes(valid_manifest)
        manifest = json.loads(valid_manifest)
        baseline = self.target / ".rpi/copilot/baselines" / manifest["entries"][0]["base_hash"]
        saved_baseline = baseline.read_bytes()
        baseline.unlink()
        refused = self.plan(expected=2)
        self.assertEqual("conflict", refused["status"])
        self.assertEqual(original, destination.read_bytes())
        baseline.write_bytes(saved_baseline)
        self.plan_path.unlink()
        self.assertEqual("noop", self.plan()["status"])

    def test_symlinked_legacy_directory_cannot_hide_command_collision(self):
        outside = self.root / "owner-prompts"
        outside.mkdir()
        (outside / "hello.prompt.md").write_bytes(b"---\nname: hello\n---\n\nowner\n")
        github = self.target / ".github"
        github.mkdir()
        (github / "prompts").symlink_to(outside, target_is_directory=True)
        result = self.plan(expected=2)
        self.assertIn("symlinked legacy surface directory", result.stderr)
        self.assertFalse((self.target / ".github/skills/hello/SKILL.md").exists())
        (github / "prompts").unlink()
        self.assertEqual("ready", self.plan()["status"])

    def test_legacy_prompt_metadata_name_collision_is_reported(self):
        prompt = self.target / ".github/prompts/team.prompt.md"
        prompt.parent.mkdir(parents=True)
        owner = b"---\nname: hello\ndescription: owner\n---\n\nowner command\n"
        prompt.write_bytes(owner)
        self.assertEqual("conflict", self.plan(expected=2)["status"])
        self.assertEqual(owner, prompt.read_bytes())
        prompt.write_bytes(owner.replace(b"name: hello", b"name: team"))
        self.plan_path.unlink()
        self.assertEqual("ready", self.plan()["status"])

    def test_symlinked_transaction_directory_refuses_before_planning(self):
        outside = self.root / "outside-journal"
        outside.mkdir()
        transactions = self.target / ".rpi/local/copilot/transactions"
        transactions.mkdir(parents=True)
        (transactions / "fake").symlink_to(outside, target_is_directory=True)
        refused = self.plan(expected=2)
        self.assertIn("symlinked transaction directory", refused.stderr)
        self.assertFalse((self.target / ".github/skills/hello/SKILL.md").exists())
        (transactions / "fake").unlink()
        self.assertEqual("ready", self.plan()["status"])


    def manifest(self):
        return json.loads((self.target / ".rpi/copilot/manifest.json").read_text())

    def test_manifest_copies_authored_hash_and_a_missing_hash_stays_healthy(self):
        content = (self.package / ".github/skills/hello/SKILL.md").read_bytes()
        self.set_package(content, authored=hashlib.sha256(content).hexdigest())
        self.plan()
        self.apply()
        entry = self.manifest()["entries"][0]
        self.assertEqual(hashlib.sha256(content).hexdigest(), entry["authored_sha256"])
        state = self.manifest()
        del state["entries"][0]["authored_sha256"]
        (self.target / ".rpi/copilot/manifest.json").write_bytes(encoded_json(state))
        healthy = self.run_cli("check", "--package", self.package, "--target", self.target, "--profile", "cli")
        self.assertEqual("healthy", healthy["status"])
        self.plan_path.unlink()
        self.assertEqual("noop", self.plan()["status"])
        self.assertNotIn("authored_sha256", self.manifest()["entries"][0])
        updated = content.replace(b"original", b"upstream")
        self.set_package(updated, authored=hashlib.sha256(updated).hexdigest())
        self.plan_path.unlink()
        self.assertEqual("ready", self.plan()["status"])
        self.apply()
        self.assertEqual(hashlib.sha256(updated).hexdigest(), self.manifest()["entries"][0]["authored_sha256"])

    def test_malformed_authored_hash_is_rejected_in_receipt_and_manifest(self):
        content = (self.package / ".github/skills/hello/SKILL.md").read_bytes()
        good = hashlib.sha256(content).hexdigest()
        for bad in ("A" * 64, good[:12], 7):
            self.set_package(content, authored=bad)
            refused = self.plan(expected=2)
            self.assertIn("invalid package file record", refused.stderr)
            self.assertFalse((self.target / ".github/skills/hello/SKILL.md").exists())
        resource = self.package / ".github/skills/hello/notes.md"
        resource.write_bytes(b"notes\n")
        self.set_package(content, authored=good, extra=[{
            "path": ".github/skills/hello/notes.md", "component": "skill:hello",
            "sha256": hashlib.sha256(b"notes\n").hexdigest(), "authored_sha256": good}])
        self.assertIn("invalid package file record", self.plan(expected=2).stderr)
        self.set_package(content, authored=good)
        self.assertEqual("ready", self.plan()["status"])
        self.apply()
        manifest_path = self.target / ".rpi/copilot/manifest.json"
        valid = manifest_path.read_bytes()
        for bad in ("g" * 64, good.upper(), None):
            state = json.loads(valid)
            state["entries"][0]["authored_sha256"] = bad
            manifest_path.write_bytes(encoded_json(state))
            refused = self.run_cli("check", "--package", self.package, "--target", self.target, expected=2)
            self.assertIn("invalid Copilot ownership entry", refused.stderr)
        manifest_path.write_bytes(valid)
        self.assertEqual("healthy", self.run_cli("check", "--package", self.package, "--target", self.target)["status"])

    def test_reserved_project_and_state_destinations_are_refused(self):
        content = (self.package / ".github/skills/hello/SKILL.md").read_bytes()
        for reserved in (".rpi/project/x.md", ".RPI/Project/x.md", ".rpi/project", ".rpi/Copilot/manifest.json",
                         ".Rpi/Local/Copilot/lock"):
            data = b"reserved\n"
            path = self.package / reserved
            if not path.is_dir():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            self.set_package(content, extra=[{"path": reserved, "component": "skill:hello",
                                              "sha256": hashlib.sha256(data).hexdigest()}])
            refused = self.plan(expected=2)
            self.assertIn("package cannot own project or Copilot state: " + reserved, refused.stderr)
            self.assertFalse((self.target / ".rpi/project").exists())
        module = load_lifecycle()
        for reserved in (".rpi/project", ".RPI/PROJECT/a/b.md", ".rpi/copilot", ".rpi/local/copilot/x"):
            with self.assertRaisesRegex(ValueError, "package cannot own project or Copilot state"):
                module.safe_relative(reserved)
        for allowed in (".rpi/projects/x.md", ".github/skills/project/SKILL.md", ".rpi/local/other"):
            self.assertEqual(allowed, module.safe_relative(allowed))
        self.set_package(content)
        self.assertEqual("ready", self.plan()["status"])

    def test_lifecycle_operations_leave_project_overlays_byte_identical(self):
        project = self.target / ".rpi/project"
        (project / "nested").mkdir(parents=True)
        (project / "rpi-plan.md").write_bytes(b"<!-- rpi-overlay: skill=rpi-plan; written-against=000000000000 -->\r\n# Plan\n")
        (project / "nested/notes.md").write_bytes(b"owner notes\n")
        (project / "rpi-research.md").symlink_to("nested/notes.md")
        (project / "nested/dangling.md").symlink_to("../../missing-overlay.md")
        before = overlay_tree(project)
        self.plan("install")
        self.assertEqual(before, overlay_tree(project))
        applied = self.apply()
        self.assertEqual(before, overlay_tree(project))
        self.assertEqual("healthy", self.run_cli("check", "--package", self.package, "--target", self.target)["status"])
        self.assertEqual(before, overlay_tree(project))
        self.assertEqual("rolled-back", self.run_cli("rollback", "--journal", applied["journal"])["status"])
        self.assertEqual(before, overlay_tree(project))
        self.plan_path.unlink()
        self.plan()
        self.apply()
        self.plan_path.unlink()
        self.assertEqual("ready", self.plan("detach")["status"])
        self.assertEqual(before, overlay_tree(project))
        self.apply()
        self.assertFalse((self.target / ".github/skills/hello/SKILL.md").exists())
        self.assertEqual(before, overlay_tree(project))


if __name__ == "__main__":
    unittest.main()
