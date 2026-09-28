"""Opt-in pre-push verification against disposable local bare repositories."""

import importlib.util
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPUSH = ROOT / "templates/scripts/rpi-prepush.py"
CANDIDATE = ROOT / "templates/scripts/rpi-candidate.py"
VERIFY = ROOT / "templates/scripts/rpi-verify.py"


def git(root, *args, check=True):
    return subprocess.run(["git", "-C", str(root), *args], text=True,
                          capture_output=True, check=check)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class PrepushTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="copilot prepush ü ")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project ü"
        self.remote = self.base / "bare remote.git"
        git(self.base, "init", "-q", "--bare", str(self.remote))
        git(self.base, "init", "-q", "-b", "main", str(self.root))
        git(self.root, "config", "user.name", "Fixture")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        git(self.root, "remote", "add", "origin", str(self.remote))
        (self.root / ".rpi/copilot/runtime").mkdir(parents=True)
        shutil.copy2(PREPUSH, self.root / ".rpi/copilot/runtime/rpi-prepush.py")
        shutil.copy2(CANDIDATE, self.root / ".rpi/copilot/runtime/rpi-candidate.py")
        shutil.copy2(VERIFY, self.root / ".rpi/copilot/runtime/rpi-verify.py")
        (self.root / ".rpi/local").mkdir(parents=True)
        (self.root / ".rpi/local/.gitignore").write_text("*\n")
        shell = self.root / "templates/scripts/demo.sh"
        shell.parent.mkdir(parents=True)
        shell.write_text("#!/bin/sh\nexit 0\n")
        self.checks = module("prepush_verify_inventory", VERIFY).required_checks(self.root)
        (self.root / ".rpi/policy.json").write_text(json.dumps({
            "schema_version": 1, "require_verification_receipt": True,
            "integration_branch": "main", "verification_checks": self.checks,
        }))
        (self.root / "README.md").write_text("candidate one\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "Initial candidate")

    def invoke(self, *args):
        return subprocess.run([sys.executable, str(PREPUSH), *map(str, args)],
                              text=True, capture_output=True, cwd=self.root, check=False)

    def receipt(self, *, commit=None, passed=True):
        candidate = module("prepush_candidate_fixture", CANDIDATE)
        identity, environment = candidate.identity(self.root), candidate.environment()
        if commit is not None:
            identity["commit"] = commit
        checks = [{**item, "exit_code": 0, "duration_seconds": 0.01}
                  for item in self.checks]
        report = {"schema_version": 1, "suite": "ci-equivalent", "status": "complete",
                  "passed": passed, "identity": identity, "identity_after": identity,
                  "identity_unchanged": True, "environment": environment,
                  "environment_after": environment, "environment_unchanged": True,
                  "checks": checks}
        evidence = self.root / ".rpi/local/copilot/verification.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(json.dumps(report))

    def test_preview_is_read_only_and_activation_chains_prior_hook(self):
        path = self.root / ".git/hooks/pre-push"
        prior = "#!/bin/sh\nprintf 'prior ran\\n' >> .prior-marker\n"
        path.write_text(prior)
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        before = path.read_bytes()
        preview = self.invoke("install", "--target", self.root)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(json.loads(preview.stdout)["status"], "preview")
        self.assertEqual(path.read_bytes(), before)
        active = self.invoke("install", "--target", self.root, "--activate")
        self.assertEqual(active.returncode, 0, active.stderr)
        self.assertEqual(json.loads(active.stdout)["status"], "active")
        self.assertEqual((self.root / ".git/hooks/pre-push.rpi-prior").read_bytes(), before)
        self.assertIn(b"pre-push.rpi-prior", path.read_bytes())
        second = self.invoke("install", "--target", self.root, "--activate")
        self.assertEqual(second.returncode, 0, second.stderr)

    def test_local_bare_push_rejects_stale_then_accepts_exact_receipt(self):
        self.assertEqual(self.invoke("install", "--target", self.root, "--activate").returncode, 0)
        stale = git(self.root, "push", "origin", "main", check=False)
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn("BLOCKED / WHY", stale.stderr)
        self.assertIsNone(git(self.remote, "rev-parse", "--verify", "refs/heads/main", check=False).stdout.strip() or None)
        self.receipt()
        pushed = git(self.root, "push", "origin", "main", check=False)
        self.assertEqual(pushed.returncode, 0, pushed.stderr)
        self.assertEqual(git(self.remote, "rev-parse", "refs/heads/main").stdout.strip(),
                         git(self.root, "rev-parse", "HEAD").stdout.strip())
        (self.root / "README.md").write_text("candidate two\n")
        git(self.root, "add", "README.md")
        git(self.root, "commit", "-qm", "Next candidate")
        older = git(self.remote, "rev-parse", "refs/heads/main").stdout.strip()
        refused = git(self.root, "push", "origin", "main", check=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual(git(self.remote, "rev-parse", "refs/heads/main").stdout.strip(), older)
        self.receipt()
        corrected = git(self.root, "push", "origin", "main", check=False)
        self.assertEqual(corrected.returncode, 0, corrected.stderr)

    def test_tag_push_and_dirty_candidate_require_exact_receipt(self):
        self.assertEqual(self.invoke("install", "--target", self.root, "--activate").returncode, 0)
        self.receipt()
        git(self.root, "tag", "v1.2.3")
        (self.root / "unexpected.txt").write_text("new untracked candidate\n")
        dirty = git(self.root, "push", "origin", "v1.2.3", check=False)
        self.assertNotEqual(dirty.returncode, 0)
        self.assertIn("BLOCKED / WHY", dirty.stderr)
        (self.root / "unexpected.txt").unlink()
        clean = git(self.root, "push", "origin", "v1.2.3", check=False)
        self.assertEqual(clean.returncode, 0, clean.stderr)

    def test_other_branch_not_gated_and_unactivated_policy_is_inert(self):
        git(self.root, "branch", "feature")
        push = git(self.root, "push", "origin", "feature", check=False)
        self.assertEqual(push.returncode, 0, push.stderr)
        self.assertFalse((self.root / ".git/hooks/pre-push").exists())

    def test_policy_and_hook_are_written_only_after_reviewed_activation(self):
        policy = self.root / ".rpi/policy.json"
        policy.unlink()
        inventory = self.base / "reviewed checks.json"
        inventory.write_text(json.dumps(self.checks))
        preview = self.invoke("install", "--target", self.root, "--checks", inventory)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertFalse(policy.exists())
        self.assertFalse((self.root / ".git/hooks/pre-push").exists())
        selected = json.loads(preview.stdout)["policy"]
        self.assertEqual(selected["verification_checks"], self.checks)
        active = self.invoke("install", "--target", self.root, "--checks", inventory,
                             "--activate")
        self.assertEqual(active.returncode, 0, active.stderr)
        self.assertEqual(json.loads(policy.read_text()), selected)
        self.assertTrue((self.root / ".git/hooks/pre-push").is_file())

    def test_existing_hook_failure_is_not_bypassed(self):
        hook = self.root / ".git/hooks/pre-push"
        hook.write_text("#!/bin/sh\necho owner refusal >&2\nexit 7\n")
        hook.chmod(0o755)
        self.assertEqual(self.invoke("install", "--target", self.root,
                                     "--activate").returncode, 0)
        self.receipt()
        refused = git(self.root, "push", "origin", "main", check=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("owner refusal", refused.stderr)
        self.assertFalse(git(self.remote, "rev-parse", "--verify", "refs/heads/main",
                             check=False).stdout.strip())

    def test_symlinked_custom_hooks_parent_cannot_escape_checkout(self):
        outside = self.base / "outside hooks"
        outside.mkdir()
        marker = outside / "owner.txt"
        marker.write_bytes(b"OWNER CONTENT")
        (self.root / "hooks-alias").symlink_to(outside, target_is_directory=True)
        git(self.root, "config", "core.hooksPath", "hooks-alias/subdir")
        result = self.invoke("install", "--target", self.root, "--activate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr.lower())
        self.assertEqual(marker.read_bytes(), b"OWNER CONTENT")
        self.assertFalse((outside / "subdir/pre-push").exists())


if __name__ == "__main__":
    unittest.main()
