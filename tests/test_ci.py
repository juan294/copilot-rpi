"""CI must exercise the same portable gate and Markdown scope as local work."""

from pathlib import Path
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

    def test_markdown_lint_excludes_immutable_source_snapshots(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/markdown-lint.yml").read_text())
        self.assertIn("!upstream/snapshots/**", workflow["jobs"]["lint"]["steps"][-1]["with"]["globs"])

    def test_release_gate_rejects_python_manifest_version_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "templates/scripts").mkdir(parents=True)
            script = project / "templates/scripts/verify-version.sh"
            script.write_bytes((ROOT / "templates/scripts/verify-version.sh").read_bytes())
            (project / "CHANGELOG.md").write_text("## [Unreleased]\n\n## [2.0.0] - 2026-09-28\n")
            (project / "pyproject.toml").write_text('[project]\nversion = "1.18.0"\n')
            subprocess.run(["git", "init", "-q", project], check=True)
            result = subprocess.run(["bash", script], cwd=project, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("pyproject.toml", result.stdout)


if __name__ == "__main__":
    unittest.main()
