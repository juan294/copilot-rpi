#!/usr/bin/env python3
"""Copilot project lifecycle. Adapted from cc-rpi aa3ea57 rpi-lifecycle.py.

Source patch: replace Claude/Codex render selection with a receipt-verified Copilot
package, isolate ownership under .rpi/copilot, and keep journals under
.rpi/local/copilot. Standalone runtime uses only Python standard library.
"""

import argparse
import base64
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import uuid

class Conflict(ValueError):
    """A valid request needs reconciliation before it can mutate files."""
    fix = None


class MergeConflict(Conflict):
    """Both the owner and the template changed the same lines of an owned file."""


def encoded(data):
    return base64.b64encode(data).decode('ascii')


def decoded(data):
    return base64.b64decode(data, validate=True)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def serialized(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()


def bound_path(root, relative):
    """Lexical containment and no symlink parents, including bound roots."""
    root = Path(root).absolute()
    name = Path(relative)
    if not isinstance(relative, str) or not relative or name.is_absolute() or name.as_posix() != relative or '..' in name.parts:
        raise ValueError('noncanonical destination: ' + str(relative))
    path = root / name
    parents = [root, *root.parents]
    parent = path.parent
    while parent != root:
        parents.append(parent)
        parent = parent.parent
    for parent in parents:
        if parent.is_symlink():
            raise Conflict('symlink parent: ' + str(parent))
        if parent.exists() and not parent.is_dir():
            raise Conflict('non-directory parent: ' + str(parent))
    return path


def snapshot(path):
    if path.is_symlink():
        return {'kind': 'symlink', 'target': os.readlink(path)}
    if not path.exists():
        return {'kind': 'missing'}
    if not path.is_file():
        raise Conflict('not a regular file: ' + str(path))
    data = path.read_bytes()
    return {'kind': 'file', 'data': encoded(data), 'sha256': digest(data), 'mode': stat.S_IMODE(path.stat().st_mode)}


def file_node(data, mode=0o644):
    return {'kind': 'file', 'data': encoded(data), 'sha256': digest(data), 'mode': mode}


def node_bytes(node):
    return decoded(node['data']) if node['kind'] == 'file' else None


def merge_bytes(local, base, upstream):
    if any(b'\0' in data for data in (local, base, upstream)):
        raise Conflict('both local and upstream changed binary content')
    with tempfile.TemporaryDirectory(prefix='rpi-merge-') as directory:
        paths = [Path(directory) / name for name in ('local', 'base', 'upstream')]
        for path, content in zip(paths, (local, base, upstream)):
            path.write_bytes(content)
        result = subprocess.run(['git', 'merge-file', '-p', *map(str, paths)], capture_output=True)
    if result.returncode != 0:
        raise MergeConflict('both local and upstream changed overlapping content')
    return result.stdout


def reconciliation_conflict(destination, reason, base, local, upstream):
    record = {'destination': destination, 'reason': reason}
    if local is None or upstream is None:
        return record
    record['hashes'] = {name: digest(data) if data is not None else None
                        for name, data in (('base', base), ('local', local), ('upstream', upstream))}
    if any(data is not None and b'\0' in data for data in (base, local, upstream)):
        record['diffs'] = {'binary': 'Binary content differs; review the hashed preimages in this local plan.'}
        return record
    def difference(before, after, first, second):
        return ''.join(difflib.unified_diff(before.decode('utf-8', errors='replace').splitlines(keepends=True),
                                           after.decode('utf-8', errors='replace').splitlines(keepends=True),
                                           fromfile=first, tofile=second))
    record['diffs'] = ({'local_to_upstream': difference(local, upstream, 'local', 'upstream')}
                       if base is None else
                       {'base_to_local': difference(base, local, 'base', 'local'),
                        'base_to_upstream': difference(base, upstream, 'base', 'upstream')})
    return record


def atomic_node(path, node):
    if node['kind'] == 'missing':
        if path.exists() or path.is_symlink():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.rpi-write-', dir=path.parent)
    try:
        if node['kind'] == 'file':
            data = decoded(node['data'])
            if digest(data) != node['sha256']:
                raise ValueError('node payload hash mismatch')
            with os.fdopen(descriptor, 'wb') as stream:
                descriptor = None
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, node['mode'])
        elif node['kind'] == 'symlink':
            os.close(descriptor)
            descriptor = None
            os.unlink(temporary)
            os.symlink(node['target'], temporary)
        else:
            raise ValueError('unsupported transaction node kind')
        os.replace(temporary, path)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if os.path.lexists(temporary):
            os.unlink(temporary)


RECEIPT = '.rpi/copilot-render.json'
STATE = '.rpi/copilot'
LOCAL = '.rpi/local/copilot'
VSCODE_SETTING_RECORD = {'id': 'vscode.agents-md', 'pointer': ['chat.useAgentsMdFile'],
                         'mode': 'value', 'value': True}


