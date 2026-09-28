"""Candidate-bound, failure-aggregating local verification."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "templates/scripts/rpi-verify.py"


class VerificationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "test@example.test"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Test"], check=True)
        (self.root / ".gitignore").write_text(".rpi/local/\n")
        (self.root / "input.txt").write_text("original")
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "fixture"], check=True)
        self.checks_file = self.root / ".rpi/local/checks.json"
        self.checks_file.parent.mkdir(parents=True)
        self.receipt = self.root / ".rpi/local/copilot/verification.json"

    def verify(self, checks, env=None):
        self.checks_file.write_text(json.dumps(checks))
        return subprocess.run([sys.executable, str(VERIFIER), "--root", str(self.root),
                               "--checks", str(self.checks_file)], capture_output=True, text=True, env=env)

    def verify_declared(self):
        return subprocess.run([sys.executable, str(VERIFIER), "--root", str(self.root)],
                              capture_output=True, text=True)

    @staticmethod
    def check(name, code="0", script=None):
        return {"name": name, "argv": [sys.executable, "-c", script or f"raise SystemExit({code})"]}

    def report(self):
        return json.loads(self.receipt.read_text())

    def test_early_failure_survives_later_success(self):
        result = self.verify([self.check("first", "7"), self.check("second")])
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        report = self.report()
        self.assertEqual("failed", report["status"])
        self.assertFalse(report["passed"])
        self.assertEqual([7, 0], [check["exit_code"] for check in report["checks"]])
        self.assertEqual("custom", report["suite"])
        self.assertEqual(report["identity"], report["identity_after"])

    def test_changed_and_untracked_input_invalidate_receipt(self):
        good = self.verify([self.check("good")])
        self.assertEqual(0, good.returncode, good.stdout + good.stderr)
        before = self.report()["identity"]
        drift = self.verify([self.check("create", script="from pathlib import Path; Path('surprise.txt').write_text('new')")])
        self.assertNotEqual(0, drift.returncode)
        self.assertFalse(self.report()["identity_unchanged"])
        self.assertGreater(self.report()["identity_after"]["file_count"], before["file_count"])
        self.assertFalse(self.report()["passed"])

    def test_interruption_supersedes_prior_green(self):
        self.assertEqual(0, self.verify([self.check("good")]).returncode)
        attempt = self.verify([self.check("finished"), self.check("interrupt", script="import os, signal; os.kill(os.getppid(), signal.SIGTERM)")])
        self.assertNotEqual(0, attempt.returncode)
        self.assertFalse(self.report()["passed"])
        self.assertNotEqual("complete", self.report()["status"])
        self.assertEqual([0], [check["exit_code"] for check in self.report()["checks"]])

    def test_running_receipt_exists_before_first_check(self):
        script = "import json; from pathlib import Path; r=json.loads(Path('.rpi/local/copilot/verification.json').read_text()); assert r['status']=='running' and not r['passed'] and r['identity']['sha256']"
        result = self.verify([self.check("observe", script=script)])
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_recovery_after_failure(self):
        self.assertNotEqual(0, self.verify([self.check("fail", "3")]).returncode)
        self.assertEqual(0, self.verify([self.check("fixed")]).returncode)
        self.assertTrue(self.report()["passed"])
        self.assertEqual("complete", self.report()["status"])
        self.assertTrue(self.report()["environment_unchanged"])

    def test_tool_failure_is_recorded_and_next_check_runs(self):
        bad = {"name": "missing", "argv": ["missing-copilot-test-tool"]}
        self.assertNotEqual(0, self.verify([bad, self.check("later")]).returncode)
        self.assertEqual([127, 0], [check["exit_code"] for check in self.report()["checks"]])

    def test_runtime_tool_change_invalidates_receipt(self):
        fake_bin = self.root / ".rpi/local/bin"
        fake_bin.mkdir(parents=True)
        shellcheck = fake_bin / "shellcheck"
        shellcheck.write_text("#!/bin/sh\necho 1.0\n")
        shellcheck.chmod(0o755)
        env = {**os.environ, "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"]}
        script = "from pathlib import Path; Path('.rpi/local/bin/shellcheck').write_text('#!/bin/sh\\necho 2.0\\n')"
        result = self.verify([self.check("change-tool", script=script)], env=env)
        self.assertNotEqual(0, result.returncode)
        self.assertFalse(self.report()["environment_unchanged"])
        self.assertEqual("1.0", self.report()["environment"]["tool_versions"]["shellcheck"])

    def test_project_policy_selects_its_complete_check_inventory(self):
        policy = self.root / ".rpi/policy.json"
        checks = [self.check("adopter-check")]
        policy.write_text(json.dumps({"schema_version": 1, "verification_checks": checks}))
        result = self.verify_declared()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("ci-equivalent", self.report()["suite"])
        self.assertEqual(checks, [{key: item[key] for key in ("name", "argv")}
                                  for item in self.report()["checks"]])

    def test_no_project_policy_uses_blueprint_inventory(self):
        shell = self.root / "templates/scripts/check.sh"
        shell.parent.mkdir(parents=True)
        shell.write_text("#!/bin/sh\nexit 0\n")
        spec = importlib.util.spec_from_file_location("copilot_verify_inventory", VERIFIER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        checks = module.required_checks(self.root)
        self.assertEqual(10, len(checks))
        self.assertEqual("python-tests", checks[0]["name"])
        self.assertEqual("internal-links", checks[-1]["name"])
        self.assertIn("templates/scripts/check.sh", checks[6]["argv"])

    def test_malformed_or_empty_policy_never_uses_blueprint_fallback(self):
        policy = self.root / ".rpi/policy.json"
        for content in ('{"schema_version":1,"verification_checks":[]}',
                        '{"schema_version":1,"schema_version":1,"verification_checks":[]}',
                        '{"schema_version":2,"verification_checks":[{"name":"x","argv":["true"]}]}',
                        '{"schema_version":1,"verification_checks":[{"name":"x","argv":["true"],"extra":1}]}'):
            with self.subTest(content=content):
                policy.write_text(content)
                result = self.verify_declared()
                self.assertNotEqual(0, result.returncode)
                self.assertIn("BLOCKED / WHY", result.stderr)
                self.assertFalse(self.receipt.exists())


if __name__ == "__main__":
    unittest.main()
