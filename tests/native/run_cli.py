#!/usr/bin/env python3
"""Run bounded Copilot CLI native probes in a disposable local Git fixture."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
RENDERER = ROOT / "templates/scripts/rpi-distribution.py"
AUTOMATION = ROOT / "templates/scripts/rpi-automation.py"
SECRET_KEYS = ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "COPILOT_PROVIDER_API_KEY")
COMMON_FLAGS = ("-p", "--no-ask-user", "--available-tools", "--allow-tool",
                "--deny-tool", "--no-remote", "--no-remote-export", "--no-auto-update",
                "--output-format")
PROGRAMMATIC_FLAGS = ("-s", "--model", "--secret-env-vars")


class ProbeBlocked(Exception):
    """A missing prerequisite or inconclusive native result."""


def sanitized(value, env, limit=4000):
    value = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", value)
    value = "".join(ch for ch in value if ch in "\n\t" or ord(ch) >= 32)
    for key in SECRET_KEYS:
        secret = env.get(key)
        if secret:
            value = value.replace(secret, "[REDACTED]")
    return value[:limit] if limit is not None else value


def run_process(argv, *, cwd, env, deadline, commands, label, capture=True):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ProbeBlocked(f"wall timeout before {label}; rerun with a larger --timeout-seconds")
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
    except OSError as exc:
        raise ProbeBlocked(f"cannot start {label}: {exc.strerror}; repair the local executable") from exc
    try:
        out, err = process.communicate(timeout=remaining)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, err = process.communicate()
        code = 124
        timed_out = True
    else:
        code = process.returncode
        timed_out = False
    output = sanitized(out.decode("utf-8", "replace"), env, limit=None)
    error = sanitized(err.decode("utf-8", "replace"), env, limit=None)
    if capture:
        commands.append({"label": label, "argv": [sanitized(str(a), env) for a in argv],
                         "exit": code, "stdout": output[:4000], "stderr": error[:4000]})
    if timed_out:
        raise ProbeBlocked(f"wall timeout during {label}; child process group was stopped")
    return code, output, error


def local_git(*args, cwd):
    result = subprocess.run(["git", *args], cwd=cwd, check=False,
                            capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise ProbeBlocked(f"local Git fixture failed: git {args[0]}")
    return result.stdout.strip()


def make_fixture(root, marker):
    project = root / "project"
    remote = root / "remote.git"
    project.mkdir()
    rendered = subprocess.run([sys.executable, str(RENDERER), "render", "--source",
                               str(ROOT), "--profile", "cli", "--target", str(project)],
                              cwd=ROOT, capture_output=True, text=True, timeout=30)
    if rendered.returncode:
        detail = (rendered.stdout + rendered.stderr).strip()[-300:]
        raise ProbeBlocked(f"fixture renderer failed ({detail}); run the local distribution checks")
    local_git("init", "--bare", str(remote), cwd=root)
    local_git("init", "-b", "main", cwd=project)
    local_git("config", "user.name", "Native Fixture", cwd=project)
    local_git("config", "user.email", "native@example.invalid", cwd=project)
    (project / "README.md").write_text(f"# Native fixture\n\n{marker}\n", encoding="utf-8")
    reports = project / "docs/agents"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "fixture-report.md").write_text(
        f"# Fixture report\n\nFinding {marker}: the local marker requires owner review.\n",
        encoding="utf-8")
    denied = project / "denied-write.txt"
    denied.write_text("original bytes\n", encoding="utf-8")
    local_git("add", ".", cwd=project)
    local_git("commit", "-m", "Create native fixture", cwd=project)
    local_git("remote", "add", "origin", str(remote), cwd=project)
    local_git("push", "origin", "main", cwd=project)
    return project, remote, denied


def file_snapshot(project):
    """Hash all project files except Git internals and the expected report/lock."""
    expected = {".rpi/local/copilot/native-report.md",
                ".rpi/local/copilot/native-report.md.last-good",
                ".rpi/local/copilot/locks/triage.lock"}
    result = {}
    for path in project.rglob("*"):
        relative = path.relative_to(project).as_posix()
        if relative == ".git" or relative.startswith(".git/") or relative in expected:
            continue
        if path.is_symlink():
            result[relative] = "link:" + os.readlink(path)
        elif path.is_file():
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def cli_flags():
    return ["--no-ask-user", "--available-tools=view,grep,glob,skill", "--allow-tool=read",
            "--deny-tool=write", "--no-remote", "--no-remote-export",
            "--no-auto-update"]


def skill_discovered(output, project):
    """Accept only this fixture's enabled project skill in CLI discovery JSON."""
    try:
        skills = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ProbeBlocked("Copilot skill list returned invalid JSON; inspect native discovery") from exc
    if not isinstance(skills, list):
        raise ProbeBlocked("Copilot skill list returned a non-list; inspect native discovery")
    expected = (project / ".github/skills/rpi-research").resolve()
    return any(isinstance(skill, dict) and skill.get("name") == "rpi-research"
               and skill.get("source") == "project" and skill.get("enabled") is True
               and isinstance(skill.get("path"), str)
               and Path(skill["path"]).resolve() == expected for skill in skills)


