#!/usr/bin/env python3
"""Read-only, offline validation of the pinned cc-rpi intake."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


STATUSES = {"adopted", "adapted", "deferred", "inapplicable"}
PIN = "aa3ea57fb26ae2e1e167acada4b769e073a417f4"
PINNED_INVENTORY_SHA = "e07f9cfdb6d8400e5bc337562cddc71d40f29f5b2c01e029467cc3d26fb5cfec"
PINNED_ANCHORS = {
    "templates/distribution.json": "6ab6b24255380c7105412ddd101a1c455343b4154b7de89b3deddea781a026a0",
    "patterns/agent-errors.md": "fc485f9de1dbc706a214601827e3bf1efbf742817f8265baf14c3a4744597eac",
    "patterns/quick-reference.md": "7b1d5b43398f0ace8c1aebc8f0fe9a00fc22e2c1104e52c46dd0c7e382eeadaa",
    "LICENSE": "7784153b6b563cf7749faa3e0c24222367b4b8ffc360bb76d9b677b3baa1589d",
}
RULE_RE = re.compile(r"^(\d+)\. (.+)$", re.MULTILINE)
ERROR_RE = re.compile(r"^## Error #(\d+): (.+)$", re.MULTILINE)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_file(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe path: {relative}")
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink path component: {relative}")
    target = root.joinpath(path)
    if not target.is_file():
        raise ValueError(f"missing or non-file path: {relative}")
    return target


def source_files(root, source):
    path = Path(source)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe source path: {source}")
    target = root / path
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink path component: {source}")
    if target.is_file():
        return [source]
    if target.is_dir():
        files = sorted(p.relative_to(root).as_posix() for p in target.rglob("*") if p.is_file() and not p.is_symlink())
        if files:
            for file in files:
                safe_file(root, file)
            return files
    raise ValueError(f"missing or empty source: {source}")


def schema_errors(value, rule, schema, location=""):
    """Validate the small JSON Schema vocabulary used by this checked-in lock."""
    if "$ref" in rule:
        name = rule["$ref"].removeprefix("#/$defs/")
        return schema_errors(value, schema["$defs"][name], schema, location)
    if "oneOf" in rule:
        matches = [part for part in rule["oneOf"] if not schema_errors(value, part, schema, location)]
        return [] if len(matches) == 1 else [f"schema violation: {location} matches {len(matches)} alternatives"]
    errors = []
    expected = rule.get("type")
    if expected:
        kinds = expected if isinstance(expected, list) else [expected]
        valid = any(
            (kind == "object" and isinstance(value, dict))
            or (kind == "array" and isinstance(value, list))
            or (kind == "string" and isinstance(value, str))
            or (kind == "integer" and isinstance(value, int) and not isinstance(value, bool))
            or (kind == "null" and value is None)
            for kind in kinds
        )
        if not valid:
            return [f"schema violation: {location or 'root'} has wrong type"]
    if "const" in rule and value != rule["const"]:
        errors.append(f"schema violation: {location or 'root'} has wrong constant")
    if "enum" in rule and value not in rule["enum"]:
        errors.append(f"schema violation: {location or 'root'} has invalid value")
    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0):
            errors.append(f"schema violation: {location} is too short")
        if "pattern" in rule and not re.search(rule["pattern"], value):
            errors.append(f"schema violation: {location} has invalid format")
    if isinstance(value, dict):
        for key in rule.get("required", []):
            if key not in value:
                errors.append(f"schema violation: {location + '.' if location else ''}{key} is required")
        properties = rule.get("properties", {})
        if rule.get("additionalProperties") is False:
            for key in value.keys() - properties.keys():
                errors.append(f"schema violation: {location + '.' if location else ''}{key} is unexpected")
        for key in value.keys() & properties.keys():
            child = f"{location}.{key}" if location else key
            errors.extend(schema_errors(value[key], properties[key], schema, child))
    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            errors.append(f"schema violation: {location} has too few items")
        if "items" in rule:
            for index, item in enumerate(value):
                errors.extend(schema_errors(item, rule["items"], schema, f"{location}[{index}]"))
    return errors


def component_hash(root, source):
    files = source_files(root, source)
    if len(files) == 1 and files[0] == source:
        return digest(safe_file(root, source).read_bytes())
    payload = b"".join(
        path.encode() + b"\0" + digest(safe_file(root, path).read_bytes()).encode() + b"\n"
        for path in files
    )
    return digest(payload)


def catalog(root):
    result = {}
    for kind, rel, pattern in (
        ("error", "patterns/agent-errors.md", ERROR_RE),
        ("rule", "patterns/quick-reference.md", RULE_RE),
    ):
        content = safe_file(root, rel).read_text()
        matches = list(pattern.finditer(content))
        for index, match in enumerate(matches):
            key = f"{kind}:{match.group(1)}"
            if key in result:
                raise ValueError(f"duplicate catalog id: {key}")
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            section = content[match.start():end] if kind == "error" else match.group()
            result[key] = {
                "id": key,
                "source": rel,
                "title": match.group(2).strip(),
                "source_sha256": digest(section.encode()),
            }
    return result


def read_json(path):
    return json.loads(path.read_text())


def check(lock_path, inventory_path, source_path=None, content_only=False):
    errors = []
    lock = read_json(lock_path)
    inventory = read_json(inventory_path)
    schema = read_json(lock_path.parent / "cc-rpi.lock.schema.json")
    errors.extend(schema_errors(lock, schema, schema))
    snapshot_root = lock_path.parent / "snapshots"
    product_root = Path(__file__).resolve().parents[1]
    if lock.get("schema_version") != 1 or inventory.get("schema_version") != 1:
        errors.append("unsupported lock or inventory schema")
    if lock.get("upstream", {}).get("commit") != PIN or inventory.get("upstream_commit") != PIN:
        errors.append("upstream pin mismatch")
    if lock.get("upstream", {}).get("version") != "2.1.0":
        errors.append("upstream version mismatch")
    if digest(inventory_path.read_bytes()) != PINNED_INVENTORY_SHA:
        errors.append("pinned inventory hash mismatch")

    recorded_files = inventory.get("files", [])
    file_paths = [item.get("path") for item in recorded_files]
    recorded_links = inventory.get("links", [])
    links = {item["path"]: item for item in recorded_links}
    if len(links) != len(recorded_links):
        errors.append("duplicate inventory link path")
    if len(file_paths) != len(set(file_paths)):
        errors.append("duplicate inventory path")
    actual_paths = {
        path.relative_to(snapshot_root).as_posix()
        for path in snapshot_root.rglob("*") if path.is_file()
    }
    for path in sorted(actual_paths - set(file_paths)):
        errors.append(f"unlisted snapshot file: {path}")
    for path in sorted(set(file_paths) - actual_paths):
        errors.append(f"missing snapshot file: {path}")
    for item in recorded_files:
        try:
            actual = digest(safe_file(snapshot_root, item["path"]).read_bytes())
            if actual != item["sha256"]:
                errors.append(f"snapshot hash mismatch: {item['path']}")
        except (KeyError, ValueError) as exc:
            errors.append(str(exc))
    for path, expected_sha in PINNED_ANCHORS.items():
        try:
            if digest(safe_file(snapshot_root, path).read_bytes()) != expected_sha:
                errors.append(f"pinned source anchor mismatch: {path}")
        except ValueError as exc:
            errors.append(str(exc))

    try:
        manifest = read_json(safe_file(snapshot_root, "templates/distribution.json"))
    except (ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid snapshot manifest: {exc}")
        manifest = {"components": []}
    if manifest.get("version") != lock.get("upstream", {}).get("version"):
        errors.append("snapshot manifest version mismatch")
    expected = {c["id"]: c for c in manifest.get("components", [])}
    if len(expected) != len(manifest.get("components", [])):
        errors.append("duplicate snapshot component id")
    components = lock.get("components", [])
    ids = [c.get("id") for c in components]
    if len(ids) != len(set(ids)):
        errors.append("duplicate component id")
    if set(ids) != set(expected):
        for identifier in sorted(set(expected) - set(ids)):
            errors.append(f"missing component disposition: {identifier}")
        for identifier in sorted(set(ids) - set(expected)):
            errors.append(f"unknown lock component: {identifier}")
    all_source_files = {"templates/distribution.json", "patterns/agent-errors.md", "patterns/quick-reference.md", "LICENSE"}
    all_source_files.update(item["resolved"] for item in recorded_links)
    for item in components:
        identifier = item.get("id")
        if item.get("disposition") not in STATUSES:
            errors.append(f"invalid disposition: {identifier}")
        if not item.get("rationale"):
            errors.append(f"missing rationale: {identifier}")
        if identifier not in expected:
            continue
        upstream = expected[identifier]
        if item.get("kind") != upstream.get("kind"):
            errors.append(f"component kind mismatch: {identifier}")
        if item.get("source") != upstream.get("source"):
            errors.append(f"component source mismatch: {identifier}")
        try:
            files = source_files(snapshot_root, upstream["source"])
            all_source_files.update(files)
            for resource in upstream.get("resources", []):
                resource_path = resource["source"] if isinstance(resource, dict) else str(Path(upstream["source"]) / resource)
                all_source_files.add(links[resource_path]["resolved"] if resource_path in links else resource_path)
            actual = component_hash(snapshot_root, upstream["source"])
            if actual != item.get("source_sha256"):
                errors.append(f"component source hash mismatch: {identifier}")
        except (KeyError, ValueError) as exc:
            errors.append(f"{identifier}: {exc}")
        destination = item.get("destination")
        if item.get("disposition") in {"adopted", "adapted"}:
            if not destination or not item.get("destination_sha256"):
                errors.append(f"missing destination hash: {identifier}")
            else:
                try:
                    actual = component_hash(product_root, destination)
                    if actual != item["destination_sha256"]:
                        errors.append(f"destination hash mismatch: {identifier}")
                except ValueError as exc:
                    errors.append(f"{identifier}: {exc}")
            if item.get("disposition") == "adapted" and not item.get("adaptation_note"):
                errors.append(f"missing adaptation note: {identifier}")
        elif destination is not None or item.get("destination_sha256") is not None:
            errors.append(f"excluded component has destination: {identifier}")
        if item.get("disposition") != "adapted" and item.get("adaptation_note") is not None:
            errors.append(f"unexpected adaptation note: {identifier}")
    if set(file_paths) != all_source_files:
        for path in sorted(all_source_files - set(file_paths)):
            errors.append(f"missing snapshot inventory: {path}")
        for path in sorted(set(file_paths) - all_source_files):
            errors.append(f"unclaimed snapshot inventory: {path}")

    try:
        expected_catalog = catalog(snapshot_root)
    except ValueError as exc:
        errors.append(str(exc))
        expected_catalog = {}
    entries = lock.get("catalog", [])
    crosswalk = lock.get("crosswalk", {})
    crosswalk_entries = {}
    try:
        crosswalk_path = crosswalk["path"]
        crosswalk_file = safe_file(product_root, crosswalk_path)
        if digest(crosswalk_file.read_bytes()) != crosswalk.get("sha256"):
            errors.append("crosswalk hash mismatch")
        crosswalk_data = read_json(crosswalk_file)
        if crosswalk_data.get("source", {}).get("commit") != PIN:
            errors.append("crosswalk source pin mismatch")
        for kind, key in (("error", "upstream_errors"), ("rule", "upstream_rules")):
            for record in crosswalk_data[key]:
                identifier = f"{kind}:{record['id']}"
                if identifier in crosswalk_entries:
                    errors.append(f"duplicate crosswalk id: {identifier}")
                crosswalk_entries[identifier] = record
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid crosswalk: {exc}")
    if set(crosswalk_entries) != set(expected_catalog):
        errors.append("crosswalk upstream catalog coverage mismatch")
    entry_ids = [entry.get("id") for entry in entries]
    if len(entry_ids) != len(set(entry_ids)):
        errors.append("duplicate catalog id")
    if set(entry_ids) != set(expected_catalog):
        for identifier in sorted(set(expected_catalog) - set(entry_ids)):
            errors.append(f"missing catalog disposition: {identifier}")
        for identifier in sorted(set(entry_ids) - set(expected_catalog)):
            errors.append(f"unknown lock catalog entry: {identifier}")
    for entry in entries:
        identifier = entry.get("id")
        if entry.get("disposition") not in STATUSES:
            errors.append(f"invalid disposition: {identifier}")
        if not entry.get("rationale"):
            errors.append(f"missing rationale: {identifier}")
        if identifier in expected_catalog:
            for key in ("source", "title", "source_sha256"):
                if entry.get(key) != expected_catalog[identifier][key]:
                    errors.append(f"catalog {key} mismatch: {identifier}")
        if identifier in crosswalk_entries:
            for key in ("copilot_ids", "disposition", "rationale"):
                if entry.get(key) != crosswalk_entries[identifier].get(key):
                    errors.append(f"crosswalk {key} mismatch: {identifier}")
        if entry.get("disposition") in {"adopted", "adapted"}:
            if not entry.get("destination") or not entry.get("destination_sha256"):
                errors.append(f"missing destination hash: {identifier}")
            else:
                try:
                    actual = digest(safe_file(product_root, entry["destination"]).read_bytes())
                    if actual != entry["destination_sha256"]:
                        errors.append(f"destination hash mismatch: {identifier}")
                except ValueError as exc:
                    errors.append(f"{identifier}: {exc}")
        elif entry.get("destination") is not None or entry.get("destination_sha256") is not None:
            errors.append(f"excluded catalog entry has destination: {identifier}")

    if source_path is not None:
        source = source_path.resolve()
        git_root = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False
        )
        if not content_only:
            if git_root.returncode != 0 or Path(git_root.stdout.strip()).resolve() != source:
                errors.append("supplied source is not a Git checkout root; use --content-only for an archive fixture")
            else:
                git = subprocess.run(
                    ["git", "-C", str(source), "rev-parse", "HEAD"],
                    capture_output=True, text=True, check=False
                )
                if git.returncode != 0 or git.stdout.strip() != PIN:
                    errors.append(f"supplied upstream commit mismatch: {git.stdout.strip()}")
        try:
            live = read_json(safe_file(source, "templates/distribution.json"))
            if not content_only:
                for link in recorded_links:
                    path = source / link["path"]
                    if not path.is_symlink() or path.readlink().as_posix() != link["target"]:
                        errors.append(f"upstream symlink drift: {link['path']}")
            live_ids = {c["id"] for c in live["components"]}
            for identifier in sorted(live_ids - set(expected)):
                errors.append(f"unknown upstream component: {identifier}")
            for identifier in sorted(set(expected) - live_ids):
                errors.append(f"missing upstream component: {identifier}")
            if live.get("version") != "2.1.0":
                errors.append(f"supplied upstream version drift: {live.get('version')}")
            for item in components:
                try:
                    actual = component_hash(source, item["source"])
                    if actual != item["source_sha256"]:
                        errors.append(f"upstream source hash drift: {item['id']}")
                except ValueError as exc:
                    errors.append(f"{item['id']}: {exc}")
            live_catalog = catalog(source)
            for identifier in sorted(set(live_catalog) - set(expected_catalog)):
                errors.append(f"unknown upstream catalog entry: {identifier}")
            for identifier in sorted(set(expected_catalog) - set(live_catalog)):
                errors.append(f"missing upstream catalog entry: {identifier}")
            for identifier in sorted(set(live_catalog) & set(expected_catalog)):
                if live_catalog[identifier]["source_sha256"] != expected_catalog[identifier]["source_sha256"]:
                    errors.append(f"upstream catalog hash drift: {identifier}")
            for item in recorded_files:
                try:
                    if digest(safe_file(source, item["path"]).read_bytes()) != item["sha256"]:
                        errors.append(f"upstream file hash drift: {item['path']}")
                except ValueError as exc:
                    errors.append(str(exc))
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"invalid supplied source: {exc}")

    if errors:
        for error in sorted(set(errors)):
            print(f"BLOCKED: {error}")
        print("FIX: review the supplied source, update the pinned intake, then rerun check-upstream.py --check")
        return 1
    suffix = "; content-only source comparison, Git identity unverified" if content_only else ""
    print(f"OK: {len(components)} components, {len(entries)} catalog entries; pinned offline intake is consistent{suffix}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=Path("upstream/cc-rpi.lock.json"))
    parser.add_argument("--inventory", type=Path, default=Path("upstream/cc-rpi.inventory.json"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--content-only", action="store_true", help="Compare archive fixture bytes without Git identity proof")
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    if args.content_only and args.source is None:
        parser.error("--content-only requires --source")
    try:
        return check(args.lock.resolve(), args.inventory.resolve(), args.source, args.content_only)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: invalid intake input: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
