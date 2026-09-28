#!/usr/bin/env python3
"""Bounded, report-only Copilot jobs for opt-in local scheduling.

Programmatic CLI flags follow GitHub's Copilot CLI programmatic reference:
https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference
This runner does not activate a scheduler or run an inference preflight.
"""

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid


REQUIRED_FLAGS = ("-p", "-s", "--no-ask-user", "--available-tools", "--allow-tool", "--model", "--no-remote", "--no-remote-export", "--no-auto-update", "--secret-env-vars")
MAX_OUTPUT = 1024 * 1024


def clean_env(source, model):
    allowed = ("HOME", "PATH", "TERM", "COPILOT_HOME", "COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "COPILOT_PROVIDER_BASE_URL", "COPILOT_PROVIDER_API_KEY")
    env = {key: source[key] for key in allowed if source.get(key)}
    env.update(COPILOT_MODEL=model, COPILOT_ALLOW_ALL="false", COPILOT_AUTO_UPDATE="false", GIT_TERMINAL_PROMPT="0", CI="1", NO_COLOR="1")
    return env


def redact(value, env):
    value = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", value)
    value = "".join(ch for ch in value if ch in "\n\t" or ord(ch) >= 32)
    for key in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "COPILOT_PROVIDER_API_KEY"):
        secret = env.get(key)
        if secret:
            value = value.replace(secret, "[REDACTED]")
    return value


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def command(argv, *, cwd, env, timeout):
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, err = process.communicate()
        return 124, out, err
    return process.returncode, out, err


def preflight(binary, project, env):
    resolved = shutil.which(str(binary), path=env.get("PATH"))
    if not resolved:
        raise ValueError("Copilot CLI missing; install it or set COPILOT_BIN to its executable path")
    binary = str(Path(resolved).resolve())
    for flag in ("--version", "--help"):
        code, out, err = command([binary, flag], cwd=project, env=env, timeout=5)
        if code:
            raise ValueError(f"Copilot CLI {flag} failed; check installation (exit {code})")
        if flag == "--help":
            help_text = (out + err).decode("utf-8", "replace")
            missing = [item for item in REQUIRED_FLAGS if item not in help_text]
            if missing:
                raise ValueError(f"Copilot CLI lacks required flags: {', '.join(missing)}; update the CLI")
    return binary


def open_owned_lock(project, job):
    """Acquire one persistent lock inode without following path aliases."""
    if not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")):
        raise ValueError("Scheduled jobs require POSIX no-follow directory and file opens")
    directory = os.open(project, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in (".rpi", "local", "copilot", "locks"):
            try:
                os.mkdir(component, mode=0o700, dir_fd=directory)
            except FileExistsError:
                pass
            try:
                child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=directory)
            except OSError as exc:
                raise ValueError(f"Unsafe lock parent {component}; preserve it and inspect its owner") from exc
            os.close(directory)
            directory = child
        name = f"{job}.lock"
        try:
            descriptor = os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                                 0o600, dir_fd=directory)
        except OSError as exc:
            raise ValueError("Unsafe scheduled-job lock; preserve it and inspect its owner") from exc
        try:
            node = os.fstat(descriptor)
            if not stat.S_ISREG(node.st_mode) or node.st_nlink != 1:
                raise ValueError("Scheduled-job lock must be one regular, unaliased file")
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if ((current.st_dev, current.st_ino) != (node.st_dev, node.st_ino)
                    or current.st_nlink != 1):
                raise ValueError("Scheduled-job lock changed during acquisition")
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise
    finally:
        os.close(directory)


def prompt_for(job, project, blueprint):
    boundary = "Only read files. Do not edit, commit, push, merge, create issues, call remote tools, or approve action items. Return a concise Markdown report with evidence paths and a ready plan for owner review."
    if job == "update":
        if blueprint is None:
            raise ValueError("Update discovery needs --blueprint or COPILOT_RPI_PATH")
        skill = blueprint / "templates/skills/rpi-update/SKILL.md"
        if not skill.is_file():
            raise ValueError(f"Missing update skill: {skill}; set COPILOT_RPI_PATH to a complete blueprint")
        if skill.stat().st_size > 100_000:
            raise ValueError("Update skill exceeds 100 KB; inspect the blueprint before scheduling")
        instructions = skill.read_text(encoding="utf-8")
        return f"Inspect project {project} for Copilot RPI update needs. The source blueprint is {blueprint}. Treat this skill as task context, but stop before its apply step.\n\n{instructions}\n\n{boundary}"
    return f"Inspect local agent reports and failure logs in project {project}. List every finding and produce a ready triage plan. If a required GitHub alert inventory is unavailable with read-only local tools, mark it unmeasured.\n\n{boundary}"


