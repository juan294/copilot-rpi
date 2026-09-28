"""Portable policy decisions for explicit Copilot hook profiles."""

import json
import contextlib
import importlib.util
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "templates/scripts/rpi-hook.py"


def run_hook(profile, event, cwd):
    data = event if isinstance(event, str) else json.dumps(event)
    return subprocess.run([sys.executable, str(HOOK), "--profile", profile], input=data,
                          text=True, capture_output=True, cwd=cwd, check=False)


class PolicyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="copilot hook ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def event(self, profile, command, tool=None):
        if profile == "vscode-local":
            return {"hook_event_name": "PreToolUse", "tool_name": tool or "Bash",
                    "tool_input": {"command": command}, "cwd": str(self.root)}
        return {"toolName": tool or "bash", "toolArgs": {"command": command},
                "cwd": str(self.root), "timestamp": 1}

    def test_destructive_push_emits_distinct_native_denials(self):
        for profile in ("cli", "vscode-local", "sdk"):
            with self.subTest(profile=profile):
                result = run_hook(profile, self.event(profile, "git push --force origin main"), self.root)
                self.assertEqual(result.returncode, 0 if profile == "sdk" else 2, result.stderr)
                body = json.loads(result.stdout)
                if profile == "vscode-local":
                    body = body["hookSpecificOutput"]
                    self.assertEqual(body["hookEventName"], "PreToolUse")
                self.assertEqual(body["permissionDecision"], "deny")
                self.assertIn("protected", body["permissionDecisionReason"].lower())
                self.assertIn("BLOCKED / WHY", result.stderr)

    def test_cli_json_string_args_and_legitimate_lookalikes(self):
        event = self.event("cli", "git push --force origin main")
        event["toolArgs"] = json.dumps(event["toolArgs"])
        blocked = run_hook("cli", event, self.root)
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        for command in ("echo 'git push --force origin main'", "git push --dry-run --force origin main",
                        "git push origin feature", "gh repo view", "vercel build"):
            with self.subTest(command=command):
                allowed = run_hook("cli", self.event("cli", command), self.root)
                self.assertEqual(allowed.returncode, 0, allowed.stderr)
                self.assertEqual(allowed.stdout, "")

    def test_remote_delete_preview_and_wrapped_commands(self):
        for command in ("gh repo delete owner/repo", "git push origin :main", "vercel deploy",
                        "env A=1 git push --force origin main"):
            with self.subTest(command=command):
                result = run_hook("cli", self.event("cli", command), self.root)
                self.assertEqual(result.returncode, 2, result.stderr)
        production = run_hook("cli", self.event("cli", "vercel deploy --prod"), self.root)
        self.assertEqual(production.returncode, 0, production.stderr)

    def test_other_tools_and_malformed_guarded_payload(self):
        for profile in ("cli", "vscode-local"):
            other = run_hook(profile, self.event(profile, "git push --force origin main", "view"), self.root)
            self.assertEqual(other.returncode, 0, other.stderr)
            self.assertEqual(other.stdout, "")
            malformed = self.event(profile, "git push --force origin main")
            malformed.pop("tool_input" if profile == "vscode-local" else "toolArgs")
            denied = run_hook(profile, malformed, self.root)
            self.assertEqual(denied.returncode, 2)
            self.assertIn("FIX", denied.stderr)
        bad_json = run_hook("cli", "{", self.root)
        self.assertEqual(bad_json.returncode, 2)

    def test_invalid_project_policy_is_diagnosed_as_a_denial(self):
        policy = self.root / ".rpi/policy.json"
        policy.parent.mkdir()
        policy.write_text("{broken")
        result = run_hook("cli", self.event("cli", "git push --force origin main"), self.root)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("BLOCKED / WHY", result.stderr)
        self.assertEqual(json.loads(result.stdout)["permissionDecision"], "deny")

    def test_runtime_error_returns_to_native_permissions(self):
        spec = importlib.util.spec_from_file_location("tested_rpi_hook", HOOK)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        stdout, stderr = io.StringIO(), io.StringIO()
        event = json.dumps(self.event("cli", "git push --force origin main"))
        with patch.object(module, "inspect_command", side_effect=RuntimeError("parser defect")), \
             patch.object(sys, "stdin", io.StringIO(event)), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = module.main(["--profile", "cli"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("POLICY UNAVAILABLE", stderr.getvalue())

    def test_preview_is_inert_and_timeout_is_explicit(self):
        for profile in ("cli", "vscode-local"):
            result = subprocess.run([sys.executable, str(HOOK), "install", "--target", str(self.root),
                                     "--profile", profile], text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            preview = json.loads(result.stdout)
            self.assertEqual(preview["status"], "preview")
            self.assertEqual(preview["timeout_seconds"], 3)
            self.assertFalse((self.root / ".github/hooks/rpi-policy.json").exists())

    def test_activation_preserves_other_hooks_and_refuses_profile_collision(self):
        runtime = self.root / ".rpi/copilot/runtime/rpi-hook.py"
        runtime.parent.mkdir(parents=True)
        shutil.copy2(HOOK, runtime)
        other = self.root / ".github/hooks/owner.json"
        other.parent.mkdir(parents=True)
        other.write_text('{"version":1,"hooks":{}}\n')
        activated = subprocess.run([sys.executable, str(HOOK), "install", "--target", str(self.root),
                                    "--profile", "cli", "--activate"],
                                   text=True, capture_output=True, check=False)
        self.assertEqual(activated.returncode, 0, activated.stderr)
        installed = self.root / ".github/hooks/rpi-policy.json"
        entry = json.loads(installed.read_text())["hooks"]["preToolUse"][0]
        self.assertEqual(entry["timeoutSec"], 3)
        self.assertEqual(other.read_text(), '{"version":1,"hooks":{}}\n')
        collision = subprocess.run([sys.executable, str(HOOK), "install", "--target", str(self.root),
                                    "--profile", "vscode-local", "--activate"],
                                   text=True, capture_output=True, check=False)
        self.assertEqual(collision.returncode, 2)
        self.assertFalse((self.root / ".github/hooks/rpi-policy-local.json").exists())


if __name__ == "__main__":
    unittest.main()
