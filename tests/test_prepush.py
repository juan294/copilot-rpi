"""Opt-in pre-push verification against disposable local bare repositories."""

import importlib.util
import json
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
        (self.root / ".rpi/local").mkdir(parents=True)
        (self.root / ".rpi/local/.gitignore").write_text("*\n")
        # Activation installs the gate runtime here; like this repository, the fixture ignores it.
        (self.root / ".gitignore").write_text(".rpi/copilot/\n")
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


    def runtime_names(self):
        return sorted(path.name for path in (self.root / ".rpi/copilot/runtime").iterdir())

    def test_activation_installs_recorded_runtime_and_deactivation_restores_prior_hook(self):
        hook = self.root / ".git/hooks/pre-push"
        prior = b"#!/bin/sh\nexit 0\n"
        hook.write_bytes(prior)
        hook.chmod(0o755)
        self.assertFalse((self.root / ".rpi/copilot/runtime").exists())
        self.assertEqual(self.invoke("install", "--target", self.root, "--activate").returncode, 0)
        self.assertEqual(self.runtime_names(), ["rpi-candidate.py", "rpi-prepush.install.json",
                                                "rpi-prepush.py", "rpi-verify.py"])
        record = json.loads((self.root / ".rpi/copilot/runtime/rpi-prepush.install.json").read_text())
        self.assertEqual(sorted(record["files"]), ["rpi-candidate.py", "rpi-prepush.py", "rpi-verify.py"])
        result = self.invoke("install", "--target", self.root, "--deactivate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "inactive")
        self.assertEqual(hook.read_bytes(), prior)
        self.assertFalse((self.root / ".git/hooks/pre-push.rpi-prior").exists())
        self.assertFalse((self.root / ".rpi/copilot/runtime").exists())
        self.assertTrue((self.root / ".rpi/policy.json").exists())

    def test_deactivation_preserves_edited_wrapper_or_runtime(self):
        self.assertEqual(self.invoke("install", "--target", self.root, "--activate").returncode, 0)
        hook = self.root / ".git/hooks/pre-push"
        wrapper = hook.read_bytes()
        hook.write_bytes(wrapper + b"# owner edit\n")
        refused = self.invoke("install", "--target", self.root, "--deactivate")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("edited", refused.stderr)
        self.assertEqual(hook.read_bytes(), wrapper + b"# owner edit\n")
        hook.write_bytes(wrapper)
        runtime = self.root / ".rpi/copilot/runtime/rpi-verify.py"
        runtime.write_bytes(b"# owner edit\n")
        refused = self.invoke("install", "--target", self.root, "--deactivate")
        self.assertEqual(refused.returncode, 1)
        self.assertEqual(runtime.read_bytes(), b"# owner edit\n")
        self.assertEqual(hook.read_bytes(), wrapper)
        missing = self.invoke("install", "--target", self.base / "absent", "--deactivate")
        self.assertEqual(missing.returncode, 1)

    def test_activation_refuses_unrecorded_runtime_and_ignores_planted_temporary_symlinks(self):
        runtime_dir = self.root / ".rpi/copilot/runtime"
        runtime_dir.mkdir(parents=True)
        outside = self.base / "outside.txt"
        outside.write_text("outside\n")
        for name in ("rpi-prepush.py", "rpi-candidate.py", "rpi-verify.py", "rpi-prepush.install.json"):
            (runtime_dir / (".{}.tmp".format(name))).symlink_to(outside)
        self.assertEqual(self.invoke("install", "--target", self.root, "--activate").returncode, 0)
        self.assertEqual(outside.read_text(), "outside\n")
        self.assertFalse((runtime_dir / "rpi-prepush.py").is_symlink())
        self.assertEqual(self.invoke("install", "--target", self.root, "--deactivate").returncode, 0)
        for path in list(runtime_dir.iterdir()):
            path.unlink()
        (runtime_dir / "rpi-verify.py").write_bytes(b"# owner verifier\n")
        refused = self.invoke("install", "--target", self.root, "--activate")
        self.assertEqual(refused.returncode, 1)
        self.assertEqual((runtime_dir / "rpi-verify.py").read_bytes(), b"# owner verifier\n")
        self.assertFalse((self.root / ".git/hooks/pre-push").exists())
        (runtime_dir / "rpi-verify.py").unlink()
        (runtime_dir / "rpi-prepush.py").symlink_to(PREPUSH)
        refused = self.invoke("install", "--target", self.root, "--activate")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("symlink", refused.stderr)


class PrepushAfterInstallTests(unittest.TestCase):
    """The documented flow from a real rendered and applied package, without copying the runtime."""

    def test_render_apply_activate_gates_push_and_deactivates(self):
        with tempfile.TemporaryDirectory(prefix="copilot prepush install ") as directory:
            base = Path(directory)
            package, target, remote = base / "package", base / "target", base / "remote.git"
            rendered = subprocess.run([sys.executable, str(ROOT / "templates/scripts/rpi-distribution.py"), "render",
                                       "--source", str(ROOT), "--profile", "cli", "--target", str(package)],
                                      capture_output=True, text=True)
            self.assertEqual(0, rendered.returncode, rendered.stderr)
            runtime = package / ".rpi/copilot/runtime"
            git(base, "init", "-q", "--bare", str(remote))
            git(base, "init", "-q", "-b", "main", str(target))
            git(target, "config", "user.name", "Fixture")
            git(target, "config", "user.email", "fixture@example.invalid")
            git(target, "remote", "add", "origin", str(remote))
            plan = base / "plan.json"
            for argv in (["plan", "--package", str(package), "--target", str(target), "--profile", "cli",
                          "--action", "update", "--output", str(plan)], ["apply", "--plan", str(plan)]):
                result = subprocess.run([sys.executable, str(runtime / "rpi-lifecycle.py"), *argv],
                                        capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            (target / "README.md").write_text("candidate\n")
            (target / ".gitignore").write_text(".rpi/copilot/\n.rpi/local/\n")
            (target / "scripts").mkdir()
            (target / "scripts/demo.sh").write_text("#!/bin/sh\nexit 0\n")
            git(target, "add", ".")
            git(target, "commit", "-qm", "Installed candidate")
            inventory = base / "checks.json"
            inventory.write_text(json.dumps(module("installed_verify", runtime / "rpi-verify.py").required_checks(target)))
            prepush = [sys.executable, str(runtime / "rpi-prepush.py"), "install", "--target", str(target)]
            active = subprocess.run([*prepush, "--checks", str(inventory), "--activate"], capture_output=True, text=True)
            self.assertEqual(0, active.returncode, active.stdout + active.stderr)
            self.assertEqual((target / ".rpi/copilot/runtime/rpi-prepush.py").read_bytes(),
                             (runtime / "rpi-prepush.py").read_bytes())
            blocked = git(target, "push", "origin", "main", check=False)
            self.assertNotEqual(0, blocked.returncode)
            self.assertIn("BLOCKED / WHY", blocked.stderr)
            inactive = subprocess.run([*prepush, "--deactivate"], capture_output=True, text=True)
            self.assertEqual(0, inactive.returncode, inactive.stdout + inactive.stderr)
            self.assertFalse((target / ".git/hooks/pre-push").exists())
            self.assertFalse((target / ".rpi/copilot/runtime").exists())
            pushed = git(target, "push", "origin", "main", check=False)
            self.assertEqual(0, pushed.returncode, pushed.stderr)

if __name__ == "__main__":
    unittest.main()
