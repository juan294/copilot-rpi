#!/usr/bin/env python3
"""Run Copilot RPI's portable gate and bind results to candidate bytes.

Adapted from cc-rpi 2.1.0, pinned at aa3ea57fb26ae2e1e167acada4b769e073a417f4
in upstream/snapshots/templates/scripts/rpi-verify.py. The custom --checks
option supports fixture execution and never attests the full default suite.
Native Copilot and database acceptance are separate receipts.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid

try:
    _previous_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    _spec = importlib.util.spec_from_file_location('rpi_verify_candidate', Path(__file__).resolve().with_name('rpi-candidate.py'))
    _candidate = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_candidate)
except (OSError, ImportError) as error:
    print(f'BLOCKED / WHY: shared candidate helper unavailable: {error} / FIX: restore the complete declared RPI runtime package', file=sys.stderr)
    raise SystemExit(1) from error
finally:
    sys.dont_write_bytecode = _previous_bytecode
environment, identity = _candidate.environment, _candidate.identity


def required_checks(root):
    """A reviewed adopter inventory, or the Copilot blueprint's own local gate."""
    declaration = root / '.rpi/policy.json'
    if declaration.parent.is_symlink() or declaration.is_symlink():
        raise ValueError('project verification policy must be a regular file')
    if declaration.exists():
        if not declaration.is_file() or declaration.stat().st_nlink != 1:
            raise ValueError('project verification policy must be a regular, unaliased file')

        def unique(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError('duplicate verification policy key: ' + key)
                value[key] = item
            return value

        policy = json.loads(declaration.read_text(encoding='utf-8'), object_pairs_hook=unique)
        if not isinstance(policy, dict) or policy.get('schema_version') != 1:
            raise ValueError('project verification policy requires schema_version 1')
        checks = policy.get('verification_checks')
        validate_checks(checks)
        return checks

    shell_files = sorted(str(path.relative_to(root)) for pattern in (
        'templates/scripts/*.sh', 'templates/scripts/agents/*.sh',
        'templates/scripts/agents/lib/*.sh', 'scripts/*.sh')
        for path in root.glob(pattern))
    if not shell_files:
        raise ValueError('ShellCheck inventory is empty')
    return [
        {'name': 'python-tests', 'argv': ['uv', 'run', '--locked', 'python', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py']},
        {'name': 'catalog-counts', 'argv': ['bash', 'templates/scripts/verify-counts.sh']},
        {'name': 'version', 'argv': ['bash', 'templates/scripts/verify-version.sh']},
        {'name': 'workflow-contracts', 'argv': ['bash', 'templates/scripts/verify-prompts.sh']},
        {'name': 'distribution-schema', 'argv': ['uv', 'run', '--locked', 'python', 'templates/scripts/rpi-distribution.py', 'validate', '--source', '.']},
        {'name': 'generated-output', 'argv': ['uv', 'run', '--locked', 'python', 'templates/scripts/rpi-distribution.py', 'check-generated', '--source', '.']},
        {'name': 'shellcheck', 'argv': ['shellcheck', '--severity=warning', *shell_files]},
        {'name': 'markdownlint', 'argv': ['npm', 'exec', '--', 'markdownlint-cli2', '**/*.md', '#node_modules', '#.venv', '#.claude', '#graphify-out', '#.rpi/local']},
        {'name': 'upstream-provenance', 'argv': ['uv', 'run', '--locked', 'python', 'scripts/check-upstream.py', '--lock', 'upstream/cc-rpi.lock.json', '--inventory', 'upstream/cc-rpi.inventory.json', '--check']},
        {'name': 'internal-links', 'argv': ['uv', 'run', '--locked', 'python', 'scripts/check-links.py']},
    ]


def validate_checks(checks):
    if not isinstance(checks, list) or not checks:
        raise ValueError('required check inventory is empty or invalid')
    names = set()
    for check in checks:
        if (not isinstance(check, dict) or set(check) != {'name', 'argv'}
                or not isinstance(check['name'], str) or not check['name']
                or check['name'] in names or not isinstance(check['argv'], list)
                or not check['argv'] or any(not isinstance(arg, str) or not arg
                                           for arg in check['argv'])):
            raise ValueError('checks require unique names and nonempty literal argv arrays')
        names.add(check['name'])


def safe_output(root, path):
    """Validate a local output without following owner-controlled aliases."""
    path = Path(os.path.abspath(path))
    # Normalize only the caller's root spelling (e.g. macOS /var -> /private/var),
    # preserving descendant components so local symlinks are still rejected.
    for parent in reversed(path.parents):
        if parent.resolve() == root:
            path = root / path.relative_to(parent)
            break
    local = root / '.rpi/local/copilot'
    try:
        relative = path.relative_to(local)
    except ValueError as error:
        raise ValueError('evidence must stay inside .rpi/local without escaping symlinks') from error
    if relative == Path('.'):
        raise ValueError('evidence must name a file inside .rpi/local')
    for parent in (root / '.rpi', local, *path.parents):
        if parent == root:
            break
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise ValueError('verification output has an unsafe parent: ' + str(parent))
    if path.is_symlink() or (path.exists() and (not path.is_file() or path.stat().st_nlink != 1)):
        raise ValueError('verification output must be a regular, unaliased file: ' + str(path))
    return path


def write_receipt(root, path, report):
    path = safe_output(root, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.verification-', suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(report, indent=2) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        safe_output(root, path)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def attempt_lock(root):
    # This standalone verifier ships with the candidate helper, independently of
    # lifecycle installation. Keep the small POSIX locking boundary self-contained.
    try:
        import fcntl
    except ImportError as error:
        raise ValueError('verification requires POSIX advisory locks; use the tested macOS or Linux runtime') from error
    if not hasattr(os, 'O_NOFOLLOW'):
        raise ValueError('verification requires safe no-follow opens; use the tested macOS or Linux runtime')
    path = safe_output(root, root / '.rpi/local/copilot/verification.lock')
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        node = os.fstat(descriptor)
        if not stat.S_ISREG(node.st_mode) or node.st_nlink != 1 or node.st_size:
            raise ValueError('unsafe verification lock; preserve it and inspect its owner')
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('verification is actively locked; wait for the current attempt before retrying') from error
        current = os.stat(path, follow_symlinks=False)
        if ((current.st_dev, current.st_ino) != (node.st_dev, node.st_ino)
                or current.st_nlink != 1 or current.st_size):
            raise ValueError('verification lock changed during acquisition; inspect concurrent writers')
        yield
    finally:
        # Persistent inode prevents split locks; process death also releases it.
        os.close(descriptor)


def ignore_local(root):
    """Keep evidence out of Git status in every clone and worktree; an existing entry is the owner's."""
    try:
        descriptor = os.open(root / '.rpi/local/.gitignore', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    except FileExistsError:
        return  # Never overwrite, and never follow, what is already there.
    with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
        handle.write('*\n')


def run(root, checks, evidence, suite):
    root = root.resolve()
    evidence = safe_output(root, evidence)
    authoritative = safe_output(root, root / '.rpi/local/copilot/verification.json')
    if evidence == root / '.rpi/local/copilot/verification.lock':
        raise ValueError('evidence cannot replace the verification lock')
    validate_checks(checks)
    with attempt_lock(root):
        ignore_local(root)
        attempt = {'schema_version': 1, 'suite': suite, 'attempt_id': uuid.uuid4().hex,
                   'status': 'running', 'passed': False, 'checks': [],
                   'started_at': datetime.now(timezone.utc).isoformat()}
        # Supersede historical success before executing any check. A killed
        # attempt leaves this durable non-success state, including custom output.
        write_receipt(root, authoritative, attempt)
        try:
            if evidence != authoritative:
                write_receipt(root, evidence, attempt)
            return execute_checks(root, checks, evidence, authoritative, attempt)
        except BaseException as error:
            failed = {**attempt, 'status': 'failed', 'error_type': type(error).__name__,
                      'recorded_at': datetime.now(timezone.utc).isoformat()}
            write_receipt(root, authoritative, failed)
            raise


def execute_checks(root, checks, evidence, authoritative, attempt):
    rerun = shlex.join([sys.executable, str(Path(__file__).resolve()), '--root', str(root)])
    before = identity(root)
    runtime_before = environment()
    attempt.update({'identity': before, 'environment': runtime_before})
    write_receipt(root, authoritative, attempt)
    results = []
    for check in checks:
        print(f"\nCHECK {check['name']}", flush=True)
        started = time.monotonic()
        try:
            completed = subprocess.run(check["argv"], cwd=root, check=False)
            code = completed.returncode
        except OSError as error:
            print(f"BLOCKED / WHY: {error} / FIX: restore the declared executable and rerun {rerun}", file=sys.stderr)
            code = 127
        results.append({**check, "exit_code": code,
                        "duration_seconds": round(time.monotonic() - started, 3)})
        attempt['checks'] = results[:]
        write_receipt(root, authoritative, attempt)
    after = identity(root)
    runtime_after = environment()
    unchanged = before == after
    runtime_unchanged = runtime_before == runtime_after
    passed = unchanged and runtime_unchanged and len(results) == len(checks) and all(c["exit_code"] == 0 for c in results)
    report = {**attempt, 'status': 'complete' if passed else 'failed', "identity": before,
              "identity_after": after, "identity_unchanged": unchanged,
              "environment": runtime_before, "environment_after": runtime_after,
              "environment_unchanged": runtime_unchanged,
              "recorded_at": datetime.now(timezone.utc).isoformat(),
              "checks": results, "passed": passed,
              "scope": "Portable local selection; excludes native Copilot and database acceptance"}
    write_receipt(root, evidence, report)
    if evidence != authoritative:
        write_receipt(root, authoritative, report)
    if not unchanged:
        print(f"BLOCKED / WHY: candidate inputs changed during verification / FIX: {rerun}", file=sys.stderr)
    if not runtime_unchanged:
        print(f"BLOCKED / WHY: verification runtime changed during checks / FIX: {rerun}", file=sys.stderr)
    print(f"{'PASS' if passed else 'FAIL'}: {len(results)} checks; evidence: {evidence}")
    return 0 if passed else 1


def supported_interpreter():
    """The first Python 3.11+ in the pre-push wrapper's order, excluding this (older) interpreter."""
    current = os.path.realpath(sys.executable)
    for name in ('python3.14', 'python3.13', 'python3.12', 'python3.11', 'python3'):
        found = shutil.which(name)
        if found is None or os.path.realpath(found) == current:
            continue
        try:
            probe = subprocess.run([found, '-c', 'import sys; sys.exit(sys.version_info < (3, 11))'],
                                   capture_output=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if probe.returncode == 0:
            return found
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--checks", type=Path, help="custom JSON check array (not a full-gate attestation)")
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    evidence = args.evidence or root / ".rpi/local/copilot/verification.json"
    try:
        if sys.version_info < (3, 11):
            script = [str(Path(__file__).resolve()), '--root', str(root)]
            found = supported_interpreter()
            rerun = (shlex.join([found, *script]) if found else
                     shlex.join(['uv', 'run', '--no-project', '--python', '3.13', 'python', *script]))
            print(f"BLOCKED / WHY: verification requires Python 3.11 or newer; this is {sys.executable} "
                  f"(Python {'.'.join(map(str, sys.version_info[:3]))}) / FIX: {rerun}", file=sys.stderr)
            return 1
        checks = json.loads(args.checks.read_text()) if args.checks else required_checks(root)
        return run(root, checks, evidence, "custom" if args.checks else "ci-equivalent")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        rerun = shlex.join([sys.executable, str(Path(__file__).resolve()), '--root', str(root)])
        print(f"BLOCKED / WHY: {error} / FIX: review the local check inventory and Git candidate, then run {rerun}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
