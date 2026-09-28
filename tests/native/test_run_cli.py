"""Native probe contract with a fake external Copilot executable."""

import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests/native/run_cli.py"
FAKE = ROOT / "tests/native/fixtures/fake_copilot.py"
SPEC = importlib.util.spec_from_file_location("native_runner", RUNNER)
native = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native)


class NativeRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.evidence = self.directory / "evidence"

    def receipt(self, profile="cli-programmatic"):
        return json.loads((self.evidence / f"{profile}-receipt.json").read_text())

    def invoke(self, profile="cli-programmatic", *, mode="ok", timeout=15, extra_env=None):
        env = dict(os.environ, COPILOT_BIN=str(FAKE), COPILOT_MODEL="fixture-model",
                   RPI_NATIVE_FAKE_MODE=mode, RPI_NATIVE_EVIDENCE_DIR=str(self.evidence))
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, str(RUNNER), "--profile", profile,
             "--timeout-seconds", str(timeout)], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=40,
        )

    def test_programmatic_positive_and_denied_write_record_disk_and_remote(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = self.receipt()
        self.assertEqual(receipt["status"], "passed")
        self.assertEqual(receipt["profile"], "cli-programmatic")
        self.assertEqual(receipt["client_version"], "fake-copilot 1.2.3")
        self.assertTrue(receipt["checks"]["allowed_report"])
        self.assertTrue(receipt["checks"]["denied_write_unchanged"])
        self.assertTrue(receipt["checks"]["native_write_denial_event"])
        self.assertTrue(receipt["checks"]["denied_write_report_observed"])
        denied = next(command for command in receipt["commands"] if command["label"] == "denied write")
        self.assertEqual(denied["exit"], 0)
        self.assertIn("permission.requested", denied["stdout"])
        self.assertIn("permission.completed", denied["stdout"])
        self.assertTrue(receipt["checks"]["remote_unchanged"])
        self.assertTrue(receipt["checks"]["blueprint_candidate_unchanged"])
        self.assertEqual(receipt["blueprint_candidate"], receipt["blueprint_candidate_after"])
        self.assertEqual(len(receipt["blueprint_candidate"]["sha256"]), 64)
        self.assertEqual(receipt["commands"][0]["argv"], [str(FAKE), "--version"])
        runner_calls = receipt["runner_copilot_argv"]
        runner_command = next(command["argv"] for command in receipt["commands"]
                              if command["label"] == "shipped automation runner")
        self.assertEqual(runner_command[runner_command.index("--timeout") + 1], "15")
        self.assertEqual([call for call in runner_calls if call == ["--version"]], [["--version"]])
        self.assertTrue(any("-p" in call and "--available-tools=view,grep,glob" in call
                            and "--allow-tool=read" in call for call in runner_calls))
        self.assertNotIn("fixture-secret-value", json.dumps(receipt))
        denied_argv = next(command["argv"] for command in receipt["commands"]
                           if command["label"] == "denied write")
        self.assertIn("--available-tools=view,grep,glob,create,edit,apply_patch,skill", denied_argv)
        self.assertIn("--deny-tool=write", denied_argv)

    def test_cli_tool_denial_event_links_target_and_error(self):
        output = '\n'.join((
            json.dumps({"type": "tool.execution_start", "data": {"toolCallId": "write-1",
                       "toolName": "apply_patch", "arguments": "*** Delete File: denied-write.txt"}}),
            json.dumps({"type": "tool.execution_complete", "data": {"toolCallId": "write-1",
                       "success": False, "error": {"code": "denied",
                       "message": "Permission to run this tool was denied due to the following rules: `write`"}}}),
            json.dumps({"type": "assistant.message", "data": {"content": "Write was denied"}}),
        ))
        target = self.directory / "denied-write.txt"
        self.assertEqual(native.native_denial_observation(output, target), (True, True))
        self.assertEqual(native.native_denial_observation(output.replace("denied-write.txt", "other.txt"), target),
                         (False, True))
        self.assertEqual(native.native_denial_observation(output.replace('"write-1"', '"other"', 1), target),
                         (False, True))
        events = output.splitlines()
        first = json.loads(events[0])
        first["data"]["arguments"] = "*** Update File: other.txt\n+denied-write.txt"
        wrong_target = "\n".join((json.dumps(first), *events[1:]))
        self.assertEqual(native.native_denial_observation(wrong_target, target), (False, True))
        same_name_elsewhere = output.replace("*** Delete File: denied-write.txt",
                                             "*** Delete File: other/denied-write.txt")
        self.assertEqual(native.native_denial_observation(same_name_elsewhere, target), (False, True))
        sdk_elsewhere = "\n".join((
            json.dumps({"type": "permission.requested", "data": {"requestId": "sdk-1",
                       "permissionRequest": {"kind": "write", "fileName": "other/denied-write.txt"}}}),
            json.dumps({"type": "permission.completed", "data": {"requestId": "sdk-1",
                       "result": {"kind": "denied-by-rules"}}}),
        ))
        self.assertEqual(native.native_denial_observation(sdk_elsewhere, target), (False, False))

    def test_programmatic_marker_gap_preserves_sanitized_report_excerpt(self):
        result = self.invoke(extra_env={"COPILOT_GITHUB_TOKEN": "force-omit-marker"})
        self.assertNotEqual(result.returncode, 0)
        receipt = self.receipt()
        self.assertEqual(receipt["status"], "blocked")
        self.assertIn("no findings", receipt["report_excerpt"])
        self.assertNotIn(receipt["fixture"]["marker"], receipt["report_excerpt"])

    def test_cli_profile_uses_explicit_skill_and_read_only_tools(self):
        result = self.invoke("cli")
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = self.receipt("cli")
        self.assertEqual(receipt["status"], "passed")
        self.assertTrue(receipt["checks"]["skill_invoked"])
        self.assertTrue(receipt["checks"]["skill_discovered"])
        self.assertTrue(receipt["checks"]["missing_skill_negative"])
        self.assertTrue(receipt["checks"]["product_unchanged"])
        self.assertTrue(receipt["checks"]["remote_unchanged"])
        prompt_command = next(command["argv"] for command in receipt["commands"]
                              if command["label"] == "cli skill")
        self.assertIn("/rpi-research", " ".join(prompt_command))
        self.assertNotIn(receipt["fixture"]["marker"], " ".join(prompt_command))
        self.assertIn("--available-tools=view,grep,glob,skill", prompt_command)
        self.assertIn("--allow-tool=read", prompt_command)
        self.assertEqual([command["label"] for command in receipt["commands"]
                          if command["label"].startswith("skill list")],
                         ["skill list positive", "skill list negative"])

    def test_cli_skill_prompt_explicitly_requests_native_tool_call(self):
        result = self.invoke("cli", mode="requires-tool-first")
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = self.receipt("cli")
        self.assertTrue(receipt["checks"]["skill_answer_after_invocation"])

    def test_prompt_echo_cannot_pass_skill_loading(self):
        result = self.invoke("cli", mode="prompt-echo")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.receipt("cli")["status"], "blocked")

    def test_correct_answer_without_native_skill_event_is_inconclusive(self):
        result = self.invoke("cli", mode="no-skill-event")
        self.assertNotEqual(result.returncode, 0)
        receipt = self.receipt("cli")
        self.assertTrue(receipt["checks"]["skill_answered"])
        self.assertFalse(receipt["checks"]["skill_invoked"])
        self.assertFalse(receipt["checks"]["skill_answer_after_invocation"])

    def test_failed_skill_completion_cannot_pass_invocation(self):
        result = self.invoke("cli", mode="failed-skill-event")
        self.assertNotEqual(result.returncode, 0)
        receipt = self.receipt("cli")
        self.assertTrue(receipt["checks"]["skill_answered"])
        self.assertFalse(receipt["checks"]["skill_invoked"])
        self.assertFalse(receipt["checks"]["skill_answer_after_invocation"])

    def test_answer_before_skill_completion_is_inconclusive(self):
        result = self.invoke("cli", mode="answer-before-skill-complete")
        self.assertNotEqual(result.returncode, 0)
        receipt = self.receipt("cli")
        self.assertTrue(receipt["checks"]["skill_invoked"])
        self.assertTrue(receipt["checks"]["skill_answered"])
        self.assertFalse(receipt["checks"]["skill_answer_after_invocation"])

    def test_prose_refusal_without_native_event_is_inconclusive(self):
        result = self.invoke(mode="prose-denial")
        self.assertNotEqual(result.returncode, 0)
        receipt = self.receipt()
        self.assertEqual(receipt["status"], "blocked")
        self.assertFalse(receipt["checks"]["native_write_denial_event"])
        self.assertIn("denial event", receipt["recovery"])

    def test_unlinked_permission_completion_is_inconclusive(self):
        result = self.invoke(mode="mismatched-event")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.receipt()["checks"]["native_write_denial_event"])

    def test_denial_without_native_report_is_inconclusive(self):
        result = self.invoke(mode="no-denial-report")
        self.assertNotEqual(result.returncode, 0)
        receipt = self.receipt()
        self.assertTrue(receipt["checks"]["native_write_denial_event"])
        self.assertFalse(receipt["checks"]["denied_write_report_observed"])

    def test_source_candidate_change_during_probe_blocks_pass(self):
        receipt = {"checks": {}, "commands": []}
        with mock.patch.object(native, "source_identity", side_effect=[
            {"sha256": "before"}, {"sha256": "after"},
        ]), mock.patch.dict(os.environ, {"COPILOT_BIN": str(FAKE),
                                     "RPI_NATIVE_FAKE_MODE": "ok"}):
            with self.assertRaisesRegex(native.ProbeBlocked, "candidate"):
                native.probe(SimpleNamespace(profile="cli", timeout_seconds=15), receipt)

    def test_profile_receipts_survive_sequential_runs(self):
        self.assertEqual(self.invoke("cli").returncode, 0)
        cli_bytes = (self.evidence / "cli-receipt.json").read_bytes()
        self.assertEqual(self.invoke("cli-programmatic").returncode, 0)
        self.assertEqual((self.evidence / "cli-receipt.json").read_bytes(), cli_bytes)
        self.assertEqual(self.receipt("cli-programmatic")["profile"], "cli-programmatic")

    def test_preflight_rejects_unsupported_flags_before_inference(self):
        result = self.invoke(mode="old-help")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported", result.stderr.lower())
        receipt = self.receipt()
        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual([command["argv"][1] for command in receipt["commands"]],
                         ["--version", "--help"])

    def test_process_checks_full_output_while_receipt_stays_bounded(self):
        commands = []
        code, output, error = native.run_process(
            [sys.executable, "-c", "print('x' * 5000 + '--no-auto-update')"],
            cwd=self.directory, env=os.environ.copy(),
            deadline=time.monotonic() + 10, commands=commands, label="long help")
        self.assertEqual(code, 0)
        self.assertEqual(error, "")
        self.assertIn("--no-auto-update", output)
        self.assertLessEqual(len(commands[0]["stdout"]), 4000)

    def test_verbose_version_does_not_expand_receipt(self):
        result = self.invoke("cli", mode="long-version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLessEqual(len(self.receipt("cli")["client_version"]), 4000)

    def test_missing_auth_is_a_blocker_without_report_success(self):
        result = self.invoke(mode="missing-auth", extra_env={"COPILOT_GITHUB_TOKEN": "force-missing-auth"})
        self.assertNotEqual(result.returncode, 0)
        receipt = self.receipt()
        self.assertEqual(receipt["status"], "blocked")
        self.assertFalse(receipt["checks"].get("allowed_report", False))
        self.assertIn("auth", receipt["recovery"].lower())

    def test_denied_write_side_effect_blocks_even_if_cli_reports_success(self):
        result = self.invoke(mode="write-anyway")
        self.assertNotEqual(result.returncode, 0)
        receipt = self.receipt()
        self.assertEqual(receipt["status"], "blocked")
        self.assertFalse(receipt["checks"]["denied_write_unchanged"])

    def test_wall_timeout_is_bounded_and_recorded(self):
        start = time.monotonic()
        result = self.invoke("cli", mode="sleep", timeout=1)
        self.assertLess(time.monotonic() - start, 5)
        self.assertNotEqual(result.returncode, 0)
        receipt = self.receipt("cli")
        self.assertEqual(receipt["status"], "blocked")
        self.assertIn("timeout", receipt["recovery"].lower())

    def test_inner_runner_timeout_finishes_before_outer_cleanup(self):
        start = time.monotonic()
        result = self.invoke(timeout=1, extra_env={"COPILOT_GITHUB_TOKEN": "force-sleep"})
        self.assertLess(time.monotonic() - start, 10)
        self.assertNotEqual(result.returncode, 0)
        receipt = self.receipt()
        self.assertIn("programmatic report failed", receipt["recovery"])
        runner = next(command for command in receipt["commands"]
                      if command["label"] == "shipped automation runner")
        self.assertEqual(runner["exit"], 124)

    def test_secret_values_never_enter_receipt_or_output(self):
        result = self.invoke(extra_env={"COPILOT_GITHUB_TOKEN": "fixture-secret-value"},
                             mode="echo-secret")
        self.assertNotIn("fixture-secret-value", result.stdout + result.stderr)
        self.assertNotIn("fixture-secret-value", (self.evidence / "cli-programmatic-receipt.json").read_text())

    def test_unrelated_environment_is_not_given_to_copilot(self):
        result = self.invoke("cli", mode="env-check",
                             extra_env={"UNRELATED_SECRET": "private-value"})
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = self.receipt("cli")
        skill_output = next(command["stdout"] for command in receipt["commands"]
                            if command["label"] == "cli skill")
        self.assertIn("unrelated_present=false", skill_output)


if __name__ == "__main__":
    unittest.main()
