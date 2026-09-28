"""Native Copilot distribution rendering and metadata controls."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "templates/scripts/rpi-distribution.py"


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def fixture(root):
    write(
        root / "templates/skills/rpi-test/SKILL.md",
        "---\nname: rpi-test\ndescription: Test a portable workflow.\n---\n\n"
        "# Test\n\nRead [guide](references/guide.md).\n",
    )
    write(root / "templates/skills/rpi-test/references/guide.md", "# Guide\n")
    write(
        root / "templates/github/agents/auditor.agent.md",
        "---\nname: auditor\ndescription: Review findings.\n"
        "tools: [read, search]\ninclude-custom-instructions: true\n---\n\n# Audit\n",
    )
    write(
        root / "templates/github/instructions/tests.instructions.md.template",
        '---\napplyTo: "**/tests/**"\ndescription: Test discipline.\n---\n\n# Tests\n',
    )
    write(root / "templates/AGENTS.md.template", "# Managed root\n")
    write(root / "templates/github/copilot-instructions.md.template", "# Managed Copilot\n")
    write(
        root / "templates/adapters/copilot.json",
        json.dumps({
            "schema_version": 1,
            "profiles": {
                "cli": {"skills": True, "prompts": False},
                "agent-host": {"skills": True, "prompts": False},
                "vscode-local": {"skills": False, "prompts": True},
            },
            "tool_aliases": ["read", "search", "edit", "execute", "agent", "web", "todo"],
        }),
    )
    manifest = {
        "schema_version": 1,
        "version": "1.18.0",
        "root_budget_bytes": 8192,
        "adapter": "templates/adapters/copilot.json",
        "profiles": {
            "cli": {"description": "Copilot CLI"},
            "agent-host": {"description": "VS Code Agent Host"},
            "vscode-local": {"description": "VS Code Local compatibility"},
        },
        "self_application": {
            "profile": "cli",
            "preserve": ["root:agents"],
            "legacy_active": [".github/prompts/old.prompt.md"],
        },
        "components": [
            {
                "id": "skill:rpi-test", "kind": "skill",
                "source": "templates/skills/rpi-test",
                "destination": ".github/skills/rpi-test",
                "profiles": ["cli", "agent-host"],
                "resources": ["references/guide.md"], "former_paths": [".github/prompts/test.prompt.md"],
            },
            {
                "id": "prompt:rpi-test", "kind": "prompt",
                "source": "templates/skills/rpi-test",
                "destination": ".github/prompts/rpi-test.prompt.md",
                "profiles": ["vscode-local"],
                "resources": [], "former_paths": [],
            },
            {
                "id": "agent:auditor", "kind": "agent",
                "source": "templates/github/agents/auditor.agent.md",
                "destination": ".github/agents/auditor.agent.md",
                "profiles": ["cli", "agent-host", "vscode-local"],
                "resources": [], "former_paths": [".github/chatmodes/old.chatmode.md"],
            },
            {
                "id": "instruction:tests", "kind": "instruction",
                "source": "templates/github/instructions/tests.instructions.md.template",
                "destination": ".github/instructions/tests.instructions.md",
                "profiles": ["cli", "agent-host", "vscode-local"],
                "resources": [], "former_paths": [],
            },
            {
                "id": "root:agents", "kind": "root",
                "source": "templates/AGENTS.md.template", "destination": "AGENTS.md",
                "profiles": ["cli", "agent-host", "vscode-local"],
                "resources": [], "former_paths": [],
            },
            {
                "id": "root:copilot", "kind": "root",
                "source": "templates/github/copilot-instructions.md.template",
                "destination": ".github/copilot-instructions.md",
                "profiles": ["cli", "agent-host", "vscode-local"],
                "resources": [], "former_paths": [],
            },
        ],
    }
    write(root / "templates/distribution.json", json.dumps(manifest, indent=2) + "\n")
    return manifest


def invoke(root, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--source", str(root)],
        capture_output=True, text=True, check=False,
    )


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.manifest = fixture(self.root)

    def save_manifest(self):
        write(self.root / "templates/distribution.json", json.dumps(self.manifest, indent=2) + "\n")

    def assert_rejected(self, expected):
        result = invoke(self.root, "validate")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(expected, result.stdout + result.stderr)

    def test_two_profile_renders_are_byte_identical_and_manifested(self):
        for name in ("one", "two"):
            target = Path(self.temp.name) / name
            result = invoke(self.root, "render", "--profile", "cli", "--target", str(target))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        first = Path(self.temp.name) / "one"
        second = Path(self.temp.name) / "two"
        left = {p.relative_to(first).as_posix(): p.read_bytes() for p in first.rglob("*") if p.is_file()}
        right = {p.relative_to(second).as_posix(): p.read_bytes() for p in second.rglob("*") if p.is_file()}
        self.assertEqual(left, right)
        self.assertIn(".github/skills/rpi-test/SKILL.md", left)
        self.assertIn(".rpi/copilot-render.json", left)
        self.assertNotIn(".github/prompts/rpi-test.prompt.md", left)
        self.assertNotIn(b"$ARGUMENTS", b"".join(left.values()))

    def test_rendered_package_verifies_with_stdlib_only(self):
        package = Path(self.temp.name) / "package"
        result = invoke(self.root, "render", "--profile", "cli", "--target", str(package))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        isolated = Path(self.temp.name) / "isolated"
        shutil.copytree(package, isolated)
        probe = subprocess.run(
            [
                sys.executable, "-S", "-c",
                "import hashlib,json,pathlib,sys; "
                "root=pathlib.Path(sys.argv[1]); "
                "receipt=json.loads((root/'.rpi/copilot-render.json').read_text()); "
                "assert receipt['profile']=='cli'; "
                "assert all(hashlib.sha256((root/item['path']).read_bytes()).hexdigest()==item['sha256'] "
                "for item in receipt['files'])",
                str(isolated),
            ],
            cwd=isolated,
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(probe.returncode, 0, probe.stdout + probe.stderr)

    def test_local_profile_uses_agent_prompt_without_skill_collision(self):
        target = Path(self.temp.name) / "local"
        result = invoke(self.root, "render", "--profile", "vscode-local", "--target", str(target))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        prompt = (target / ".github/prompts/rpi-test.prompt.md").read_text()
        self.assertIn("agent: agent", prompt)
        self.assertNotIn("mode:", prompt)
        self.assertIn("rpi-test/references/guide.md", prompt)
        self.assertEqual((target / ".github/prompts/rpi-test/references/guide.md").read_text(), "# Guide\n")
        self.assertFalse((target / ".github/skills/rpi-test").exists())

    def test_local_rejects_skill_prompt_name_collision(self):
        self.manifest["components"][0]["profiles"].append("vscode-local")
        self.save_manifest()
        self.assert_rejected("profile kind mismatch")

    def test_adapter_rejects_known_profile_with_wrong_kind(self):
        self.manifest["components"][0]["profiles"] = ["vscode-local"]
        self.manifest["components"][1]["profiles"] = ["cli"]
        self.save_manifest()
        self.assert_rejected("profile kind mismatch")

    def test_local_resource_paths_with_shared_suffix_remain_distinct(self):
        skill = self.root / "templates/skills/rpi-test/SKILL.md"
        skill.write_text(skill.read_text() + "Read [short](guide.md).\n")
        write(self.root / "templates/skills/rpi-test/guide.md", "# Short\n")
        self.manifest["components"][0]["resources"].append("guide.md")
        self.save_manifest()
        target = Path(self.temp.name) / "local-overlap"
        result = invoke(self.root, "render", "--profile", "vscode-local", "--target", str(target))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        prompt = (target / ".github/prompts/rpi-test.prompt.md").read_text()
        self.assertIn("[guide](rpi-test/references/guide.md)", prompt)
        self.assertIn("[short](rpi-test/guide.md)", prompt)

    def test_duplicate_yaml_key_and_unsupported_metadata_fail(self):
        skill = self.root / "templates/skills/rpi-test/SKILL.md"
        skill.write_text(skill.read_text().replace("description: Test", "description: First\ndescription: Test"))
        self.assert_rejected("duplicate YAML key")
        skill.write_text(skill.read_text().replace("description: First\n", ""))
        agent = self.root / "templates/github/agents/auditor.agent.md"
        agent.write_text(agent.read_text().replace("tools:", "unknown-field: true\ntools:"))
        self.assert_rejected("unsupported metadata")

    def test_unhashable_yaml_key_has_attributed_diagnostic(self):
        skill = self.root / "templates/skills/rpi-test/SKILL.md"
        original = skill.read_text()
        skill.write_text(original.replace("description: Test a portable workflow.", "description: Test a portable workflow.\n? [a, b]\n: value"))
        result = invoke(self.root, "validate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SKILL.md", result.stdout)
        self.assertIn("BLOCKED:", result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        skill.write_text(original)
        self.assertEqual(invoke(self.root, "validate").returncode, 0)

    def test_missing_resource_and_unlinked_resource_fail(self):
        (self.root / "templates/skills/rpi-test/references/guide.md").unlink()
        self.assert_rejected("missing resource")
        write(self.root / "templates/skills/rpi-test/references/guide.md", "# Guide\n")
        skill = self.root / "templates/skills/rpi-test/SKILL.md"
        skill.write_text(skill.read_text().replace("[guide](references/guide.md)", "the guide"))
        self.assert_rejected("unlinked resource")

    def test_path_escape_and_symlink_are_rejected(self):
        self.manifest["components"][0]["destination"] = "../outside"
        self.save_manifest()
        self.assert_rejected("unsafe destination")
        self.manifest["components"][0]["destination"] = ".github/skills/rpi-test"
        self.save_manifest()
        resource = self.root / "templates/skills/rpi-test/references/guide.md"
        resource.unlink()
        resource.symlink_to(self.root / "templates/AGENTS.md.template")
        self.assert_rejected("symlink")

    def test_native_destination_must_match_component_kind(self):
        self.manifest["components"][0]["destination"] = ".claude/skills/rpi-test"
        self.save_manifest()
        self.assert_rejected("invalid native destination")

    def test_duplicate_name_and_wrong_profile_are_rejected(self):
        duplicate = dict(self.manifest["components"][0])
        duplicate["id"] = "skill:another"
        self.manifest["components"].append(duplicate)
        self.save_manifest()
        self.assert_rejected("collision")
        self.manifest["components"].pop()
        self.save_manifest()
        result = invoke(self.root, "render", "--profile", "unknown", "--target", str(Path(self.temp.name) / "out"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown profile", result.stdout + result.stderr)

    def test_duplicate_agent_display_name_is_rejected(self):
        write(
            self.root / "templates/github/agents/second.agent.md",
            "---\nname: auditor\ndescription: Another reviewer.\ntools: [read]\n---\n\n# Second\n",
        )
        self.manifest["components"].append({
            "id": "agent:second", "kind": "agent",
            "source": "templates/github/agents/second.agent.md",
            "destination": ".github/agents/second.agent.md",
            "profiles": ["cli", "agent-host", "vscode-local"],
            "resources": [], "former_paths": [],
        })
        self.save_manifest()
        self.assert_rejected("agent name collision")

    def test_model_pin_and_tool_omission_are_rejected(self):
        agent = self.root / "templates/github/agents/auditor.agent.md"
        agent.write_text(agent.read_text().replace("tools: [read, search]", "model: paid-model\ntools: [read, search]"))
        self.assert_rejected("model pin")
        agent.write_text(agent.read_text().replace("model: paid-model\ntools: [read, search]", ""))
        self.assert_rejected("missing tools")
        agent.write_text(agent.read_text().replace("description: Review findings.", "description: Review findings.\ntools: []"))
        result = invoke(self.root, "validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_adapter_metadata_is_required_and_checked(self):
        adapter = self.root / "templates/adapters/copilot.json"
        data = json.loads(adapter.read_text())
        data["profiles"]["vscode-local"]["prompts"] = False
        adapter.write_text(json.dumps(data))
        self.assert_rejected("adapter profile mismatch")

    def test_optional_mcp_example_is_inert_and_validated(self):
        source = "templates/vscode-mcp.json.template"
        write(self.root / source, json.dumps({"inputs": [], "servers": {}}))
        self.manifest["components"].append({
            "id": "example:vscode-mcp", "kind": "example", "source": source,
            "destination": ".vscode/mcp.example.json", "profiles": ["vscode-local"],
            "resources": [], "former_paths": [], "optional": True,
        })
        self.save_manifest()
        target = Path(self.temp.name) / "examples"
        default = invoke(self.root, "render", "--profile", "vscode-local", "--target", str(target))
        self.assertEqual(default.returncode, 0, default.stdout + default.stderr)
        self.assertFalse((target / ".vscode/mcp.example.json").exists())
        selected_target = Path(self.temp.name) / "selected-examples"
        selected = invoke(
            self.root, "render", "--profile", "vscode-local", "--target", str(selected_target), "--include-examples"
        )
        self.assertEqual(selected.returncode, 0, selected.stdout + selected.stderr)
        self.assertTrue((selected_target / ".vscode/mcp.example.json").exists())
        self.assertFalse((selected_target / ".vscode/mcp.json").exists())
        write(self.root / source, "{bad json")
        self.assert_rejected("invalid example JSON")

    def test_root_budget_and_unknown_active_surface_fail(self):
        write(self.root / "templates/AGENTS.md.template", "x" * 8193)
        self.assert_rejected("root budget")
        write(self.root / "templates/AGENTS.md.template", "# Managed root\n")
        write(self.root / ".github/skills/rogue/SKILL.md", "---\nname: rogue\ndescription: Rogue.\n---\n")
        self.assert_rejected("undeclared active surface")

    def test_undeclared_authored_skill_and_extra_active_resource_fail(self):
        write(
            self.root / "templates/skills/rogue/SKILL.md",
            "---\nname: rogue\ndescription: Hidden authored skill.\n---\n\n# Rogue\n",
        )
        self.assert_rejected("undeclared authored skill")
        (self.root / "templates/skills/rogue/SKILL.md").unlink()
        (self.root / "templates/skills/rogue").rmdir()
        rendered = invoke(self.root, "render", "--profile", "cli", "--target", str(self.root))
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        write(self.root / ".github/skills/rpi-test/rogue.sh", "echo rogue\n")
        self.assert_rejected("undeclared active surface")

    def test_undeclared_authored_agent_fails(self):
        write(
            self.root / "templates/github/agents/rogue.agent.md",
            "---\ndescription: Hidden agent.\ntools: [read]\n---\n\n# Rogue\n",
        )
        self.assert_rejected("undeclared authored agent")

    def test_self_application_rejects_other_profile_active_prompt(self):
        write(
            self.root / ".github/prompts/rpi-test.prompt.md",
            "---\nname: rpi-test\nagent: agent\n---\n\n# Local only\n",
        )
        self.assert_rejected("undeclared active surface")

    def test_legacy_chatmode_and_prompt_report_migration_without_deletion(self):
        write(self.root / ".github/chatmodes/old.chatmode.md", "---\ndescription: Old role.\n---\n\n# Old role\n")
        write(self.root / ".github/prompts/old.prompt.md", "---\nmode: agent\ndescription: Old prompt.\n---\n\n# Old prompt\n")
        result = invoke(self.root, "validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("migration", result.stdout)
        self.assertIn("observed active root", result.stdout)
        self.assertTrue((self.root / ".github/chatmodes/old.chatmode.md").exists())
        write(self.root / ".github/chatmodes/rogue.chatmode.md", "---\ndescription: Rogue.\n---\n")
        self.assert_rejected("undeclared legacy chatmode")
        (self.root / ".github/chatmodes/rogue.chatmode.md").unlink()
        self.assertEqual(invoke(self.root, "validate").returncode, 0)

    def test_legacy_prompt_without_description_is_rejected(self):
        write(self.root / ".github/prompts/old.prompt.md", "---\nmode: agent\n---\n\n# Old prompt\n")
        self.assert_rejected("missing legacy prompt description")
        write(
            self.root / ".github/prompts/old.prompt.md",
            "---\nmode: agent\ndescription: Restored.\n---\n\n# Old prompt\n",
        )
        self.assertEqual(invoke(self.root, "validate").returncode, 0)

    def test_two_legacy_prompts_with_same_name_collide(self):
        self.manifest["self_application"]["legacy_active"].append(".github/prompts/another.prompt.md")
        self.save_manifest()
        for filename in ("old.prompt.md", "another.prompt.md"):
            write(
                self.root / ".github/prompts" / filename,
                "---\nname: same-command\nmode: agent\ndescription: Old.\n---\n\n# Old\n",
            )
        self.assert_rejected("active command name collision")

    def test_check_generated_detects_drift_and_recovers(self):
        write(self.root / "AGENTS.md", "# Owner-specific guidance\n")
        result = invoke(self.root, "render", "--profile", "cli", "--target", str(self.root))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / "AGENTS.md").read_text(), "# Owner-specific guidance\n")
        receipt = json.loads((self.root / ".rpi/copilot-render.json").read_text())
        self.assertIn("AGENTS.md", receipt["preserved"])
        self.assertEqual(invoke(self.root, "check-generated", "--profile", "cli").returncode, 0)
        active = self.root / ".github/agents/auditor.agent.md"
        active.write_text(active.read_text() + "changed\n")
        drift = invoke(self.root, "check-generated", "--profile", "cli")
        self.assertNotEqual(drift.returncode, 0)
        self.assertIn("generated drift", drift.stdout)

    def test_check_generated_rejects_tampered_or_missing_receipt(self):
        rendered = invoke(self.root, "render", "--profile", "cli", "--target", str(self.root))
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        receipt_path = self.root / ".rpi/copilot-render.json"
        original = receipt_path.read_bytes()
        receipt = json.loads(original)
        receipt["files"][0]["sha256"] = "0" * 64
        receipt_path.write_text(json.dumps(receipt))
        tampered = invoke(self.root, "check-generated", "--profile", "cli")
        self.assertNotEqual(tampered.returncode, 0)
        self.assertIn("render receipt drift", tampered.stdout)
        receipt_path.unlink()
        missing = invoke(self.root, "check-generated", "--profile", "cli")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("render receipt drift", missing.stdout)
        receipt_path.write_bytes(original)
        self.assertEqual(invoke(self.root, "check-generated", "--profile", "cli").returncode, 0)

    def test_active_agent_duplicate_yaml_key_fails_validate(self):
        rendered = invoke(self.root, "render", "--profile", "cli", "--target", str(self.root))
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        active = self.root / ".github/agents/auditor.agent.md"
        active.write_text(active.read_text().replace("tools: [read, search]", "tools: [read]\ntools: [search]"))
        self.assert_rejected("duplicate YAML key")

    def test_legacy_prompt_and_active_skill_name_collision_fails(self):
        self.manifest["self_application"]["legacy_active"].append(".github/prompts/rpi-test.prompt.md")
        self.save_manifest()
        rendered = invoke(self.root, "render", "--profile", "cli", "--target", str(self.root))
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        write(
            self.root / ".github/prompts/rpi-test.prompt.md",
            "---\nname: rpi-test\ndescription: Old prompt.\nmode: agent\n---\n\n# Old\n",
        )
        self.assert_rejected("active command name collision")

    def test_self_application_preserves_skill_until_legacy_prompt_retirement(self):
        self.manifest["self_application"]["preserve"].append("skill:rpi-test")
        self.manifest["self_application"]["legacy_active"].append(".github/prompts/rpi-test.prompt.md")
        self.save_manifest()
        write(
            self.root / ".github/prompts/rpi-test.prompt.md",
            "---\nname: rpi-test\ndescription: Old prompt.\nmode: agent\n---\n\n# Old\n",
        )
        rendered = invoke(self.root, "render", "--profile", "cli", "--target", str(self.root))
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        self.assertFalse((self.root / ".github/skills/rpi-test/SKILL.md").exists())
        self.assertEqual(invoke(self.root, "validate").returncode, 0)

    def test_mixed_profile_render_target_is_rejected_without_mutation(self):
        target = Path(self.temp.name) / "shared-target"
        first = invoke(self.root, "render", "--profile", "cli", "--target", str(target))
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        before = (target / ".rpi/copilot-render.json").read_bytes()
        mixed = invoke(self.root, "render", "--profile", "vscode-local", "--target", str(target))
        self.assertNotEqual(mixed.returncode, 0)
        self.assertIn("nonempty staging target", mixed.stdout)
        self.assertEqual((target / ".rpi/copilot-render.json").read_bytes(), before)
        self.assertFalse((target / ".github/prompts/rpi-test.prompt.md").exists())
        corrected = invoke(
            self.root, "render", "--profile", "vscode-local",
            "--target", str(Path(self.temp.name) / "local-target"),
        )
        self.assertEqual(corrected.returncode, 0, corrected.stdout + corrected.stderr)


if __name__ == "__main__":
    unittest.main()
