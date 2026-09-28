"""Contracts for authored Copilot Agent Host and CLI template sources."""

import json
import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
AGENTS = TEMPLATES / "github" / "agents"
INSTRUCTIONS = TEMPLATES / "github" / "instructions"
KNOWN_TOOLS = {"read", "search", "edit", "execute", "agent", "web", "todo"}


def frontmatter(path: Path) -> tuple[dict, str]:
    source = path.read_text()
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", source, re.DOTALL)
    if not match:
        raise AssertionError(f"missing YAML frontmatter: {path}")
    return yaml.safe_load(match.group(1)), match.group(2)


class NativeTemplateContracts(unittest.TestCase):
    def test_three_native_roles_have_explicit_narrow_tools(self):
        expected = {
            "rpi-research": {"read", "search"},
            "rpi-planner": {"read", "search", "edit"},
            "rpi-auditor": {"read", "search"},
        }
        files = {path.stem.removesuffix(".agent"): path for path in AGENTS.glob("*.agent.md")}
        self.assertEqual(set(expected), set(files))
        for name, tools in expected.items():
            with self.subTest(role=name):
                metadata, body = frontmatter(files[name])
                self.assertEqual(set(metadata["tools"]), tools)
                self.assertLessEqual(set(metadata["tools"]), KNOWN_TOOLS)
                self.assertTrue(metadata["include-custom-instructions"])
                self.assertFalse(metadata.get("disable-model-invocation", False))
                self.assertTrue(metadata["user-invocable"])
                self.assertTrue(metadata["description"])
                self.assertNotIn("model", metadata)
                self.assertNotIn("infer", metadata)
                self.assertNotIn("*", metadata["tools"])
                self.assertTrue(body.strip())

    def test_read_only_roles_return_evidence_for_parent_to_write(self):
        for name in ("rpi-research", "rpi-auditor"):
            metadata, body = frontmatter(AGENTS / f"{name}.agent.md")
            self.assertFalse({"edit", "execute", "agent"} & set(metadata["tools"]))
            self.assertIn("parent", body.lower())
            self.assertIn("file:line", body)
        research = (AGENTS / "rpi-research.agent.md").read_text().lower()
        self.assertIn("descriptive", research)
        self.assertIn("rpi-assess", research)

    def test_scoped_instructions_preserve_domain_contracts(self):
        required = {
            "tests": ("red", "mock only", "sequential"),
            "api": ("validation", "authorization", "error"),
            "migrations": ("existing migration", "rollback", "data"),
            "deployment-safety": ("local", "preview", "authorization"),
            "supabase": ("rls", "privilege", "local"),
        }
        files = {path.name.removesuffix(".instructions.md.template"): path for path in
                 INSTRUCTIONS.glob("*.instructions.md.template")}
        self.assertEqual(set(required), set(files))
        for name, clauses in required.items():
            with self.subTest(instruction=name):
                metadata, body = frontmatter(files[name])
                self.assertTrue(metadata["description"])
                self.assertTrue(metadata["applyTo"])
                self.assertNotEqual("**", metadata["applyTo"])
                self.assertNotIn("{", metadata["applyTo"])
                for clause in clauses:
                    self.assertIn(clause, body.lower())

    def test_always_loaded_roots_are_small_and_complementary(self):
        agents = (TEMPLATES / "AGENTS.md.template").read_text()
        copilot = (TEMPLATES / "github" / "copilot-instructions.md.template").read_text()
        self.assertLessEqual(len((agents + copilot).encode()), 8192)
        self.assertIn("rpi-implement", agents)
        self.assertIn("AGENTS.md", copilot)
        self.assertIn(".github/skills/", copilot)
        self.assertNotIn("~60%", agents + copilot)
        self.assertNotIn("~95%", agents + copilot)
        self.assertNotIn("git push", agents + copilot)
        self.assertNotIn("@copilot", agents + copilot)

    def test_settings_and_mcp_examples_are_explicit_and_inert(self):
        settings = json.loads((TEMPLATES / "vscode-settings.json.template").read_text())
        self.assertEqual(settings, {"chat.useAgentsMdFile": True})
        self.assertNotIn("github.copilot.chat.agent.thinkingTool", settings)
        self.assertNotIn("github.copilot.chat.agent.autoFix", settings)
        vscode = json.loads((TEMPLATES / "vscode-mcp.json.template").read_text())
        cli = json.loads((TEMPLATES / "copilot-cli-mcp.json.template").read_text())
        self.assertEqual(set(vscode), {"inputs", "servers"})
        self.assertEqual(set(cli), {"mcpServers"})
        self.assertEqual(len(vscode["servers"]), 1)
        self.assertEqual(len(cli["mcpServers"]), 1)
        for item in vscode["inputs"]:
            self.assertTrue(item["id"])
            self.assertTrue(item["type"])
        vscode_text = json.dumps(vscode)
        for input_id in re.findall(r"\$\{input:([^}]+)\}", vscode_text):
            self.assertIn(input_id, {item["id"] for item in vscode["inputs"]})
        self.assertNotIn("npx", vscode_text + json.dumps(cli))
        self.assertNotIn("allow-all", vscode_text + json.dumps(cli))


if __name__ == "__main__":
    unittest.main()