def run_job(*, job, project, blueprint, report, binary, model, timeout, environ=None):
    source = os.environ if environ is None else environ
    try:
        project = Path(project).resolve(strict=True)
        if not project.is_dir():
            raise ValueError("Project must be a directory")
        blueprint = Path(blueprint).resolve(strict=True) if blueprint else None
        report = Path(report)
        report = (project / report).resolve() if not report.is_absolute() else report.resolve()
        if not report.is_relative_to(project):
            raise ValueError("Report must stay inside the project")
        if not model or not model.strip():
            raise ValueError("No model selected; set COPILOT_MODEL or pass --model for this scheduled job")
        if timeout < 1 or timeout > 3600:
            raise ValueError("Timeout must be 1-3600 seconds")
        env = clean_env(source, model.strip())
        prompt = prompt_for(job, project, blueprint)
        binary = preflight(binary, project, env)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    lock_path = project / ".rpi/local/copilot/locks" / f"{job}.lock"
    try:
        lock_descriptor = open_owned_lock(project, job)
    except BlockingIOError:
        print(f"BLOCKED: {job} already runs; inspect {lock_path}", file=sys.stderr)
        return 3
    except (OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    token = uuid.uuid4().hex
    with os.fdopen(lock_descriptor, "r+") as lock:
        lock.seek(0)
        lock.truncate()
        json.dump({"pid": os.getpid(), "token": token, "started": int(time.time())}, lock)
        lock.flush()
        os.fsync(lock.fileno())
        argv = [binary, "-p", prompt, "-s", "--no-ask-user", "--available-tools=read",
                "--allow-tool=read", f"--model={model.strip()}", "--no-remote",
                "--no-remote-export", "--no-auto-update"]
        secrets = [key for key in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN",
                                   "COPILOT_PROVIDER_API_KEY") if env.get(key)]
        if secrets:
            argv.append(f"--secret-env-vars={','.join(secrets)}")
        try:
            code, out, err = command(argv, cwd=project, env=env, timeout=timeout)
        except OSError as exc:
            print(f"FAILED: Copilot CLI could not start: {exc.strerror}; check COPILOT_BIN", file=sys.stderr)
            return 2
        malformed = len(out) > MAX_OUTPUT or b"\x00" in out
        try:
            out.decode("utf-8", "strict")
        except UnicodeDecodeError:
            malformed = True
        response = redact(out.decode("utf-8", "replace"), env).strip()
        diagnostic = redact(err.decode("utf-8", "replace"), env).strip()
        if malformed or not response:
            code = code or 4
            if not diagnostic:
                diagnostic = "Empty, malformed or oversized Copilot output"
        if re.search(r"(?i)(permission denied|authentication (failed|required)|not authenticated|unknown option|unknown model|model unavailable)", response + "\n" + diagnostic):
            code = code or 4
        if code:
            if code == 124:
                hint = "Copilot timed out; inspect the task or increase --timeout within the 3600-second cap"
            else:
                hint = "Check Copilot authentication, selected model and read-tool permission; rerun after repair"
            print(f"FAILED: {job} exit {code}. {hint}. {diagnostic[:300]}", file=sys.stderr)
            return code
        body = (f"# {job.title()} discovery report\n\n{response}\n").encode("utf-8")
        try:
            atomic_write(report, body)
            atomic_write(report.with_suffix(report.suffix + ".last-good"), body)
        except OSError as exc:
            print(f"FAILED: cannot write report or last good copy: {exc.strerror}; check directory permissions", file=sys.stderr)
            return 2
        print(f"OK: {report}")
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "schedule-preview"):
        part = commands.add_parser(name)
        part.add_argument("--job", choices=("update", "triage"), required=True)
        part.add_argument("--project", type=Path, required=True)
        part.add_argument("--blueprint", type=Path, default=Path(os.environ["COPILOT_RPI_PATH"]) if os.environ.get("COPILOT_RPI_PATH") else None)
        part.add_argument("--model", default=os.environ.get("COPILOT_MODEL", ""))
        part.add_argument("--report", type=Path)
        part.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)
    if args.command == "schedule-preview":
        runner = Path(__file__).resolve()
        arguments = ["python3", str(runner), "run", "--job", args.job,
                     "--project", str(args.project.resolve())]
        if args.blueprint:
            arguments += ["--blueprint", str(args.blueprint.resolve())]
        if args.model:
            arguments += ["--model", args.model]
        if args.report:
            arguments += ["--report", str(args.report)]
        if args.timeout != 900:
            arguments += ["--timeout", str(args.timeout)]
        command_line = shlex.join(arguments)
        print(f"Preview only. Review project, model, authentication and environment before activating a scheduler.\nCron: 0 {'3' if args.job == 'update' else '7'} * * * {command_line}\nlaunchd ProgramArguments: {json.dumps(arguments)}\nNo job was installed or started.")
        return 0
    default_name = "copilot-rpi-update-report.md" if args.job == "update" else "triage-report.md"
    report = args.report or args.project / "docs/agents" / default_name
    return run_job(job=args.job, project=args.project, blueprint=args.blueprint,
                   report=report, binary=os.environ.get("COPILOT_BIN", "copilot"),
                   model=args.model, timeout=args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
