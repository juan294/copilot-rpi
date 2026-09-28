"""Scheduled Copilot automation: fake only the external CLI boundary."""

import importlib.util
import fcntl
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest
import shutil
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "templates/scripts/rpi-automation.py"
SPEC = importlib.util.spec_from_file_location("rpi_automation", RUNNER)
automation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(automation)


class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "docs/agents").mkdir(parents=True)
        self.blueprint = self.root / "blueprint"
        (self.blueprint / "templates/skills/rpi-update").mkdir(parents=True)
        (self.blueprint / "templates/skills/rpi-update/SKILL.md").write_text("Update contract\n")
        self.bin = self.root / "copilot"
        self.bin.write_text("""#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
Path(os.environ['COPILOT_HOME'], 'capture.json').write_text(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(), 'env': sorted(os.environ), 'allow_all': os.environ.get('COPILOT_ALLOW_ALL')}))
if '--version' in sys.argv: print('copilot 1.2.3'); sys.exit(0)
mode_file = Path(os.environ['COPILOT_HOME'], 'mode')
mode = mode_file.read_text() if mode_file.exists() else 'ok'
if '--help' in sys.argv:
 print('-p --prompt -s --silent --no-ask-user --available-tools --allow-tool --model --no-remote --no-remote-export --no-auto-update --secret-env-vars' if mode != 'old-cli' else '-p'); sys.exit(0)
if mode == 'timeout': print('partial', flush=True); time.sleep(30)
if mode == 'deny': print('tool permission denied', file=sys.stderr); sys.exit(2)
if mode == 'empty': sys.exit(0)
if mode == 'malformed': sys.stdout.buffer.write(b'bad\\x00report'); sys.exit(0)
if mode == 'secret': print('The token is ' + os.environ['COPILOT_GITHUB_TOKEN']); sys.exit(0)
print('Ready plan: inspect reports. No changes made.')
""")
        self.bin.chmod(0o755)
        self.capture = self.root / "capture.json"
        self.report = self.project / "docs/agents/report.md"

    def run_job(self, **overrides):
        mode = overrides.pop("mode", None)
        mode_file = self.root / "mode"
        if mode:
            mode_file.write_text(mode)
        else:
            mode_file.unlink(missing_ok=True)
        env = dict(os.environ, COPILOT_HOME=str(self.root), COPILOT_MODEL="test-model")
        env.update(overrides.pop("env", {}))
        return automation.run_job(
            job=overrides.pop("job", "update"), project=self.project,
            blueprint=self.blueprint, report=self.report, binary=self.bin,
            model=overrides.pop("model", "test-model"),
            timeout=overrides.pop("timeout", 3), environ=env,
            **overrides,
        )

    def test_read_only_copilot_contract_and_controlled_environment(self):
        result = self.run_job(env={"COPILOT_ALLOW_ALL": "true", "UNRELATED_SECRET": "x"})
        self.assertEqual(result, 0)
        capture = json.loads(self.capture.read_text())
        argv = capture["argv"]
        self.assertEqual(Path(capture["cwd"]), self.project.resolve())
        self.assertIn("--available-tools=read", argv)
        self.assertIn("--allow-tool=read", argv)
        self.assertIn("--no-ask-user", argv)
        self.assertIn("--model=test-model", argv)
        self.assertEqual(capture["allow_all"], "false")
        self.assertNotIn("UNRELATED_SECRET", capture["env"])
        self.assertFalse(any("claude" in part.lower() or "push" in part.lower() for part in argv if part.startswith("--")))
        self.assertIn("Ready plan", self.report.read_text())

    def test_failure_and_partial_output_preserve_last_good(self):
        self.assertEqual(self.run_job(), 0)
        before = self.report.read_bytes()
        self.assertNotEqual(self.run_job(mode="deny"), 0)
        self.assertEqual(self.report.read_bytes(), before)
        self.assertEqual((self.report.with_suffix(".md.last-good")).read_bytes(), before)
        self.assertNotEqual(self.run_job(mode="empty"), 0)
        self.assertEqual(self.report.read_bytes(), before)
        self.assertNotEqual(self.run_job(mode="malformed"), 0)
        self.assertEqual(self.report.read_bytes(), before)

    def test_timeout_is_bounded_and_preserves_report(self):
        self.report.write_text("old")
        self.assertNotEqual(self.run_job(timeout=1, mode="timeout"), 0)
        self.assertEqual(self.report.read_text(), "old")

    def test_preflight_never_runs_prompt_and_missing_model_is_actionable(self):
        env = dict(os.environ, COPILOT_HOME=str(self.root))
        self.assertNotEqual(automation.run_job(job="triage", project=self.project,
                            blueprint=None, report=self.report, binary=self.bin,
                            model="", timeout=2, environ=env), 0)
        self.assertFalse(self.report.exists())

    def test_unsupported_cli_flag_stops_before_inference(self):
        self.assertNotEqual(self.run_job(mode="old-cli"), 0)
        self.assertFalse(self.report.exists())
        capture = json.loads(self.capture.read_text())
        self.assertEqual(capture["argv"], ["--help"])

    def test_stale_lock_is_recovered_without_killing_live_owner(self):
        lock = self.project / ".rpi/local/copilot/locks/update.lock"
        lock.parent.mkdir(parents=True)
        lock.write_text('{"pid":999999,"token":"old"}')
        self.assertEqual(self.run_job(), 0)
        self.assertTrue(lock.exists())
        self.assertNotEqual(json.loads(lock.read_text())["pid"], 999999)

    def test_live_lock_is_not_recovered(self):
        lock = self.project / ".rpi/local/copilot/locks/update.lock"
        lock.parent.mkdir(parents=True)
        with lock.open("w") as owned:
            fcntl.flock(owned, fcntl.LOCK_EX | fcntl.LOCK_NB)
            owned.write('{"pid":1,"token":"other"}')
            owned.flush()
            self.assertNotEqual(self.run_job(), 0)
            self.assertTrue(lock.exists())
            self.assertFalse(self.report.exists())

    def test_symlinked_lock_and_parent_preserve_external_bytes(self):
        outside = self.root / "owner.lock"
        outside.write_bytes(b"owner bytes")
        lock = self.project / ".rpi/local/copilot/locks/triage.lock"
        lock.parent.mkdir(parents=True)
        lock.symlink_to(outside)
        self.assertNotEqual(self.run_job(job="triage"), 0)
        self.assertEqual(outside.read_bytes(), b"owner bytes")
        self.assertTrue(lock.is_symlink())
        lock.unlink()
        lock.parent.rmdir()
        external_dir = self.root / "external-locks"
        external_dir.mkdir()
        lock.parent.symlink_to(external_dir, target_is_directory=True)
        self.assertNotEqual(self.run_job(job="triage"), 0)
        self.assertFalse((external_dir / "triage.lock").exists())

    def test_lock_inode_persists_so_runner_cannot_split_its_own_lock(self):
        lock = self.project / ".rpi/local/copilot/locks/update.lock"
        lock.parent.mkdir(parents=True)
        lock.write_text("stale metadata")
        original_inode = lock.stat().st_ino
        original_unlink = Path.unlink
        split_results = []

        def probe_unlink(path, *args, **kwargs):
            result = original_unlink(path, *args, **kwargs)
            if path == lock and not split_results:
                # Old implementation has released the path while retaining its
                # flock. A concurrent runner can now lock a different inode.
                split_results.append(None)
                split_results[0] = self.run_job()
            return result

        with mock.patch.object(Path, "unlink", probe_unlink):
            self.assertEqual(self.run_job(), 0)
        self.assertEqual(split_results, [])
        self.assertTrue(lock.exists())
        self.assertEqual(lock.stat().st_ino, original_inode)

    def test_report_redacts_forwarded_credential(self):
        self.assertEqual(self.run_job(mode="secret", env={"COPILOT_GITHUB_TOKEN": "secret-token-123"}), 0)
        self.assertNotIn("secret-token-123", self.report.read_text())
        self.assertIn("[REDACTED]", self.report.read_text())

    def test_all_forwarded_credentials_are_hidden_from_copilot_tools(self):
        credentials = {name: f"secret-{name}" for name in (
            "COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "COPILOT_PROVIDER_API_KEY")}
        self.assertEqual(self.run_job(env=credentials), 0)
        argv = json.loads(self.capture.read_text())["argv"]
        self.assertIn("--secret-env-vars=" + ",".join(credentials), argv)
        for value in credentials.values():
            self.assertNotIn(value, json.dumps(argv))

    def test_scheduler_preview_has_no_side_effects(self):
        proc = subprocess.run([sys.executable, str(RUNNER), "schedule-preview", "--job", "triage",
                               "--project", str(self.project)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("rpi-automation.py run --job triage", proc.stdout)
        self.assertFalse((self.project / ".rpi").exists())
        self.assertFalse(self.capture.exists())

    def test_launchd_installer_previews_and_preserves_unrelated_plist(self):
        agent_dir = self.project / "scripts/agents"
        (agent_dir / "lib").mkdir(parents=True)
        installer = agent_dir / "install-agents.sh"
        shutil.copy2(ROOT / "templates/scripts/agents/install-agents.sh", installer)
        shutil.copy2(ROOT / "templates/scripts/agents/lib/agent-utils.sh", agent_dir / "lib/agent-utils.sh")
        (agent_dir / "nightly.sh").write_text("#!/bin/bash\n# SCHEDULE: daily 03:00\n# RPI_AUTOMATION_MODE: report-only\n")
        home = self.root / "home"
        home.mkdir()
        env = dict(os.environ, HOME=str(home), COPILOT_MODEL="test-model", COPILOT_BIN=str(self.bin), COPILOT_HOME=str(self.root))
        preview = subprocess.run(["bash", str(installer)], env=env, capture_output=True, text=True)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn("nightly", preview.stdout)
        self.assertFalse((home / "Library/LaunchAgents").exists())
        plist = home / f"Library/LaunchAgents/com.{self.project.name}.nightly.plist"
        plist.parent.mkdir(parents=True)
        plist.write_text("owner-customized")
        # Explicit activation must refuse an unmanaged existing registration.
        activated = subprocess.run(["bash", str(installer), "--activate"], env=env, capture_output=True, text=True)
        self.assertNotEqual(activated.returncode, 0)
        self.assertEqual(plist.read_text(), "owner-customized")

    def test_explicit_launchd_activation_registers_only_marked_agent(self):
        agent_dir = self.project / "scripts/agents"
        (agent_dir / "lib").mkdir(parents=True)
        installer = agent_dir / "install-agents.sh"
        shutil.copy2(ROOT / "templates/scripts/agents/install-agents.sh", installer)
        shutil.copy2(ROOT / "templates/scripts/agents/lib/agent-utils.sh", agent_dir / "lib/agent-utils.sh")
        marked = agent_dir / "nightly.sh"
        marked.write_text("#!/bin/bash\n# SCHEDULE: daily 03:00\n# RPI_AUTOMATION_MODE: report-only\n")
        (agent_dir / "legacy.sh").write_text("#!/bin/bash\n# SCHEDULE: daily 04:00\n")
        home = self.root / "home"
        home.mkdir()
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        launcher = bin_dir / "launchctl"
        launcher.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$LAUNCH_LOG\"\n")
        launcher.chmod(0o755)
        launch_log = self.root / "launch.log"
        env = dict(os.environ, HOME=str(home), COPILOT_MODEL="test-model", COPILOT_BIN=str(self.bin),
                   COPILOT_HOME=str(self.root), PATH=f"{bin_dir}:{os.environ['PATH']}", LAUNCH_LOG=str(launch_log))
        proc = subprocess.run(["bash", str(installer), "--activate"], env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        plist = home / f"Library/LaunchAgents/com.{self.project.name}.nightly.plist"
        self.assertTrue(plist.exists())
        value = plistlib.loads(plist.read_bytes())
        self.assertEqual(value["ProgramArguments"], ["/bin/bash", str(marked)])
        self.assertEqual(value["EnvironmentVariables"]["COPILOT_MODEL"], "test-model")
        self.assertFalse((plist.parent / f"com.{self.project.name}.legacy.plist").exists())
        self.assertIn("bootstrap", launch_log.read_text())

    def test_launchd_staging_symlink_cannot_overwrite_external_file(self):
        agent_dir = self.project / "scripts/agents"
        (agent_dir / "lib").mkdir(parents=True)
        installer = agent_dir / "install-agents.sh"
        shutil.copy2(ROOT / "templates/scripts/agents/install-agents.sh", installer)
        shutil.copy2(ROOT / "templates/scripts/agents/lib/agent-utils.sh", agent_dir / "lib/agent-utils.sh")
        (agent_dir / "nightly.sh").write_text("#!/bin/bash\n# SCHEDULE: daily 03:00\n# RPI_AUTOMATION_MODE: report-only\n")
        home = self.root / "home"
        plist_dir = home / "Library/LaunchAgents"
        plist_dir.mkdir(parents=True)
        plist = plist_dir / f"com.{self.project.name}.nightly.plist"
        outside = self.root / "owner.plist"
        outside.write_bytes(b"owner bytes")
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        launcher = bin_dir / "launchctl"
        launcher.write_text("#!/bin/sh\nexit 0\n")
        launcher.chmod(0o755)
        env = dict(os.environ, HOME=str(home), COPILOT_MODEL="test-model", COPILOT_BIN=str(self.bin),
                   COPILOT_HOME=str(self.root), PATH=f"{bin_dir}:{os.environ['PATH']}",
                   OUTSIDE=str(outside), PLIST=str(plist), INSTALLER=str(installer))
        proc = subprocess.run(["bash", "-c", 'ln -s "$OUTSIDE" "$PLIST.tmp.$$"; exec bash "$INSTALLER" --activate'],
                              env=env, capture_output=True, text=True)
        self.assertEqual(outside.read_bytes(), b"owner bytes")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_launchd_dangling_target_symlink_is_preserved(self):
        agent_dir = self.project / "scripts/agents"
        (agent_dir / "lib").mkdir(parents=True)
        installer = agent_dir / "install-agents.sh"
        shutil.copy2(ROOT / "templates/scripts/agents/install-agents.sh", installer)
        shutil.copy2(ROOT / "templates/scripts/agents/lib/agent-utils.sh", agent_dir / "lib/agent-utils.sh")
        (agent_dir / "nightly.sh").write_text("#!/bin/bash\n# SCHEDULE: daily 03:00\n# RPI_AUTOMATION_MODE: report-only\n")
        home = self.root / "home"
        plist_dir = home / "Library/LaunchAgents"
        plist_dir.mkdir(parents=True)
        plist = plist_dir / f"com.{self.project.name}.nightly.plist"
        plist.symlink_to(self.root / "missing-owner.plist")
        env = dict(os.environ, HOME=str(home), COPILOT_MODEL="test-model", COPILOT_BIN=str(self.bin),
                   COPILOT_HOME=str(self.root))
        proc = subprocess.run(["bash", str(installer), "--activate"], env=env, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(plist.is_symlink())


if __name__ == "__main__":
    unittest.main()