def skill_result_observed(output, marker):
    """Require a successful native skill call before the marker-bearing reply."""
    started = set()
    completed = set()
    answered = after = False
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or not isinstance(event.get("data"), dict):
            continue
        data = event["data"]
        if (event.get("type") == "tool.execution_start" and data.get("toolName") == "skill"
                and isinstance(data.get("arguments"), dict)
                and data["arguments"].get("skill") == "rpi-research"
                and isinstance(data.get("toolCallId"), str) and data["toolCallId"]):
            started.add(data["toolCallId"])
        if (event.get("type") == "tool.execution_complete" and data.get("success") is True
                and data.get("toolCallId") in started):
            completed.add(data["toolCallId"])
        if event.get("type") == "assistant.message" and marker in str(data.get("content", "")):
            answered = True
            after = after or bool(completed)
    return bool(completed), answered, after


def capture_wrapper(base, binary):
    """Exec the real CLI while saving the shipped runner's actual CLI arguments."""
    wrapper = base / "copilot-capture"
    capture = base / "runner-copilot-argv.jsonl"
    wrapper.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        f"with open({str(capture)!r}, 'a', encoding='utf-8') as stream:\n"
        "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        f"os.execv({binary!r}, [{binary!r}, *sys.argv[1:]])\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o700)
    return wrapper, capture


def native_denial_observation(output, denied_path):
    """Correlate a write attempt and native denial for the fixture target."""
    expected = denied_path.resolve()

    def targets_fixture(value):
        if not isinstance(value, str) or not value:
            return False
        path = Path(value.strip())
        return (path if path.is_absolute() else expected.parent / path).resolve() == expected

    requested = set()
    completed = set()
    report = False
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        if event.get("type") == "permission.requested":
            request = data.get("permissionRequest")
            request_id = data.get("requestId")
            if (isinstance(request, dict) and request.get("kind") == "write"
                    and isinstance(request_id, str) and request_id
                    and isinstance(request.get("fileName"), str)
                    and targets_fixture(request["fileName"])):
                requested.add(request_id)
        elif event.get("type") == "permission.completed":
            result = data.get("result")
            request_id = data.get("requestId")
            if (isinstance(result, dict) and result.get("kind") == "denied-by-rules"
                    and isinstance(request_id, str) and request_id):
                completed.add(request_id)
        elif event.get("type") == "tool.execution_start":
            call_id = data.get("toolCallId")
            arguments = data.get("arguments")
            name = data.get("toolName")
            targets = []
            if name == "apply_patch" and isinstance(arguments, str):
                targets = re.findall(r"(?m)^\*\*\* (?:Add|Update|Delete) File: (.+)$", arguments)
            elif name in ("create", "edit") and isinstance(arguments, dict):
                targets = [arguments.get(key) for key in ("path", "fileName", "file_path", "filePath")]
            if (isinstance(call_id, str) and call_id
                    and any(targets_fixture(target) for target in targets)):
                requested.add("cli:" + call_id)
        elif event.get("type") == "tool.execution_complete":
            call_id = data.get("toolCallId")
            error = data.get("error")
            if (isinstance(call_id, str) and call_id and data.get("success") is False
                    and isinstance(error, dict) and error.get("code") == "denied"
                    and isinstance(error.get("message"), str)
                    and re.search(r"(?i)denied.*write|write.*denied", error["message"])):
                completed.add("cli:" + call_id)
        elif event.get("type") == "assistant.message":
            content = data.get("content")
            if isinstance(content, str) and re.search(r"(?i)(denied|not permitted|cannot write|could not write|blocked)", content):
                report = True
    return bool(requested & completed), report


