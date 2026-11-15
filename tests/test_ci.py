"""CI must exercise the same portable gate and Markdown scope as local work."""

from pathlib import Path
import re
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class CIContractTests(unittest.TestCase):
    def test_validate_runs_full_gate(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/validate.yml").read_text())
        commands = [step.get("run", "") for job in workflow["jobs"].values()
                    for step in job["steps"]]
        self.assertTrue(any("bash scripts/verify-local.sh" in command for command in commands))

    def test_node_line_comes_from_nvmrc_not_a_literal(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/validate.yml").read_text())
        setups = [step for job in workflow["jobs"].values() for step in job["steps"]
                  if str(step.get("uses", "")).startswith("actions/setup-node@")]
        self.assertEqual(1, len(setups))
        self.assertEqual(".nvmrc", setups[0]["with"].get("node-version-file"))
        self.assertNotIn("node-version", setups[0]["with"])
        self.assertRegex((ROOT / ".nvmrc").read_text(), r"\A24\n?\Z")

    def test_markdown_lint_excludes_immutable_source_snapshots(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/markdown-lint.yml").read_text())
        self.assertIn("!upstream/snapshots/**", workflow["jobs"]["lint"]["steps"][-1]["with"]["globs"])

    def run_release_gate(self, files):
        """Run verify-version.sh in a scratch Git repository holding only `files`."""
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            script = project / "templates/scripts/verify-version.sh"
            script.parent.mkdir(parents=True)
            script.write_bytes((ROOT / "templates/scripts/verify-version.sh").read_bytes())
            for name, text in files.items():
                (project / name).parent.mkdir(parents=True, exist_ok=True)
                (project / name).write_text(text)
            subprocess.run(["git", "init", "-q", project], check=True)
            subprocess.run(["git", "-C", project, "add", "."], check=True)
            return subprocess.run(["bash", script], cwd=project, capture_output=True, text=True)

    def test_release_gate_rejects_python_manifest_version_drift(self):
        result = self.run_release_gate({
            "CHANGELOG.md": "## [Unreleased]\n\n## [9.0.0] - 2026-09-29\n",
            "pyproject.toml": '[project]\nversion = "1.19.0"\n',
        })
        self.assertNotEqual(0, result.returncode)
        self.assertIn("pyproject.toml", result.stdout)

    def test_release_gate_checks_npm_lock_root_versions_but_not_dependency_ranges(self):
        lock = """{{
  "name": "fixture",
  "version": "{root}",
  "lockfileVersion": 3,
  "packages": {{
    "": {{
      "name": "fixture",
      "version": "{package}",
      "devDependencies": {{
        "dep": "^9.0.0"
      }}
    }},
    "node_modules/dep": {{
      "version": "9.0.0",
      "dependencies": {{
        "other": "^9.0.0"
      }}
    }}
  }}
}}
"""
        cases = {("9.1.0", "9.1.0"): 0, ("9.0.0", "9.1.0"): 1, ("9.1.0", "9.0.0"): 1}
        for (root, package), expected in cases.items():
            with self.subTest(root=root, package=package):
                result = self.run_release_gate({
                    "CHANGELOG.md": "## [Unreleased]\n\n## [9.1.0] - 2026-11-15\n\n## [9.0.0] - 2026-09-29\n",
                    "package.json": '{\n  "name": "fixture",\n  "version": "9.1.0"\n}\n',
                    "package-lock.json": lock.format(root=root, package=package),
                })
                self.assertEqual(expected, result.returncode, result.stdout)
                if expected:
                    self.assertIn("package-lock.json", result.stdout)

    def test_release_gate_ignores_upstream_cc_rpi_versions_equal_to_previous_release(self):
        files = {
            "CHANGELOG.md": "## [Unreleased]\n\n## [9.1.0] - 2026-11-15\n\n## [9.0.0] - 2026-09-29\n",
            "package.json": '{\n  "name": "fixture",\n  "version": "9.1.0"\n}\n',
            "tool.py": '"""Adapted from pinned cc-rpi 9.0.0 at abc.\nAdapted from cc-rpi source 9.0.0 at `abc`."""\n',
            "upstream/cc-rpi.lock.json": '{"rationale": "no Copilot item in source 9.0.0"}\n',
        }
        clean = self.run_release_gate(files)
        self.assertEqual(0, clean.returncode, clean.stdout)
        files["README.md"] = "Copilot RPI 9.0.0 is current.\n"
        result = self.run_release_gate(files)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("README.md", result.stdout)
        self.assertNotIn("tool.py", result.stdout)
        for line in ("Copilot RPI 9.0.0 syncs with cc-rpi 9.0.0.", "see cc-rpi 9.0.0x and the 9.0.0 notes"):
            with self.subTest(line=line):
                mixed = dict(files, **{"notes.md": line + "\n"})
                result = self.run_release_gate(mixed)
                self.assertNotEqual(0, result.returncode, result.stdout)
                self.assertIn("notes.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
