#!/usr/bin/env python3
"""Fake CLI boundary for native harness tests. No network or inference."""

import os
import json
from pathlib import Path
import re
import sys
import time


HELP = "-p -s --no-ask-user --available-tools --allow-tool --deny-tool --model --no-remote --no-remote-export --no-auto-update --secret-env-vars --output-format"
mode = os.environ.get("RPI_NATIVE_FAKE_MODE", "ok")
if os.environ.get("COPILOT_GITHUB_TOKEN") == "force-missing-auth":
    mode = "missing-auth"
elif os.environ.get("COPILOT_GITHUB_TOKEN") == "force-omit-marker":
    mode = "omit-marker"
elif os.environ.get("COPILOT_GITHUB_TOKEN") == "force-sleep":
    mode = "sleep"
args = sys.argv[1:]
if args == ["--version"]:
    print("fake-copilot 1.2.3" + ("x" * 5000 if mode == "long-version" else ""))
elif args == ["--help"]:
    print("-p" if mode == "old-help" else HELP)
elif args == ["skill", "list", "--json"]:
    skill = Path(".github/skills/rpi-research")
    print(json.dumps([{"name": "rpi-research", "source": "project", "path": str(skill.resolve()),
                       "enabled": True}] if skill.is_dir() else []))
elif mode == "missing-auth":
    print("authentication required", file=sys.stderr)
    sys.exit(2)
elif mode == "sleep":
    time.sleep(20)
elif mode == "echo-secret":
    print("token=" + os.environ.get("COPILOT_GITHUB_TOKEN", ""))
elif "-p" not in args:
    print("missing prompt", file=sys.stderr)
    sys.exit(2)
else:
    prompt = args[args.index("-p") + 1]
    source = Path("README.md") if "/rpi-research" in prompt else Path("docs/agents/fixture-report.md")
    match = re.search(r"NATIVE_FIXTURE_[0-9a-f]{16}", source.read_text())
    marker = match.group() if match else "missing-marker"
    if "denied-write" in prompt:
        if mode == "write-anyway":
            Path("denied-write.txt").write_text("changed despite denial\n")
        if mode == "prose-denial":
            print("Permission denied: write tool unavailable")
        else:
            print('{"type":"permission.requested","data":{"requestId":"native-write-1","permissionRequest":{"kind":"write","fileName":"denied-write.txt"}}}')
            finished_id = "other-request" if mode == "mismatched-event" else "native-write-1"
            print('{"type":"permission.completed","data":{"requestId":"' + finished_id + '","result":{"kind":"denied-by-rules"}}}')
            if mode != "no-denial-report":
                print('{"type":"assistant.message","data":{"content":"Write was denied"}}')
    elif "/rpi-research" in prompt:
        if mode == "prompt-echo":
            print(prompt)
            sys.exit(0)
        if not Path(".github/skills/rpi-research/SKILL.md").exists():
            print("unknown skill: rpi-research", file=sys.stderr)
            sys.exit(2)
        suffix = ("; unrelated_present=" + str("UNRELATED_SECRET" in os.environ).lower()) if mode == "env-check" else ""
        answer = json.dumps({"type": "assistant.message", "data": {
            "content": "Research result: " + marker + "; no product files changed" + suffix}})
        missing_explicit_call = (mode == "requires-tool-first"
                                 and "First invoke the skill tool" not in prompt)
        if mode != "no-skill-event" and not missing_explicit_call:
            print(json.dumps({"type": "tool.execution_start", "data": {
                "toolCallId": "fake-skill-call", "toolName": "skill", "arguments": {"skill": "rpi-research"}}}))
            if mode == "answer-before-skill-complete":
                print(answer)
            print(json.dumps({"type": "tool.execution_complete", "data": {
                "toolCallId": "fake-skill-call", "success": mode != "failed-skill-event"}}))
        if mode != "answer-before-skill-complete":
            print(answer)
    else:
        print("Ready plan: " + ("no findings" if mode == "omit-marker" else marker) + ". No changes made.")
