#!/usr/bin/env python3
"""Validate and render the Copilot RPI native component manifest.

Path, resource and collision invariants are adapted from cc-rpi source
aa3ea57fb26ae2e1e167acada4b769e073a417f4. Copilot metadata and profiles
are intentionally owned here. Rendering only writes to an explicit target.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] in {"plan", "apply", "check", "rollback", "detach"}:
    # Lifecycle is the adopter runtime. Dispatch before importing maintainer-only
    # PyYAML so a rendered package runs with Python's standard library alone.
    import runpy
    runpy.run_path(str(Path(__file__).with_name("rpi-lifecycle.py")), run_name="__main__")
    raise SystemExit(0)

import yaml


PROFILES = {"cli", "agent-host", "vscode-local"}
KINDS = {"skill", "prompt", "agent", "instruction", "root", "example"}
SKILL_FIELDS = {"name", "description", "argument-hint", "user-invocable", "disable-model-invocation"}
AGENT_FIELDS = {
    "name", "description", "tools", "include-custom-instructions",
    "disable-model-invocation", "user-invocable", "argument-hint", "handoffs", "target",
}
INSTRUCTION_FIELDS = {"applyTo", "description"}
PROMPT_FIELDS = {"name", "description", "argument-hint", "agent", "tools"}
LEGACY_PROMPT_FIELDS = PROMPT_FIELDS | {"mode"}
LEGACY_CHATMODE_FIELDS = {"name", "description", "tools"}
KNOWN_TOOLS = {"read", "search", "edit", "execute", "agent", "web", "todo"}
ACTIVE_ROOTS = (
    ".github/skills", ".github/agents", ".github/instructions", ".github/prompts",
)
OUTPUT_MANIFEST = ".rpi/copilot-render.json"


class DuplicateKeyLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        try:
            hash(key)
        except TypeError as exc:
            raise ValueError("unsupported YAML mapping key: expected a scalar") from exc
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node)
    return result


DuplicateKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative, label="path"):
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"unsafe {label}: {relative}")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != relative:
        raise ValueError(f"unsafe {label}: {relative}")
    current = root
    for part in path.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"symlink {label}: {relative}")
    return root / path


def frontmatter(path, kind):
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n") or "\n---\n" not in content[4:]:
        raise ValueError(f"{path}: malformed YAML frontmatter")
    raw, body = content[4:].split("\n---\n", 1)
    try:
        metadata = yaml.load(raw, Loader=DuplicateKeyLoader)
    except (yaml.YAMLError, ValueError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    if not isinstance(metadata, dict) or not body.strip():
        raise ValueError(f"{path}: malformed YAML frontmatter or empty body")
    if "model" in metadata or "infer" in metadata:
        raise ValueError(f"{path}: model pin or retired infer metadata is prohibited")
    allowed = {
        "skill": SKILL_FIELDS, "agent": AGENT_FIELDS, "instruction": INSTRUCTION_FIELDS,
        "prompt": PROMPT_FIELDS, "legacy-prompt": LEGACY_PROMPT_FIELDS,
        "legacy-chatmode": LEGACY_CHATMODE_FIELDS,
    }[kind]
    unknown = set(metadata) - allowed
    if unknown:
        raise ValueError(f"{path}: unsupported metadata: {', '.join(sorted(unknown))}")
    if kind == "skill":
        name = metadata.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]{1,64}", name) or name != path.parent.name:
            raise ValueError(f"{path}: skill name must match directory and use lowercase letters, digits or hyphens")
        description = metadata.get("description")
        if not isinstance(description, str) or not 0 < len(description) <= 1024:
            raise ValueError(f"{path}: missing or oversized description")
        for field in ("user-invocable", "disable-model-invocation"):
            if field in metadata and not isinstance(metadata[field], bool):
                raise ValueError(f"{path}: {field} must be boolean")
    elif kind == "agent":
        if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
            raise ValueError(f"{path}: missing description")
        if "tools" not in metadata:
            raise ValueError(f"{path}: missing tools; omission grants all tools")
        tools = metadata["tools"]
        if not isinstance(tools, list) or any(not isinstance(tool, str) or tool not in KNOWN_TOOLS for tool in tools):
            raise ValueError(f"{path}: unsupported tool name")
        if len(set(tools)) != len(tools):
            raise ValueError(f"{path}: duplicate tool name")
        for field in ("include-custom-instructions", "disable-model-invocation", "user-invocable"):
            if field in metadata and not isinstance(metadata[field], bool):
                raise ValueError(f"{path}: {field} must be boolean")
        if metadata.get("target") not in (None, "vscode", "github-copilot"):
            raise ValueError(f"{path}: unsupported target")
    elif kind == "instruction":
        if not isinstance(metadata.get("applyTo"), str) or not metadata["applyTo"].strip():
            raise ValueError(f"{path}: missing applyTo")
    elif kind == "prompt" and metadata.get("agent") != "agent":
        raise ValueError(f"{path}: missing current agent metadata")
    elif kind == "legacy-prompt":
        if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
            raise ValueError(f"{path}: missing legacy prompt description")
        if metadata.get("mode") not in ("agent", "ask", "plan") and metadata.get("agent") is None:
            raise ValueError(f"{path}: missing legacy prompt mode or agent")
    elif kind == "legacy-chatmode":
        if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
            raise ValueError(f"{path}: missing legacy chatmode description")
    return metadata, body, content


def load_manifest(root):
    manifest_path = safe_path(root, "templates/distribution.json", "manifest path")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != 1 or not re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")):
        raise ValueError("unsupported manifest schema or version")
    if set(manifest.get("profiles", {})) != PROFILES:
        raise ValueError("manifest must declare cli, agent-host and vscode-local profiles")
    adapter_path = safe_path(root, manifest.get("adapter"), "adapter path")
    adapter = json.loads(adapter_path.read_text())
    expected_modes = {
        "cli": {"skills": True, "prompts": False},
        "agent-host": {"skills": True, "prompts": False},
        "vscode-local": {"skills": False, "prompts": True},
    }
    if adapter.get("schema_version") != 1 or adapter.get("profiles") != expected_modes:
        raise ValueError("adapter profile mismatch")
    if set(adapter.get("tool_aliases", [])) != KNOWN_TOOLS:
        raise ValueError("adapter tool alias mismatch")
    budget = manifest.get("root_budget_bytes")
    if not isinstance(budget, int) or isinstance(budget, bool) or not 0 < budget <= 8192:
        raise ValueError("root budget must be 1..8192 bytes")
    if not isinstance(manifest.get("components"), list) or not manifest["components"]:
        raise ValueError("manifest has no components")
    ids = set()
    for component in manifest["components"]:
        cid = component.get("id")
        if not isinstance(cid, str) or not re.fullmatch(r"[a-z]+:[a-z0-9-]+", cid) or cid in ids:
            raise ValueError(f"duplicate or invalid component ID: {cid}")
        ids.add(cid)
        if component.get("kind") not in KINDS:
            raise ValueError(f"{cid}: unsupported component kind")
        profiles = component.get("profiles")
        if not isinstance(profiles, list) or not profiles or len(set(profiles)) != len(profiles) or set(profiles) - PROFILES:
            raise ValueError(f"{cid}: invalid profile selection")
        mode_key = {"skill": "skills", "prompt": "prompts"}.get(component["kind"])
        if mode_key and any(not adapter["profiles"][profile][mode_key] for profile in profiles):
            raise ValueError(f"{cid}: profile kind mismatch: {profiles}")
        source = safe_path(root, component.get("source"), "source")
        safe_path(Path("/virtual-output"), component.get("destination"), "destination")
        source_name = Path(component["source"]).name
        expected_destination = {
            "skill": f".github/skills/{source_name}",
            "prompt": f".github/prompts/{source_name}.prompt.md",
            "agent": f".github/agents/{source_name}",
            "instruction": f".github/instructions/{source_name.removesuffix('.template')}",
        }.get(component["kind"])
        if expected_destination and component["destination"] != expected_destination:
            raise ValueError(f"{cid}: invalid native destination: {component['destination']}")
        if component["kind"] == "root" and component["destination"] not in (
            "AGENTS.md", ".github/copilot-instructions.md"
        ):
            raise ValueError(f"{cid}: invalid native destination: {component['destination']}")
        if not isinstance(component.get("resources"), list) or not isinstance(component.get("former_paths"), list):
            raise ValueError(f"{cid}: resources and former_paths must be explicit lists")
        for former in component["former_paths"]:
            safe_path(Path("/virtual-output"), former, "former path")
        if component["kind"] != "skill" and component["resources"]:
            raise ValueError(f"{cid}: only skill components have bundled resources")
        if component["kind"] == "example" and not component.get("optional", False):
            raise ValueError(f"{cid}: example must be optional")
        if component["kind"] == "example":
            if not component["destination"].endswith(".example.json"):
                raise ValueError(f"{cid}: example destination must be inert .example.json")
            try:
                data = json.loads(source.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"{cid}: invalid example JSON: {exc}") from exc
            if not isinstance(data, dict):
                raise ValueError(f"{cid}: invalid example JSON root")
            if component["destination"] == ".vscode/mcp.example.json" and not (
                isinstance(data.get("servers"), dict) and isinstance(data.get("inputs"), list)
            ):
                raise ValueError(f"{cid}: invalid VS Code MCP example schema")
            if component["destination"] == ".github/mcp.example.json" and not isinstance(data.get("mcpServers"), dict):
                raise ValueError(f"{cid}: invalid Copilot CLI MCP example schema")
    authored_skills = {path.parent.relative_to(root).as_posix() for path in (root / "templates/skills").glob("*/SKILL.md")}
    declared_skills = {item["source"] for item in manifest["components"] if item["kind"] == "skill"}
    for missing in sorted(authored_skills - declared_skills):
        raise ValueError(f"undeclared authored skill: {missing}")
    for missing in sorted(declared_skills - authored_skills):
        raise ValueError(f"missing authored skill: {missing}")
    for kind, pattern, directory in (
        ("agent", "*.agent.md", "templates/github/agents"),
        ("instruction", "*.instructions.md.template", "templates/github/instructions"),
    ):
        authored = {path.relative_to(root).as_posix() for path in (root / directory).glob(pattern)}
        declared = {item["source"] for item in manifest["components"] if item["kind"] == kind}
        for missing in sorted(authored - declared):
            raise ValueError(f"undeclared authored {kind}: {missing}")
        for missing in sorted(declared - authored):
            raise ValueError(f"missing authored {kind}: {missing}")
    self_app = manifest.get("self_application", {})
    if self_app.get("profile") not in PROFILES:
        raise ValueError("self_application needs a declared profile")
    preserve = self_app.get("preserve", [])
    if not isinstance(preserve, list) or set(preserve) - ids:
        raise ValueError("self_application preserve contains unknown ID")
    for former in self_app.get("legacy_active", []):
        safe_path(Path("/virtual-output"), former, "legacy path")
    return manifest


def skill_files(root, component):
    cid = component["id"]
    directory = safe_path(root, component["source"], "source")
    if not directory.is_dir():
        raise ValueError(f"{cid}: missing skill source directory: {directory}")
    entry = safe_path(directory, "SKILL.md", "skill entrypoint")
    if not entry.is_file():
        raise ValueError(f"{cid}: missing SKILL.md")
    metadata, body, content = frontmatter(entry, "skill")
    if "$ARGUMENTS" in content or "Claude Code" in content.split("\n---\n", 1)[0]:
        raise ValueError(f"{cid}: Claude-only header or $ARGUMENTS syntax")
    declared = set()
    files = {"SKILL.md": entry.read_bytes()}
    for resource in component["resources"]:
        path = safe_path(directory, resource, "resource")
        if not path.is_file() or resource in declared:
            raise ValueError(f"{cid}: missing resource or duplicate: {resource}")
        if resource not in body:
            raise ValueError(f"{cid}: unlinked resource: {resource}")
        declared.add(resource)
        files[resource] = path.read_bytes()
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    for path in actual - declared - {"SKILL.md"}:
        raise ValueError(f"{cid}: undeclared bundled resource: {path}")
    return metadata, files


def generated_files(root, manifest, profile, include_examples=False):
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")
    outputs = {}
    names = set()
    agent_names = set()
    roots = 0
    skills_by_source = {
        item["source"]: item for item in manifest["components"] if item["kind"] == "skill"
    }
    for component in manifest["components"]:
        if profile not in component["profiles"] or component["kind"] == "example" and not include_examples:
            continue
        cid, kind = component["id"], component["kind"]
        source = safe_path(root, component["source"], "source")
        destination = component["destination"]
        if kind in ("skill", "prompt"):
            source_component = skills_by_source.get(component["source"]) if kind == "prompt" else component
            if source_component is None:
                raise ValueError(f"{cid}: prompt lacks a declared canonical skill")
            metadata, files = skill_files(root, source_component)
            name = metadata["name"]
            if name in names:
                raise ValueError(f"{cid}: command name collision: {name}")
            if kind == "skill":
                for relative, data in files.items():
                    output = f"{destination}/{relative}"
                    if output in outputs:
                        raise ValueError(f"{cid}: output collision: {output}")
                    outputs[output] = (data, cid)
            else:
                body = files["SKILL.md"].split(b"\n---\n", 1)[1].decode("utf-8")
                resources = sorted((item for item in files if item != "SKILL.md"), key=len, reverse=True)
                for index, relative in enumerate(resources):
                    body = body.replace(relative, f"__RPI_RESOURCE_{index}__")
                for index, relative in enumerate(resources):
                    body = body.replace(f"__RPI_RESOURCE_{index}__", f"{name}/{relative}")
                for relative, data in files.items():
                    if relative == "SKILL.md":
                        continue
                    resource_output = f".github/prompts/{name}/{relative}"
                    if resource_output in outputs:
                        raise ValueError(f"{cid}: output collision: {resource_output}")
                    outputs[resource_output] = (data, cid)
                text = (
                    f"---\nname: {name}\ndescription: {json.dumps(metadata['description'])}\n"
                    "agent: agent\n---\n\n"
                    "The command invocation does not authorize external publication.\n\n"
                    + body
                )
                if destination in outputs:
                    raise ValueError(f"{cid}: output collision: {destination}")
                outputs[destination] = (text.encode(), cid)
            names.add(name)
        else:
            if not source.is_file():
                raise ValueError(f"{cid}: missing source: {source}")
            if kind in ("agent", "instruction"):
                metadata, _, _ = frontmatter(source, kind)
                if kind == "agent":
                    agent_name = metadata.get("name", source.name.removesuffix(".agent.md"))
                    if not isinstance(agent_name, str) or not agent_name.strip():
                        raise ValueError(f"{cid}: invalid agent name")
                    if agent_name.casefold() in agent_names:
                        raise ValueError(f"{cid}: agent name collision: {agent_name}")
                    agent_names.add(agent_name.casefold())
            data = source.read_bytes()
            if b"$ARGUMENTS" in data:
                raise ValueError(f"{cid}: $ARGUMENTS is unsupported Copilot syntax")
            if destination in outputs:
                raise ValueError(f"{cid}: output collision: {destination}")
            outputs[destination] = (data, cid)
            if kind == "root":
                roots += len(data)
    if roots > manifest["root_budget_bytes"]:
        raise ValueError(f"root budget exceeded: {roots} > {manifest['root_budget_bytes']}")
    return outputs, roots


def validate(root, manifest):
    all_outputs = {}
    for profile in PROFILES:
        outputs, roots = generated_files(root, manifest, profile)
        all_outputs[profile] = outputs
        print(f"profile {profile}: {len(outputs)} files; managed root {roots} bytes")
    active_root = [root / path for path in ("AGENTS.md", ".github/copilot-instructions.md")]
    active_root = [path for path in active_root if path.is_file()]
    scoped = list((root / ".github/instructions").glob("*.instructions.md"))
    print(
        f"observed active root: {sum(path.stat().st_size for path in active_root)} bytes "
        f"across {len(active_root)} files; scoped instructions: "
        f"{sum(path.stat().st_size for path in scoped)} bytes across {len(scoped)} files"
    )
    declared = set(all_outputs[manifest["self_application"]["profile"]])
    legacy = set(manifest["self_application"].get("legacy_active", []))
    active_commands = {}
    active_agent_names = set()
    for directory in ACTIVE_ROOTS:
        for path in (root / directory).rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if relative not in declared and relative not in legacy:
                raise ValueError(f"undeclared active surface: {relative}")
            if relative in legacy:
                print(f"migration pending: declared legacy active surface {relative}")
            kind = None
            if relative.endswith("/SKILL.md"):
                kind = "skill"
            elif relative.endswith(".agent.md"):
                kind = "agent"
            elif relative.endswith(".instructions.md"):
                kind = "instruction"
            elif relative.endswith(".prompt.md"):
                kind = "legacy-prompt" if relative in legacy else "prompt"
            if kind:
                metadata, _, _ = frontmatter(path, kind)
                if kind == "agent":
                    name = metadata.get("name", path.name.removesuffix(".agent.md")).casefold()
                    if name in active_agent_names:
                        raise ValueError(f"active agent name collision: {name}")
                    active_agent_names.add(name)
                if kind in ("skill", "prompt", "legacy-prompt"):
                    name = metadata.get("name", path.name.removesuffix(".prompt.md")).casefold()
                    prior = active_commands.get(name)
                    if prior:
                        raise ValueError(f"active command name collision: {name} ({prior}, {relative})")
                    active_commands[name] = relative
    former_chatmodes = {
        path for item in manifest["components"] for path in item["former_paths"]
        if path.startswith(".github/chatmodes/")
    }
    for path in (root / ".github/chatmodes").glob("*.chatmode.md"):
        relative = path.relative_to(root).as_posix()
        if relative not in former_chatmodes:
            raise ValueError(f"undeclared legacy chatmode: {relative}")
        frontmatter(path, "legacy-chatmode")
        print(f"migration pending: declared legacy chatmode {relative}")
    return all_outputs


def render_record(manifest, profile, outputs, roots, preserve_ids):
    files = []
    preserved = []
    for relative, (data, cid) in sorted(outputs.items()):
        if cid in preserve_ids:
            preserved.append(relative)
        else:
            files.append({"path": relative, "component": cid, "sha256": sha(data)})
    return {
        "schema_version": 1, "source_version": manifest["version"], "profile": profile,
        "managed_root_bytes": roots, "files": files, "preserved": preserved,
    }


def render(root, manifest, profile, target, include_examples=False):
    if target == root:
        if profile != manifest["self_application"]["profile"]:
            raise ValueError("self-application requires its declared profile")
        validate(root, manifest)
    elif target.exists() and any(target.iterdir()):
        raise ValueError(f"nonempty staging target: {target}")
    outputs, roots = generated_files(root, manifest, profile, include_examples)
    target.mkdir(parents=True, exist_ok=True)
    preserve_ids = set(manifest["self_application"].get("preserve", [])) if target == root else set()
    record = render_record(manifest, profile, outputs, roots, preserve_ids)
    runtime = {}
    if target != root:
        for name in ("rpi-distribution.py", "rpi-lifecycle.py", "rpi-config.py"):
            relative = f".rpi/copilot/runtime/{name}"
            if name == "rpi-distribution.py":
                runtime[relative] = (
                    b"#!/usr/bin/env python3\n"
                    b'"""Standalone Copilot RPI lifecycle entrypoint."""\n'
                    b"import runpy\nfrom pathlib import Path\n"
                    b"runpy.run_path(str(Path(__file__).with_name('rpi-lifecycle.py')), run_name='__main__')\n"
                )
            else:
                source = safe_path(root, f"templates/scripts/{name}", "runtime source")
                if not source.is_file():
                    source = Path(__file__).with_name(name)
                runtime[relative] = source.read_bytes()
            record["files"].append({"path": relative, "component": f"runtime:{name}", "sha256": sha(runtime[relative])})
        record["files"].sort(key=lambda item: item["path"])
    for relative, (data, cid) in sorted(outputs.items()):
        if cid in preserve_ids:
            continue
        path = safe_path(target, relative, "output")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for relative, data in runtime.items():
        path = safe_path(target, relative, "runtime output")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    output_manifest = safe_path(target, OUTPUT_MANIFEST, "output manifest")
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(record, indent=2) + "\n")
    print(f"rendered {len(record['files'])} files for {profile} into {target}")


def check_generated(root, manifest, profile):
    outputs = validate(root, manifest)[profile]
    preserve = set(manifest["self_application"].get("preserve", []))
    failed = []
    for relative, (data, cid) in sorted(outputs.items()):
        if cid in preserve:
            print(f"preserved owner file: {relative}")
            continue
        path = safe_path(root, relative, "active output")
        if not path.is_file() or path.read_bytes() != data:
            failed.append(relative)
    _, roots = generated_files(root, manifest, profile)
    expected_receipt = json.dumps(render_record(manifest, profile, outputs, roots, preserve), indent=2).encode() + b"\n"
    receipt_path = safe_path(root, OUTPUT_MANIFEST, "render receipt")
    if not receipt_path.is_file() or receipt_path.read_bytes() != expected_receipt:
        print(f"BLOCKED: render receipt drift: {OUTPUT_MANIFEST}")
        failed.append(OUTPUT_MANIFEST)
    if failed:
        for relative in failed:
            print(f"BLOCKED: generated drift: {relative}")
        return 1
    print(f"PASS: {profile} generated files match authored sources")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "render", "check-generated"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--source", type=Path, default=Path("."))
        if name != "validate":
            cmd.add_argument("--profile", default="cli")
        if name == "render":
            cmd.add_argument("--target", type=Path, required=True)
            cmd.add_argument("--include-examples", action="store_true")
    args = parser.parse_args()
    root = args.source.resolve()
    try:
        manifest = load_manifest(root)
        if args.command == "validate":
            validate(root, manifest)
            return 0
        if args.command == "render":
            render(root, manifest, args.profile, args.target.resolve(), args.include_examples)
            return 0
        return check_generated(root, manifest, args.profile)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        print("FIX: review the named source, manifest profile and native metadata; rerun validate --source .")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