def engine_command(*parts):
    return shlex.join([sys.executable, str(Path(__file__).resolve()), *map(str, parts)])


def configuration_engine():
    path = Path(__file__).with_name('rpi-config.py')
    spec = importlib.util.spec_from_file_location('rpi_copilot_config', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_relative(value):
    if not isinstance(value, str) or not value or Path(value).is_absolute() or Path(value).as_posix() != value or '..' in Path(value).parts:
        raise ValueError('noncanonical destination: ' + str(value))
    if value.startswith(('.rpi/copilot/', '.rpi/local/copilot/')) or value in (STATE, LOCAL):
        raise ValueError('package cannot own Copilot state: ' + value)
    return value


def permitted_product_path(component, relative):
    """Receipt hashes prove bytes, while this policy limits what a package may activate."""
    if not isinstance(component, str) or ':' not in component:
        return False
    kind, name = component.split(':', 1)
    if not re.fullmatch('[a-z0-9-]+', name):
        return False
    if kind == 'skill':
        return relative.startswith('.github/skills/' + name + '/')
    if kind == 'prompt':
        return relative == '.github/prompts/' + name + '.prompt.md' or relative.startswith('.github/prompts/' + name + '/')
    if kind == 'agent':
        return relative == '.github/agents/' + name + '.agent.md'
    if kind == 'instruction':
        return relative == '.github/instructions/' + name + '.instructions.md'
    if kind == 'root':
        return (name == 'agents' and relative == 'AGENTS.md') or (name == 'copilot' and relative == '.github/copilot-instructions.md')
    if kind == 'example':
        return relative in ('.vscode/settings.example.json', '.vscode/mcp.example.json', '.github/mcp.example.json')
    return False


def package_files(package, profile):
    package = Path(package).absolute()
    if package.is_symlink():
        raise Conflict('package root cannot be a symlink')
    package = package.resolve()
    receipt_path = bound_path(package, RECEIPT)
    receipt_node = snapshot(receipt_path)
    if receipt_node['kind'] != 'file':
        raise Conflict('missing package render receipt: ' + str(receipt_path))
    receipt = json.loads(node_bytes(receipt_node))
    if not isinstance(receipt, dict) or receipt.get('schema_version') != 1 or receipt.get('profile') != profile or not isinstance(receipt.get('files'), list):
        raise ValueError('invalid package render receipt or profile')
    files = {}
    for item in receipt['files']:
        if not isinstance(item, dict) or not isinstance(item.get('component'), str) or not re.fullmatch('[0-9a-f]{64}', item.get('sha256', '')):
            raise ValueError('invalid package file record')
        relative = item.get('path')
        if isinstance(relative, str) and relative.startswith('.rpi/copilot/runtime/') and item['component'].startswith('runtime:'):
            if relative != '.rpi/copilot/runtime/' + item['component'].removeprefix('runtime:'):
                raise ValueError('invalid package runtime record')
        else:
            safe_relative(relative)
            if not permitted_product_path(item['component'], relative):
                raise ValueError('undeclared active or capability destination in package: ' + relative)
        if relative in files:
            raise ValueError('duplicate package destination: ' + relative)
        node = snapshot(bound_path(package, relative))
        if node['kind'] != 'file' or node['sha256'] != item['sha256']:
            raise Conflict('package file changed from receipt: ' + relative)
        if not item['component'].startswith('runtime:'):
            files[relative] = {'component_id': item['component'], 'data': node_bytes(node)}
    return receipt, files, receipt_node['sha256']


def state_paths(target):
    target = Path(target).absolute()
    if target.is_symlink() or target == Path('/'):
        raise Conflict('target root must be a project directory, not a symlink or filesystem root')
    target = target.resolve()
    if not target.is_dir():
        raise ValueError('target project directory must already exist: ' + str(target))
    bound_path(target, 'AGENTS.md')
    return target, target / STATE, target / LOCAL


def load_state(state):
    node = snapshot(bound_path(state, 'manifest.json'))
    if node['kind'] == 'missing':
        return None
    if node['kind'] != 'file':
        raise Conflict('Copilot ownership manifest must be a regular file')
    value = json.loads(node_bytes(node))
    if (not isinstance(value, dict) or value.get('schema_version') != 1 or
            value.get('ownership') != 'copilot-rpi' or not isinstance(value.get('entries'), list) or
            not isinstance(value.get('config_entries', []), list)):
        raise ValueError('invalid Copilot ownership manifest')
    seen = set()
    for entry in value['entries']:
        if not isinstance(entry, dict) or not isinstance(entry.get('base_hash'), str):
            raise ValueError('invalid Copilot ownership entry')
        path = safe_relative(entry.get('destination'))
        if (path in seen or not permitted_product_path(entry.get('component_id'), path) or
                not re.fullmatch('[0-9a-f]{64}', entry.get('base_hash', ''))):
            raise ValueError('invalid or duplicate Copilot ownership entry')
        seen.add(path)
    for entry in value.get('config_entries', []):
        if not isinstance(entry, dict) or not isinstance(entry.get('base_hash'), str) or not isinstance(entry.get('record'), dict):
            raise ValueError('invalid Copilot configuration ownership entry')
        if (entry.get('destination') != '.vscode/settings.json' or
                entry['record'] != VSCODE_SETTING_RECORD or
                not re.fullmatch('[0-9a-f]{64}', entry.get('base_hash', ''))):
            raise ValueError('invalid Copilot configuration ownership entry')
    return value


def legacy_candidates(target, paths):
    candidates = set(paths)
    for directory, suffix in (('.github/prompts', '.prompt.md'), ('.github/chatmodes', '.chatmode.md')):
        root = bound_path(target, directory)
        if root.is_symlink():
            raise Conflict('symlinked legacy surface directory: ' + str(root))
        if root.is_dir():
            pending = [root]
            visited = 0
            while pending:
                current = pending.pop()
                with os.scandir(current) as entries:
                    for entry in entries:
                        visited += 1
                        if visited > 10000:
                            raise Conflict('too many legacy surface entries; inspect ' + str(root))
                        if entry.is_symlink() and entry.is_dir():
                            raise Conflict('symlinked nested legacy surface directory: ' + entry.path)
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(Path(entry.path))
                        elif entry.name.endswith(suffix):
                            candidates.add(Path(entry.path).relative_to(target).as_posix())
    return sorted(candidates)


def legacy_command_name(relative, content):
    """Read only the simple command selector needed to detect active collisions."""
    if content and content.startswith(b'---\n'):
        try:
            header = content.split(b'\n---\n', 1)[0].decode('utf-8')
            for line in header.splitlines()[1:]:
                match = re.fullmatch(r'\s*name:\s*["\']?([a-z0-9-]+)["\']?\s*', line)
                if match:
                    return match.group(1)
        except UnicodeDecodeError:
            pass
    return Path(relative).name.removesuffix('.prompt.md')


def historical_bytes(request, relative):
    source, revision = request.get('legacy_source'), request.get('legacy_base')
    if not source or not revision:
        return None
    if not re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', revision):
        raise ValueError('--legacy-base requires a full immutable commit ID')
    source = Path(source).absolute()
    if source.is_symlink():
        raise Conflict('legacy source checkout cannot be a symlink')
    source = source.resolve()
    path = relative
    if relative.startswith('.github/prompts/') and Path(relative).parent.as_posix() != '.github/prompts':
        return None
    if relative.startswith('.github/chatmodes/') and Path(relative).parent.as_posix() != '.github/chatmodes':
        return None
    if relative.startswith('.github/prompts/') and Path(relative).name != 'process-errors.prompt.md':
        path = 'templates/prompts/' + Path(relative).name
    elif relative.startswith('.github/chatmodes/'):
        path = 'templates/github/chatmodes/' + Path(relative).name
    elif relative.startswith('.github/instructions/'):
        path = 'templates/github/instructions/' + Path(relative).name + '.template'
    top = subprocess.run(['git', '-C', str(source), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if top.returncode or Path(top.stdout.strip()).resolve() != source:
        raise ValueError('--legacy-source must name the explicit Git checkout root')
    check = subprocess.run(['git', '-C', str(source), 'cat-file', '-t', revision], capture_output=True, text=True)
    if check.returncode or check.stdout.strip() != 'commit':
        raise ValueError('legacy base is not a commit in the explicit source checkout')
    blob = subprocess.run(['git', '-C', str(source), 'show', revision + ':' + path], capture_output=True)
    return blob.stdout if blob.returncode == 0 else None


def node_for(data, before):
    return {'kind': 'missing'} if data is None else file_node(data, before.get('mode', 0o644))


def make_plan(request):
    package = Path(request['package']).absolute()
    target, state, local_state = state_paths(request['target'])
    profile = request['profile']
    receipt, package_contents, receipt_sha = package_files(package, profile)
    previous = load_state(state)
    if previous and previous.get('profile') != profile and request['action'] != 'detach':
        raise Conflict('existing Copilot profile differs; detach or explicitly migrate before changing profile')
    if previous and previous.get('target') != str(target):
        raise Conflict('installation target differs from recorded path; inspect manifest and re-plan')
    source_hash = digest(serialized(receipt))
    selected = set(request.get('components') or [item['component_id'] for item in package_contents.values()])
    reviewed_adoptions = set(request.get('adopt_exact') or [])
    available = {item['component_id'] for item in package_contents.values()}
    retired_review = set(request.get('retired_components') or [])
    if selected - available and request['action'] != 'detach':
        raise ValueError('unknown package component: ' + ', '.join(sorted(selected - available)))
    if reviewed_adoptions - selected:
        raise ValueError('--adopt-exact names an unselected component')
    old = {item['destination']: item for item in (previous or {}).get('entries', [])}
    unknown_old = {item['component_id'] for item in old.values()} - available - retired_review
    if unknown_old:
        raise Conflict('persisted ownership names components absent from this package: ' + ', '.join(sorted(unknown_old)) +
                       '; inspect the manifest, or explicitly review retirement with --retired-component')
    if retired_review - {item['component_id'] for item in old.values()}:
        raise ValueError('--retired-component names no recorded component')
    desired = {} if request['action'] == 'detach' else {path: item for path, item in package_contents.items() if item['component_id'] in selected}
    observations, operations, actions, conflicts, retained, baselines, new_entries = {}, [], [], [], [], {}, []
    configuration = configuration_engine()
    capability_selection = request.get('capabilities')
    if capability_selection is None:
        capability_selection = (previous or {}).get('capabilities', [])
    if set(capability_selection) - {'vscode-settings'}:
        raise ValueError('unknown native capability selection')
    if set(request.get('allow_capabilities', [])) - {'vscode-settings'}:
        raise ValueError('unknown capability authorization')
    if request.get('allow_capabilities') and 'vscode-settings' not in capability_selection and request['action'] != 'detach':
        raise ValueError('--allow-capabilities vscode-settings requires --capability vscode-settings or a recorded selection')
    if request['action'] == 'detach':
        capability_selection = []
    def observe(area, relative):
        key = (area, relative)
        if key not in observations:
            observations[key] = snapshot(bound_path(state if area == 'state' else target, relative))
        return observations[key]
    for relative in sorted(set(old) | set(desired)):
        prior, proposed = old.get(relative), desired.get(relative)
        before = observe('target', relative)
        local = node_bytes(before)
        upstream = proposed['data'] if proposed else None
        base = None
        try:
            if before['kind'] not in ('file', 'missing'):
                raise Conflict('symlink or non-file destination; preserve owner entry')
            if prior:
                baseline = observe('state', 'baselines/' + prior['base_hash'])
                base = node_bytes(baseline)
                if base is None or digest(base) != prior['base_hash']:
                    raise Conflict('missing or damaged ownership baseline')
            if not prior:
                if local == upstream and proposed['component_id'] in reviewed_adoptions:
                    result = upstream  # Explicit owner-reviewed exact-byte mapping.
                elif local is not None and relative == 'AGENTS.md':
                    retained.append({'destination': relative, 'component_id': proposed['component_id'],
                                     'reason': 'project root instructions retained; no Copilot ownership claimed'})
                    continue
                elif local is not None:
                    raise Conflict('destination exists without proven ownership')
                else:
                    result = upstream
            elif upstream is None:
                if local == base:
                    result = None
                else:
                    result = local
                    retained.append({'destination': relative, 'component_id': prior['component_id'], 'reason': 'modified owned content retained on removal'})
            elif local is None:
                result = upstream
            elif local in (base, upstream):
                result = upstream
            elif upstream == base:
                result = local
                retained.append({'destination': relative, 'component_id': prior['component_id'], 'reason': 'local-only edit retained'})
            else:
                result = merge_bytes(local, base, upstream)
            if proposed:
                base_hash = digest(upstream)
                baselines[base_hash] = upstream
                new_entries.append({'destination': relative, 'component_id': proposed['component_id'], 'base_hash': base_hash, 'status': 'clean' if result == upstream else 'local-only'})
            if result != local:
                action = 'create' if local is None else 'remove' if result is None else 'update'
                actions.append({'destination': relative, 'component_id': (proposed or prior)['component_id'], 'action': action})
                operations.append({'root': 'target', 'destination': relative, 'before': before, 'after': node_for(result, before)})
        except (Conflict, OSError) as exc:
            record = reconciliation_conflict(relative, str(exc), base, local, upstream)
            record['component_id'] = (proposed or prior)['component_id']
            record['fix'] = 'preserve owner bytes, repair the named file or baseline, then re-run ' + engine_command('plan', '--package', package, '--target', target, '--profile', profile, '--output', target / LOCAL / 'plans/reconciled.json')
            conflicts.append(record)
    legacy = []
    legacy_names = set()
    sync_node = observe('target', '.github/copilot-rpi-sync.json')
    legacy_sync = None
    if sync_node['kind'] == 'file':
        try:
            hint = json.loads(node_bytes(sync_node))
            claim = hint.get('lastSyncCommit') if isinstance(hint, dict) else None
            legacy_sync = {'destination': '.github/copilot-rpi-sync.json', 'sha256': sync_node['sha256'],
                           'status': 'untrusted-hint', **({'claimed_revision': claim} if isinstance(claim, str) else {})}
        except (ValueError, TypeError):
            legacy_sync = {'destination': '.github/copilot-rpi-sync.json', 'sha256': sync_node['sha256'],
                           'status': 'malformed-untrusted-hint'}
    elif sync_node['kind'] != 'missing':
        conflicts.append({'destination': '.github/copilot-rpi-sync.json', 'reason': 'legacy sync hint is a symlink or non-file'})
    for relative in legacy_candidates(target, request.get('legacy_paths', [])):
        try:
            before = observe('target', relative)
            if before['kind'] == 'missing':
                continue
            content = node_bytes(before)
            historical = historical_bytes(request, relative)
            proven = historical is not None and content == historical
            legacy.append({'destination': relative, 'status': 'exact-historical' if proven else 'retained-unproven', 'reason': 'exact immutable source bytes' if proven else 'sync metadata or filename is not ownership proof'})
            if proven and request['action'] != 'detach':
                operations.append({'root': 'target', 'destination': relative, 'before': before, 'after': {'kind': 'missing'}})
                actions.append({'destination': relative, 'component_id': 'legacy:' + Path(relative).name, 'action': 'remove'})
            elif relative.endswith('.prompt.md'):
                legacy_names.add(legacy_command_name(relative, content))
        except (Conflict, OSError) as exc:
            conflicts.append({'destination': relative, 'reason': str(exc)})
    for relative, item in desired.items():
        if relative.endswith('/SKILL.md') and Path(relative).parent.name in legacy_names:
            conflicts.append({'destination': relative, 'component_id': item['component_id'], 'reason': 'active legacy prompt has the same command name; prove exact historical bytes or retire it by owner review'})
    config_records = []
    prior_config = (previous or {}).get('config_entries', [])
    for entry in prior_config:
        before = observe('state', 'baselines/' + entry['base_hash'])
        raw = node_bytes(before)
        if raw is None or digest(raw) != entry['base_hash'] or raw != serialized(entry['record']):
            conflicts.append({'destination': entry['destination'], 'reason': 'missing or damaged configuration baseline'})
    if not any(item['destination'] == '.vscode/settings.json' for item in conflicts):
        settings_path = '.vscode/settings.json'
        settings_before = observe('target', settings_path)
        if settings_before['kind'] not in ('file', 'missing'):
            conflicts.append({'destination': settings_path, 'reason': 'native settings is a symlink or non-file'})
        else:
            desired_config = [VSCODE_SETTING_RECORD] if 'vscode-settings' in capability_selection else []
            old_config = [item['record'] for item in prior_config]
            if desired_config or old_config:
                try:
                    reconciled = configuration.reconcile(node_bytes(settings_before), old_config, desired_config,
                        allow_capabilities='vscode-settings' in request.get('allow_capabilities', []),
                        allow_removal=request['action'] == 'detach')
                    for item in reconciled['conflicts']:
                        conflicts.append({'destination': settings_path, 'reason': item['reason'], 'record_id': item['id'],
                                          'fix': 'review .vscode/settings.json and re-plan with --allow-capabilities vscode-settings'})
                    retained.extend({'destination': settings_path, 'reason': item['reason'], 'record_id': item['id'],
                                     **({'in_effect': False} if item.get('in_effect') is False else {})}
                                    for item in reconciled['retained'])
                    if not reconciled['conflicts']:
                        after_data = reconciled['content']
                        if after_data != node_bytes(settings_before):
                            operations.append({'root': 'target', 'destination': settings_path, 'before': settings_before,
                                               'after': node_for(after_data, settings_before)})
                            actions.append({'destination': settings_path, 'component_id': 'capability:vscode-settings',
                                            'action': 'remove' if after_data is None else 'create' if settings_before['kind'] == 'missing' else 'update'})
                        for item in reconciled['entries']:
                            raw = serialized(item)
                            baselines[digest(raw)] = raw
                            config_records.append({'destination': settings_path, 'record': item, 'base_hash': digest(raw)})
                except (ValueError, OSError) as exc:
                    conflicts.append({'destination': settings_path, 'reason': str(exc),
                                      'fix': 'repair .vscode/settings.json and rerun plan'})
    if request['action'] == 'detach':
        legacy = []
    for name, data in sorted(baselines.items()):
        before = observe('state', 'baselines/' + name)
        if before['kind'] == 'missing':
            operations.append({'root': 'state', 'destination': 'baselines/' + name, 'before': before, 'after': file_node(data)})
        elif node_bytes(before) != data:
            conflicts.append({'destination': 'baselines/' + name, 'reason': 'damaged content-addressed baseline'})
    next_manifest = None if request['action'] == 'detach' else {
        'schema_version': 1, 'ownership': 'copilot-rpi', 'profile': profile, 'target': str(target),
        'source_sha256': source_hash, 'source_version': receipt['source_version'],
        'components': sorted(selected), 'entries': sorted(new_entries, key=lambda x: x['destination']),
        'capabilities': sorted(capability_selection), 'config_entries': config_records}
    manifest_before = observe('state', 'manifest.json')
    manifest_after = node_for(serialized(next_manifest) if next_manifest else None, manifest_before)
    if manifest_before != manifest_after:
        operations.append({'root': 'state', 'destination': 'manifest.json', 'before': manifest_before, 'after': manifest_after})
    if len(operations) == 1 and operations[0]['root'] == 'state' and operations[0]['destination'] == 'manifest.json':
        before_manifest = json.loads(node_bytes(manifest_before) or b'null')
        after_manifest = json.loads(node_bytes(manifest_after) or b'null')
        if isinstance(before_manifest, dict) and isinstance(after_manifest, dict):
            for document in (before_manifest, after_manifest):
                for entry in document.get('entries', []):
                    entry.pop('status', None)
            if before_manifest == after_manifest:
                operations.clear()  # A local-only label is not an actionable update.
    target_stat = target.stat() if target.exists() else None
    target_identity = {'path': str(target), 'device': target_stat.st_dev if target_stat else None, 'inode': target_stat.st_ino if target_stat else None}
    return {'schema_version': 1, 'request': request, 'source_sha256': source_hash, 'package_receipt_sha256': receipt_sha,
            'target_identity': target_identity, 'profile': profile, 'components': sorted(selected),
            'status': 'conflict' if conflicts else 'ready' if operations else 'noop',
            'actions': actions, 'operations': operations, 'conflicts': conflicts, 'retained': retained, 'legacy': legacy,
            'legacy_sync': legacy_sync,
            'capability_changes': sorted(set(capability_selection) ^ set((previous or {}).get('capabilities', []))),
            'observations': [{'root': area, 'destination': name, 'node': node} for (area, name), node in sorted(observations.items())]}


def operation_path(plan, operation):
    target, state, _ = state_paths(plan['request']['target'])
    if operation['root'] == 'state':
        relative = operation['destination']
        if relative != 'manifest.json' and not re.fullmatch('baselines/[0-9a-f]{64}', relative):
            raise ValueError('invalid Copilot state operation')
        return bound_path(state, relative)
    if operation['root'] != 'target':
        raise ValueError('unbound transaction root')
    relative = safe_relative(operation['destination'])
    native = relative in ('AGENTS.md', '.github/copilot-instructions.md', '.vscode/settings.json') or any(
        relative.startswith(prefix) for prefix in ('.github/skills/', '.github/prompts/', '.github/chatmodes/',
                                                    '.github/agents/', '.github/instructions/')) or relative in (
        '.github/mcp.example.json', '.vscode/mcp.example.json', '.vscode/settings.example.json')
    if not native:
        raise ValueError('transaction cannot mutate an undeclared project surface: ' + relative)
    return bound_path(target, relative)


def observation_path(plan, observation):
    target, state, _ = state_paths(plan['request']['target'])
    if observation['root'] == 'target':
        return bound_path(target, safe_relative(observation['destination']))
    if observation['root'] == 'state':
        return bound_path(state, observation['destination'])
    raise ValueError('unbound observation root')


def validate_plan(plan):
    if not isinstance(plan, dict) or plan.get('schema_version') != 1 or not isinstance(plan.get('request'), dict):
        raise ValueError('invalid plan schema')
    fresh = make_plan(plan['request'])
    if fresh != plan:
        raise Conflict('plan or source/target inputs changed; create a new plan')
    if plan['status'] == 'conflict':
        raise Conflict('unresolved plan conflicts; repair and create a new plan')
    for operation in plan['operations']:
        operation_path(plan, operation)


def atomic_json(path, value):
    atomic_node(path, file_node(serialized(value), 0o600))


def lock_path(target):
    return bound_path(target, LOCAL + '/lock')


def acquire_project_lock(target):
    # Adapted from upstream acquire_lock: no-follow persistent inode and flock.
    import fcntl
    path = lock_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not hasattr(os, 'O_NOFOLLOW'):
        raise ValueError('POSIX O_NOFOLLOW is required for lifecycle mutation')
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        node = os.fstat(fd)
        if not stat.S_ISREG(node.st_mode) or node.st_nlink != 1 or node.st_size:
            raise Conflict('unsafe lifecycle lock')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current = os.stat(path, follow_symlinks=False)
        if (node.st_dev, node.st_ino) != (current.st_dev, current.st_ino):
            raise Conflict('lifecycle lock changed during acquisition')
        return fd
    except BaseException:
        os.close(fd)
        raise


def transaction_paths(target):
    root = bound_path(target, LOCAL + '/transactions')
    if not root.is_dir():
        return []
    paths = []
    with os.scandir(root) as entries:
        for entry in entries:
            if entry.is_symlink():
                raise Conflict('symlinked transaction directory: ' + entry.path)
            if entry.is_dir(follow_symlinks=False):
                journal = Path(entry.path) / 'journal.json'
                if journal.exists() or journal.is_symlink():
                    paths.append(journal)
    paths.sort()
    for path in paths:
        bound_path(target, path.relative_to(target).as_posix())
    return paths


def interrupted(target):
    for path in transaction_paths(target):
        if path.is_symlink():
            raise Conflict('symlink transaction journal: ' + str(path))
        value = json.loads(path.read_bytes())
        if value.get('status') == 'applying':
            raise Conflict('interrupted transaction; ' + engine_command('rollback', '--journal', path))


def apply_plan(plan, fail_after=None):
    validate_plan(plan)
    if plan['status'] == 'noop':
        return {'status': 'noop'}
    target, state, local = state_paths(plan['request']['target'])
    interrupted(target)
    lock = acquire_project_lock(target)
    try:
        validate_plan(plan)
        interrupted(target)
        transaction = uuid.uuid4().hex
        path = bound_path(target, LOCAL + '/transactions/' + transaction + '/journal.json')
        sequence = 1 + max((json.loads(item.read_bytes()).get('sequence', 0) for item in transaction_paths(target)), default=0)
        journal = {'schema_version': 1, 'transaction': transaction, 'status': 'applying', 'target': str(target),
                   'operations': plan['operations'], 'completed': 0, 'pending': None, 'sequence': sequence}
        receipt = {'target': str(target), 'transaction': transaction, 'sequence': sequence,
                   'operations_sha256': digest(serialized(plan['operations']))}
        atomic_json(path.with_name('receipt.json'), receipt)
        atomic_json(path, journal)
        try:
            written = {}
            for index, operation in enumerate(plan['operations']):
                if operation['root'] == 'state' and operation['destination'] == 'manifest.json':
                    for observation in plan['observations']:
                        key = (observation['root'], observation['destination'])
                        expected = written.get(key, observation['node'])
                        if snapshot(observation_path(plan, observation)) != expected:
                            raise Conflict('input changed before manifest commit: ' + observation['destination'])
                destination = operation_path(plan, operation)
                if snapshot(destination) != operation['before']:
                    raise Conflict('preimage changed during transaction: ' + operation['destination'])
                journal['pending'] = index
                atomic_json(path, journal)
                atomic_node(destination, operation['after'])
                written[(operation['root'], operation['destination'])] = operation['after']
                journal['completed'] += 1
                journal['pending'] = None
                atomic_json(path, journal)
                if fail_after == journal['completed']:
                    raise Conflict('simulated interruption')
        except (Conflict, OSError, ValueError) as exc:
            exc.fix = engine_command('rollback', '--journal', path) + '; then create a new plan'
            raise
        journal['status'] = 'complete'
        atomic_json(path, journal)
        return {'status': 'applied', 'journal': str(path), 'actions': plan['actions']}
    finally:
        os.close(lock)


def rollback(path):
    path = Path(path).absolute()
    if path.is_symlink():
        raise Conflict('journal cannot be a symlink')
    path = path.resolve()
    node = snapshot(path)
    if node['kind'] != 'file':
        raise ValueError('journal is not a regular file')
    journal = json.loads(node_bytes(node))
    if not isinstance(journal, dict) or journal.get('schema_version') != 1 or not re.fullmatch('[0-9a-f]{32}', journal.get('transaction', '')):
        raise ValueError('invalid transaction journal')
    target, state, local = state_paths(journal['target'])
    expected = bound_path(target, LOCAL + '/transactions/' + journal['transaction'] + '/journal.json')
    if expected != path:
        raise ValueError('journal does not match its Copilot project namespace')
    receipt_path = bound_path(target, LOCAL + '/transactions/' + journal['transaction'] + '/receipt.json')
    receipt_node = snapshot(receipt_path)
    if receipt_node['kind'] != 'file':
        raise Conflict('missing regular transaction recovery receipt')
    receipt = json.loads(node_bytes(receipt_node))
    if receipt != {'target': str(target), 'transaction': journal['transaction'], 'sequence': journal['sequence'],
                   'operations_sha256': digest(serialized(journal['operations']))}:
        raise Conflict('transaction journal differs from immutable recovery receipt')
    if journal['status'] == 'rolled-back':
        return {'status': 'noop'}
    if journal['status'] not in ('applying', 'complete') or type(journal['completed']) is not int or not 0 <= journal['completed'] <= len(journal['operations']):
        raise ValueError('invalid transaction progress')
    plan_stub = {'request': {'target': str(target)}}
    for operation in journal['operations']:
        operation_path(plan_stub, operation)
    lock = acquire_project_lock(target)
    try:
        if snapshot(path) != node:
            raise Conflict('journal changed before rollback lock')
        if snapshot(receipt_path) != receipt_node:
            raise Conflict('recovery receipt changed before rollback lock')
        for other in transaction_paths(target):
            if other == path:
                continue
            value = json.loads(other.read_bytes())
            if value.get('sequence', 0) > journal['sequence'] and value.get('status') in ('applying', 'complete'):
                raise Conflict('newer transaction exists; ' + engine_command('rollback', '--journal', other) + ' first')
        completed = journal['operations'][:journal['completed']]
        pending = journal.get('pending')
        if pending is not None:
            if pending != journal['completed'] or pending >= len(journal['operations']):
                raise ValueError('invalid pending operation')
            candidate = journal['operations'][pending]
            actual = snapshot(operation_path(plan_stub, candidate))
            if actual == candidate['after']:
                completed.append(candidate)
            elif actual != candidate['before']:
                raise Conflict('interrupted operation has newer owner bytes')
        for operation in completed:
            actual = snapshot(operation_path(plan_stub, operation))
            if actual not in (operation['before'], operation['after']):
                raise Conflict('postimage changed; rollback would overwrite newer work: ' + operation['destination'])
        for operation in reversed(completed):
            destination = operation_path(plan_stub, operation)
            if snapshot(destination) == operation['after']:
                atomic_node(destination, operation['before'])
        journal['status'] = 'rolled-back'
        journal['pending'] = None
        atomic_json(path, journal)
        return {'status': 'rolled-back'}
    finally:
        os.close(lock)


def check(request):
    plan = make_plan({**request, 'action': 'update'})
    result = {key: value for key, value in plan.items() if key not in ('request', 'observations', 'operations')}
    inactive = any(item.get('in_effect') is False for item in plan['retained'])
    result['status'] = 'healthy' if plan['status'] == 'noop' and not inactive else 'action-needed'
    return result


def command(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('plan', 'detach', 'check'):
        sub = commands.add_parser(name)
        sub.add_argument('--package', type=Path, required=True)
        sub.add_argument('--target', type=Path, required=True)
        sub.add_argument('--profile', choices=('cli', 'agent-host', 'vscode-local'), default='cli')
        sub.add_argument('--component', action='append', dest='components')
        sub.add_argument('--adopt-exact', action='append', default=[])
        sub.add_argument('--retired-component', action='append', dest='retired_components', default=[])
        sub.add_argument('--allow-capabilities', action='append', default=[])
        sub.add_argument('--capability', action='append', dest='capabilities')
        sub.add_argument('--legacy-source', type=Path)
        sub.add_argument('--legacy-base')
        if name != 'check':
            sub.add_argument('--output', type=Path, required=True)
        if name == 'plan':
            sub.add_argument('--action', choices=('install', 'update'), default='update')
    apply_parser = commands.add_parser('apply')
    apply_parser.add_argument('--plan', type=Path, required=True)
    apply_parser.add_argument('--fail-after', type=int, help=argparse.SUPPRESS)
    rollback_parser = commands.add_parser('rollback')
    rollback_parser.add_argument('--journal', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'apply':
            result = apply_plan(json.loads(args.plan.read_bytes()), args.fail_after)
        elif args.command == 'rollback':
            result = rollback(args.journal)
        else:
            request = {'package': str(args.package.absolute()), 'target': str(args.target.absolute()),
                       'profile': args.profile, 'components': args.components, 'allow_capabilities': args.allow_capabilities,
                       'adopt_exact': args.adopt_exact,
                       'retired_components': args.retired_components,
                       'capabilities': args.capabilities,
                       'legacy_source': str(args.legacy_source.absolute()) if args.legacy_source else None,
                       'legacy_base': args.legacy_base, 'action': 'detach' if args.command == 'detach' else getattr(args, 'action', 'update')}
            if bool(request['legacy_source']) != bool(request['legacy_base']):
                raise ValueError('--legacy-source and --legacy-base must be supplied together')
            target, _, _ = state_paths(request['target'])
            interrupted(target)
            result = check(request) if args.command == 'check' else make_plan(request)
            if args.command != 'check':
                output = args.output.parent.absolute().resolve() / args.output.name
                if output.exists() or output.is_symlink():
                    raise Conflict('plan output exists; choose a new --output path')
                bound_path(output.parent, output.name)
                atomic_node(output, file_node(serialized(result), 0o600))
        visible = {key: value for key, value in result.items() if key not in ('request', 'observations', 'operations')}
        if result.get('status') in ('conflict', 'action-needed'):
            replacement = Path(request['target']) / LOCAL / 'plans/reconciled.json'
            visible['fix'] = 'BLOCKED / WHY: review conflicts / FIX: repair the named bytes and rerun ' + engine_command('plan', '--package', request['package'], '--target', request['target'], '--profile', request['profile'], '--output', replacement)
        print(json.dumps(visible, sort_keys=True))
        return 2 if result.get('status') in ('conflict', 'action-needed') else 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        fix = getattr(exc, 'fix', None)
        if fix is None and args.command in ('plan', 'detach', 'check'):
            output = getattr(args, 'output', None) or Path(args.target) / LOCAL / 'plans/reconciled.json'
            if output.exists():
                output = output.with_name(output.stem + '-retry.json')
            fix = 'repair the named input, then rerun ' + engine_command('plan', '--package', args.package, '--target', args.target, '--profile', args.profile, '--output', output)
        fix = fix or 'inspect the named journal or plan and rerun with a fresh review artifact'
        print('BLOCKED / WHY: ' + str(exc) + ' / FIX: ' + fix, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(command())