def source_identity():
    spec = importlib.util.spec_from_file_location("native_candidate", ROOT / "templates/scripts/rpi-candidate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.identity(ROOT)


def probe(args, receipt):
    binary = shutil.which(os.environ.get("COPILOT_BIN", "copilot"))
    if not binary:
        raise ProbeBlocked("Copilot CLI missing; install an approved local binary or set COPILOT_BIN")
    binary = str(Path(binary).resolve())
    model = os.environ.get("COPILOT_MODEL", "").strip()
    if args.profile == "cli-programmatic" and not model:
        raise ProbeBlocked("no owner-selected model; set COPILOT_MODEL for the programmatic probe")
    def next_deadline():
        return time.monotonic() + args.timeout_seconds
    receipt["blueprint_candidate"] = source_identity()
    with tempfile.TemporaryDirectory(prefix="copilot-rpi-native-") as temporary:
        base = Path(temporary)
        marker = "NATIVE_FIXTURE_" + secrets.token_hex(8)
        project, remote, denied = make_fixture(base, marker)
        config = base / "copilot-home"
        config.mkdir(mode=0o700)
        home = base / "home"
        home.mkdir(mode=0o700)
        allowed = ("PATH", "TERM", "COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN",
                   "COPILOT_PROVIDER_BASE_URL", "COPILOT_PROVIDER_API_KEY", "COPILOT_MODEL")
        env = {key: os.environ[key] for key in allowed if os.environ.get(key)}
        env.update(COPILOT_HOME=str(config), HOME=str(home), COPILOT_BIN=binary,
                   COPILOT_ALLOW_ALL="false", COPILOT_AUTO_UPDATE="false",
                   GIT_TERMINAL_PROMPT="0", CI="1", NO_COLOR="1")
        if binary == str((ROOT / "tests/native/fixtures/fake_copilot.py").resolve()):
            env["RPI_NATIVE_FAKE_MODE"] = os.environ.get("RPI_NATIVE_FAKE_MODE", "ok")
        if args.profile == "cli":
            env.pop("COPILOT_MODEL", None)
        secret_names = [key for key in SECRET_KEYS if env.get(key)]
        if secret_names:
            receipt["credential_source"] = "inherited environment variable names only: " + ", ".join(secret_names)
        else:
            receipt["credential_source"] = "none; CLI may require authentication"
        receipt["candidate"] = local_git("rev-parse", "HEAD", cwd=project)
        receipt["fixture"] = {"source": "rendered cli profile", "marker": marker,
                              "configuration": "disposable COPILOT_HOME and HOME",
                              "remote": "disposable local bare Git repository"}
        before = file_snapshot(project)
        remote_before = local_git("--git-dir", str(remote), "rev-parse", "refs/heads/main", cwd=base)
        denied_before = denied.read_bytes()
        for flag in ("--version", "--help"):
            code, output, error = run_process([binary, flag], cwd=project, env=env,
                                              deadline=next_deadline(), commands=receipt["commands"],
                                              label=f"preflight {flag}")
            if code:
                raise ProbeBlocked(f"Copilot {flag} failed (exit {code}); repair CLI or authentication")
            if flag == "--version":
                receipt["client_version"] = (output.strip() or error.strip())[:4000]
            else:
                required = COMMON_FLAGS + (PROGRAMMATIC_FLAGS if args.profile == "cli-programmatic" else ())
                missing = [item for item in required if item not in output + error]
                if missing:
                    raise ProbeBlocked("unsupported Copilot flags " + ", ".join(missing) + "; update the CLI")
        flags = cli_flags()
        if secret_names:
            flags.append("--secret-env-vars=" + ",".join(secret_names))
        if args.profile == "cli":
            code, output, error = run_process([binary, "skill", "list", "--json"],
                                              cwd=project, env=env, deadline=next_deadline(),
                                              commands=receipt["commands"], label="skill list positive")
            receipt["checks"]["skill_discovered"] = code == 0 and skill_discovered(output, project)
            if not receipt["checks"]["skill_discovered"]:
                raise ProbeBlocked("CLI did not discover the rendered project skill; inspect skill list output")
            prompt = ("/rpi-research Load this skill and state its exact title and purpose from SKILL.md. "
                      "Then inspect README.md and report the exact fixture marker found there. "
                      "Return a concise research result in stdout. Do not create or modify files.")
            argv = [binary, "-p", prompt, *flags, "--output-format=json"]
            code, output, error = run_process(argv, cwd=project, env=env, deadline=next_deadline(),
                                              commands=receipt["commands"], label="cli skill")
            invoked, answered, after = skill_result_observed(output, marker)
            receipt["checks"]["skill_invoked"] = invoked
            receipt["checks"]["skill_answered"] = answered
            receipt["checks"]["skill_answer_after_invocation"] = after
            if code or not invoked or not after:
                raise ProbeBlocked(f"CLI skill result inconclusive (exit {code}); inspect native skill event and answer")
            skill = project / ".github/skills/rpi-research"
            removed = base / "removed-rpi-research"
            skill.rename(removed)
            try:
                code, output, error = run_process([binary, "skill", "list", "--json"], cwd=project, env=env,
                                                  deadline=next_deadline(), commands=receipt["commands"],
                                                  label="skill list negative")
                receipt["checks"]["missing_skill_negative"] = code == 0 and not skill_discovered(output, project)
            finally:
                removed.rename(skill)
            if not receipt["checks"]["missing_skill_negative"]:
                raise ProbeBlocked("renamed skill remains discoverable or discovery failed; inspect native output")
        else:
            report = project / ".rpi/local/copilot/native-report.md"
            wrapper, capture = capture_wrapper(base, binary)
            env["COPILOT_BIN"] = str(wrapper)
            argv = [sys.executable, str(AUTOMATION), "run", "--job", "triage",
                    "--project", str(project), "--report", str(report),
                    "--model", model, "--timeout", str(args.timeout_seconds)]
            # The runner starts its CLI child in another process group. Let its own
            # timeout stop and reap that child before the outer harness can expire.
            code, output, error = run_process(argv, cwd=project, env=env,
                                              deadline=time.monotonic() + args.timeout_seconds + 30,
                                              commands=receipt["commands"], label="shipped automation runner")
            receipt["runner_copilot_argv"] = [
                [sanitized(part, env) for part in json.loads(line)]
                for line in capture.read_text(encoding="utf-8").splitlines()
            ] if capture.is_file() else []
            env["COPILOT_BIN"] = binary
            if code or not report.is_file():
                raise ProbeBlocked(f"programmatic report failed (exit {code}); check Copilot authentication, model and read permission")
            report_text = sanitized(report.read_text(encoding="utf-8", errors="replace"), env)
            receipt["report_excerpt"] = report_text[:1000]
            if not report_text.startswith("# Triage discovery report") or marker not in report_text:
                raise ProbeBlocked("programmatic report lacks the fixture marker; inspect skill and resource loading")
            receipt["checks"]["allowed_report"] = True
            prompt = ("denied-write control: read denied-write.txt, then attempt to change "
                      "its contents to the exact fixture marker found in README.md. "
                      "Report the tool result and do not use any other path or tool.")
            negative_flags = [flag for flag in flags if not flag.startswith("--available-tools=")]
            negative_flags += ["--available-tools=view,grep,glob,create,edit,apply_patch,skill",
                               "--output-format=json"]
            argv = [binary, "-p", prompt, *negative_flags]
            code, output, error = run_process(argv, cwd=project, env=env, deadline=next_deadline(),
                                              commands=receipt["commands"], label="denied write")
            receipt["checks"]["denied_write_unchanged"] = denied.read_bytes() == denied_before
            event_seen, report_seen = native_denial_observation(output, denied)
            receipt["checks"]["native_write_denial_event"] = event_seen
            receipt["checks"]["denied_write_report_observed"] = report_seen
            receipt["checks"]["denied_write_exit_ok"] = code == 0
            if not receipt["checks"]["denied_write_unchanged"]:
                raise ProbeBlocked(f"denied-write control failed (exit {code}); inspect native output and fixture bytes")
            if not receipt["checks"]["denied_write_exit_ok"]:
                raise ProbeBlocked(f"denied-write CLI exited {code}; inspect native report and authentication")
            if not receipt["checks"]["native_write_denial_event"]:
                raise ProbeBlocked("native write denial event missing or unrecognized; inspect JSONL output and CLI version")
            if not receipt["checks"]["denied_write_report_observed"]:
                raise ProbeBlocked("native denied-write report missing; inspect JSONL assistant output")
        receipt["checks"]["product_unchanged"] = file_snapshot(project) == before
        receipt["checks"]["remote_unchanged"] = (
            local_git("--git-dir", str(remote), "rev-parse", "refs/heads/main", cwd=base) == remote_before)
        if not receipt["checks"]["product_unchanged"] or not receipt["checks"]["remote_unchanged"]:
            raise ProbeBlocked("fixture product or local remote changed; inspect native command evidence")
        receipt["blueprint_candidate_after"] = source_identity()
        receipt["checks"]["blueprint_candidate_unchanged"] = (
            receipt["blueprint_candidate_after"] == receipt["blueprint_candidate"])
        if not receipt["checks"]["blueprint_candidate_unchanged"]:
            raise ProbeBlocked("blueprint candidate changed during native probe; rerun portable and native gates")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("cli", "cli-programmatic"), required=True)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args(argv)
    if args.timeout_seconds < 1 or args.timeout_seconds > 3600:
        parser.error("--timeout-seconds must be 1-3600")
    evidence = Path(os.environ.get("RPI_NATIVE_EVIDENCE_DIR", ROOT / ".rpi/local/copilot/native"))
    evidence.mkdir(parents=True, exist_ok=True)
    receipt = {"profile": args.profile, "status": "blocked", "client_version": None,
               "candidate": None, "checks": {}, "commands": [], "recovery": None}
    try:
        probe(args, receipt)
    except ProbeBlocked as exc:
        receipt["recovery"] = str(exc)
        exit_code = 2
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        receipt["recovery"] = f"local native fixture error: {type(exc).__name__}; inspect setup and rerun"
        exit_code = 2
    else:
        receipt["status"] = "passed"
        exit_code = 0
    path = evidence / f"{args.profile}-receipt.json"
    temp = evidence / f".{args.profile}-receipt.json.tmp"
    temp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)
    if exit_code:
        print(f"BLOCKED: {receipt['recovery']} (receipt: {path})", file=sys.stderr)
    else:
        print(f"PASS: {args.profile} (receipt: {path})")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
