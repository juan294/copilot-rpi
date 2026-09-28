#!/usr/bin/env python3
"""Check local targets of Markdown links without network access."""

import argparse
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


LINK = re.compile(r"!?(?:\[[^\]]*\])\((<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)")
SKIP_PARTS = {".git", ".venv", ".claude", "node_modules", "graphify-out", "upstream"}


def markdown_sources(root: Path) -> list[Path]:
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if listed.returncode == 0:
        candidates = (root / name.decode() for name in listed.stdout.split(b"\0") if name)
    else:
        candidates = root.rglob("*.md")
    return sorted(
        path for path in candidates
        if path.suffix == ".md"
        and path.is_file()
        and not any(part in SKIP_PARTS for part in path.relative_to(root).parts)
        and path.relative_to(root).parts[:2] != (".rpi", "local")
    )


def anchors(path: Path) -> set[str]:
    found = set()
    seen = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        if heading:
            title = re.sub(r"<[^>]+>", "", heading.group(1)).lower()
            title = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE)
            slug = re.sub(r"\s+", "-", title.strip())
            count = seen.get(slug, 0)
            seen[slug] = count + 1
            found.add(f"{slug}-{count}" if count else slug)
        found.update(re.findall(r'<a\s+[^>]*id=["\']([^"\']+)["\']', line))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    problems = []
    checked = 0
    for source in markdown_sources(root):
        for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            for match in LINK.finditer(line):
                raw = match.group(1).strip("<>")
                parsed = urlsplit(raw)
                if parsed.scheme or parsed.netloc:
                    continue
                target = unquote(parsed.path)
                resolved = (
                    (root if target.startswith("/") else source.parent) / target.lstrip("/")
                ).resolve() if target else source
                checked += 1
                if not resolved.is_relative_to(root) or not resolved.exists():
                    problems.append(f"{source.relative_to(root)}:{line_number}: missing {raw}")
                elif parsed.fragment and resolved.suffix == ".md" and unquote(parsed.fragment) not in anchors(resolved):
                    problems.append(f"{source.relative_to(root)}:{line_number}: missing anchor {raw}")
    if problems:
        for problem in problems:
            print(f"BLOCKED: {problem}\nWHY: local link target or anchor is absent\nFIX: correct the link or add the target")
        return 1
    print(f"PASS: {checked} local Markdown links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
