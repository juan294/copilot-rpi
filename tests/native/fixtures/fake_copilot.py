#!/usr/bin/env python3
"""Fake CLI boundary for native harness tests. No network or inference."""

import os
from pathlib import Path
import re
import sys
import time


HELP = "-p -s --no-ask-user --available-tools --allow-tool --deny-tool --model --no-remote --no-remote-export --no-auto-update --secret-env-vars --output-format"
mode = os.environ.get("RPI_NATIVE_FAKE_MODE", "ok")
if os.environ.get("COPILOT_GITHUB_TOKEN") == "force-missing-auth":
    mode = "missing-auth"
args = sys.argv[1:]
if args == ["--version"]:
    print("fake-copilot 1.2.3")
elif args == ["--help"]:
    print("-p" if mode == "old-help" else HELP)
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
        print("Research result: " + marker + "; no product files changed" + suffix)
    else:
        print("Ready plan: " + marker + ". No changes made.")
