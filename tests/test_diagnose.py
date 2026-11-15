"""Read-only installation and project overlay diagnostics for the Copilot lifecycle runtime."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    from .lifecycle_support import load_lifecycle, overlay_tree
except ImportError:  # unittest discover -s tests imports test modules at top level.
    from lifecycle_support import load_lifecycle, overlay_tree


ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = ROOT / "templates/scripts/rpi-lifecycle.py"
DISTRIBUTION = ROOT / "templates/scripts/rpi-distribution.py"
ITEM_FIELDS = {"file", "skill", "status", "reason", "fix", "written_against", "current", "header_line", "overrides"}
INSTALLATION_FIELDS = {"status", "manifest", "profile", "source_version", "drift", "reason", "fix"}
SECTION = b"## Project overlay\n\nRead `.rpi/project/<skill>.md` when it exists.\n\n"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def skill_source(name, section=True, note=b""):
    return (b"---\nname: " + name.encode() + b"\ndescription: Test workflow.\n---\n\n# " + name.encode() + b"\n\n"
            + (SECTION if section else b"") + b"## Steps\n\nDo the work.\n" + note)


def header(skill, written_against):
    return "<!-- rpi-overlay: skill=" + skill + "; written-against=" + written_against + " -->"


def current(source):
    return sha(source)[:12]


def overlay_text(skill, written_against, body=""):
    return (header(skill, written_against) + "\n" + body).encode()


class DiagnoseTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="copilot diagnose ü ")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.target = self.base / "owner project"
        self.target.mkdir()
        self.plans = 0

    def package(self, profile, skills, authored=True, name="package"):
        """Write a rendered-package fixture; skills maps a skill name to its authored SKILL.md bytes."""
        package = self.base / (name + "-" + profile)
        records = []
        for skill, source in sorted(skills.items()):
            if profile == "vscode-local":
                relative, component = ".github/prompts/" + skill + ".prompt.md", "prompt:" + skill
                data = (b"---\nname: " + skill.encode() + b"\ndescription: \"Test workflow.\"\nagent: agent\n---\n\n"
                        b"The command invocation does not authorize external publication.\n\n"
                        + source.split(b"\n---\n", 1)[1])
            else:
                relative, component, data = ".github/skills/" + skill + "/SKILL.md", "skill:" + skill, source
            path = package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            record = {"path": relative, "component": component, "sha256": sha(data)}
            if authored:
                record["authored_sha256"] = sha(source)
            records.append(record)
        receipt = {"schema_version": 1, "source_version": "2.1.0", "profile": profile, "managed_root_bytes": 0,
                   "files": records, "preserved": []}
        (package / ".rpi").mkdir(parents=True, exist_ok=True)
        (package / ".rpi/copilot-render.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return package

    def install(self, package, profile):
        self.plans += 1
        output = self.base / ("plan-" + str(self.plans) + ".json")
        planned = subprocess.run([sys.executable, str(LIFECYCLE), "plan", "--package", str(package), "--target",
                                  str(self.target), "--profile", profile, "--output", str(output)],
                                 capture_output=True, text=True)
        self.assertEqual(0, planned.returncode, planned.stdout + planned.stderr)
        applied = subprocess.run([sys.executable, str(LIFECYCLE), "apply", "--plan", str(output)],
                                 capture_output=True, text=True)
        self.assertEqual(0, applied.returncode, applied.stdout + applied.stderr)

    def overlay(self, name, data):
        path = self.target / ".rpi/project" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def diagnose(self, *, script=LIFECYCLE, target=None, flags=()):
        result = subprocess.run([sys.executable, *flags, str(script), "diagnose", "--target", str(target or self.target)],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual({"schema_version", "target", "installation", "project_overlays"}, set(report))
        self.assertEqual(INSTALLATION_FIELDS, set(report["installation"]))
        for item in report["project_overlays"]:
            self.assertEqual(ITEM_FIELDS, set(item), item)
        report["stdout"] = result.stdout
        return report

    def items(self, report):
        return {item["file"]: item for item in report["project_overlays"]}

    def test_present_overlay_for_each_profile(self):
        source = skill_source("rpi-plan")
        expected = current(source)
        for profile in ("cli", "agent-host", "vscode-local"):
            with self.subTest(profile=profile):
                self.target = self.base / ("project-" + profile)
                self.target.mkdir()
                self.install(self.package(profile, {"rpi-plan": source}), profile)
                self.overlay("rpi-plan.md", overlay_text("rpi-plan", expected, "# Plan overlay\n\n## Procedure\n\nStep.\n"))
                report = self.diagnose()
                self.assertEqual({"status": "present", "manifest": ".rpi/copilot/manifest.json", "profile": profile,
                                  "source_version": "2.1.0", "drift": [], "reason": None, "fix": None},
                                 report["installation"])
                self.assertEqual([{"file": ".rpi/project/rpi-plan.md", "skill": "rpi-plan", "status": "present",
                                   "reason": None, "fix": None, "written_against": expected, "current": expected,
                                   "header_line": header("rpi-plan", expected), "overrides": 0}],
                                 report["project_overlays"])

    def test_stale_overlay_reports_header_line_and_recovers(self):
        source = skill_source("rpi-plan")
        self.install(self.package("cli", {"rpi-plan": source}), "cli")
        path = self.overlay("rpi-plan.md", overlay_text("rpi-plan", "0" * 12, "## Procedure\n\nStep.\n"))
        item = self.items(self.diagnose())[".rpi/project/rpi-plan.md"]
        self.assertEqual("stale", item["status"])
        self.assertEqual("0" * 12, item["written_against"])
        self.assertEqual(current(source), item["current"])
        self.assertEqual(header("rpi-plan", current(source)), item["header_line"])
        self.assertIn("header_line", item["fix"])
        lines = path.read_text().splitlines(keepends=True)
        path.write_text(item["header_line"] + "\n" + "".join(lines[1:]))
        self.assertEqual("present", self.items(self.diagnose())[".rpi/project/rpi-plan.md"]["status"])

    def test_inert_old_copy_recovers_after_update(self):
        old = skill_source("rpi-plan", section=False)
        new = skill_source("rpi-plan", section=True)
        self.install(self.package("cli", {"rpi-plan": old}, name="old"), "cli")
        self.overlay("rpi-plan.md", overlay_text("rpi-plan", current(new), "## Procedure\n\nStep.\n"))
        item = self.items(self.diagnose())[".rpi/project/rpi-plan.md"]
        self.assertEqual("inert", item["status"])
        self.assertIn("## Project overlay", item["reason"])
        self.assertIn("update", item["fix"])
        self.install(self.package("cli", {"rpi-plan": new}, name="new"), "cli")
        item = self.items(self.diagnose())[".rpi/project/rpi-plan.md"]
        self.assertEqual("present", item["status"], item)
        self.assertIsNone(item["fix"])

    def test_invalid_causes_name_their_fix(self):
        skills = {name: skill_source(name) for name in ("rpi-plan", "rpi-assess", "rpi-status", "rpi-implement",
                                                        "rpi-triage", "rpi-update", "rpi-validate", "rpi-release")}
        self.install(self.package("cli", skills), "cli")
        hashes = {name: current(source) for name, source in skills.items()}
        valid = overlay_text("rpi-plan", hashes["rpi-plan"], "## Procedure\n\nStep.\n")
        self.overlay("rpi-plan.md", valid)
        (self.target / ".rpi/project/rpi-research.md").symlink_to("rpi-plan.md")
        self.overlay("rpi-Validate.md", valid.replace(b"rpi-plan", b"rpi-validate"))
        self.overlay("rpi-implement.md", overlay_text("rpi-implement", hashes["rpi-implement"]) + b"x" * 65536)
        self.overlay("rpi-triage.md", overlay_text("rpi-triage", hashes["rpi-triage"]) + b"\xff\xfe bad\n")
        self.overlay("rpi-unknown.md", valid)
        self.overlay("rpi-debug.md", valid.replace(b"rpi-plan", b"rpi-debug"))
        self.overlay("rpi-update.md", valid.replace(b"rpi-plan", b"rpi-update"))
        (self.target / ".rpi/project/rpi-release.md").mkdir()
        self.overlay("rpi-assess.md", b"# Missing header\n\n## Procedure\n")
        self.overlay("rpi-status.md", valid)
        items = self.items(self.diagnose())
        self.assertEqual("present", items[".rpi/project/rpi-plan.md"]["status"])
        expected_fix = {
            "rpi-research.md": "regular file",
            "rpi-release.md": "regular file",
            "rpi-Validate.md": "rename .rpi/project/rpi-Validate.md to .rpi/project/rpi-validate.md",
            "rpi-implement.md": "65536",
            "rpi-triage.md": "UTF-8",
            "rpi-unknown.md": "rename or remove",
            "rpi-debug.md": "rename or remove",
            "rpi-update.md": "lifecycle",
            "rpi-assess.md": header("rpi-assess", hashes["rpi-assess"]),
            "rpi-status.md": header("rpi-status", hashes["rpi-status"]),
        }
        for name, fix in expected_fix.items():
            item = items[".rpi/project/" + name]
            with self.subTest(name=name):
                self.assertEqual("invalid", item["status"], item)
                self.assertTrue(item["reason"])
                self.assertIn(fix, item["reason"] + " " + item["fix"])
        self.assertIsNone(items[".rpi/project/rpi-unknown.md"]["skill"])
        self.assertIsNone(items[".rpi/project/rpi-update.md"]["skill"])
        self.assertEqual(header("rpi-assess", hashes["rpi-assess"]), items[".rpi/project/rpi-assess.md"]["header_line"])

    def test_no_installation_and_skipped_entries(self):
        source = skill_source("rpi-plan")
        self.overlay("rpi-plan.md", overlay_text("rpi-plan", current(source)))
        self.overlay(".DS_Store", b"\0finder")
        self.overlay(".rpi-plan.md.swp", b"swap")
        self.overlay(".rpi-plan.md", overlay_text("rpi-plan", current(source)))
        self.overlay("._rpi-plan.md", b"\0\5\26\7AppleDouble")
        self.overlay("README.txt", b"notes")
        (self.target / ".rpi/project/archive").mkdir()
        report = self.diagnose()
        self.assertEqual("missing", report["installation"]["status"])
        self.assertIn("install", report["installation"]["fix"])
        self.assertEqual([".rpi/project/rpi-plan.md"], [item["file"] for item in report["project_overlays"]])
        item = report["project_overlays"][0]
        self.assertEqual("inert", item["status"])
        self.assertIsNone(item["current"])

    def test_unreadable_manifest_reports_check_command_and_recovers(self):
        source = skill_source("rpi-plan")
        self.install(self.package("cli", {"rpi-plan": source}), "cli")
        manifest = self.target / ".rpi/copilot/manifest.json"
        valid = manifest.read_bytes()
        self.overlay("rpi-plan.md", overlay_text("rpi-plan", current(source)))
        for damaged in (b"{not json", b'{"schema_version":1,"ownership":"copilot-rpi","entries":[null]}'):
            manifest.write_bytes(damaged)
            report = self.diagnose()
            installation = report["installation"]
            self.assertEqual("unreadable", installation["status"])
            self.assertTrue(installation["reason"])
            self.assertIn(" check ", installation["fix"])
            self.assertIn("--target", installation["fix"])
            self.assertEqual("present", report["project_overlays"][0]["status"])
            self.assertIsNone(report["project_overlays"][0]["current"])
        manifest.write_bytes(valid)
        self.assertEqual("present", self.diagnose()["installation"]["status"])

    def test_drift_lists_modified_and_missing_destinations(self):
        skills = {"rpi-plan": skill_source("rpi-plan"), "rpi-assess": skill_source("rpi-assess")}
        self.install(self.package("cli", skills), "cli")
        (self.target / ".github/skills/rpi-plan/SKILL.md").write_bytes(b"owner rewrite\n")
        (self.target / ".github/skills/rpi-assess/SKILL.md").unlink()
        drift = self.diagnose()["installation"]["drift"]
        self.assertEqual([{"destination": ".github/skills/rpi-assess/SKILL.md", "state": "missing"},
                          {"destination": ".github/skills/rpi-plan/SKILL.md", "state": "modified"}], drift)

    def test_install_without_authored_hashes_skips_staleness(self):
        source = skill_source("rpi-plan")
        self.install(self.package("cli", {"rpi-plan": source}, authored=False), "cli")
        self.overlay("rpi-plan.md", overlay_text("rpi-plan", "0" * 12))
        item = self.diagnose()["project_overlays"][0]
        self.assertEqual("present", item["status"])
        self.assertIsNone(item["current"])
        self.assertIsNone(item["header_line"])
        self.assertEqual("staleness is not checked until the next update records authored hashes", item["reason"])
        self.assertIsNone(item["fix"])
        self.overlay("rpi-plan.md", b"# no header\n")
        item = self.diagnose()["project_overlays"][0]
        self.assertEqual("invalid", item["status"])
        self.assertNotIn("update", item["fix"])
        self.assertIn("rpi-overlay: skill=rpi-plan", item["fix"])

    def test_bom_crlf_and_declared_overrides(self):
        source = skill_source("rpi-release")
        self.install(self.package("cli", {"rpi-release": source}), "cli")
        line = header("rpi-release", current(source))
        entry = ('- Stock rule: "Run every check."\r\n  Override: run the fast subset first\r\n  Reason: cost\r\n'
                 '  Source: abc1234\r\n  Owner decision: 2026-11-15, docs/decisions/x.md\r\n')
        good = "﻿" + line + "\r\n# Release overlay\r\n\r\n## Procedure\r\n\r\nStep.\r\n\r\n## Declared overrides\r\n\r\n"
        self.overlay("rpi-release.md", (good + entry + entry).encode("utf-8"))
        item = self.diagnose()["project_overlays"][0]
        self.assertEqual(("present", 2, None), (item["status"], item["overrides"], item["reason"]))
        malformed = entry + '- Stock rule: "Push after review."\r\n  Override: push now\r\n'
        self.overlay("rpi-release.md", (good + malformed).encode("utf-8"))
        item = self.diagnose()["project_overlays"][0]
        self.assertEqual(("present", 2), (item["status"], item["overrides"]))
        self.assertIn("declared override 2", item["reason"])
        self.assertIn("Reason, Source, Owner decision", item["reason"])
        self.assertIn("Owner decision", item["fix"])
        self.overlay("rpi-release.md", good.encode("utf-8"))
        item = self.diagnose()["project_overlays"][0]
        self.assertEqual(0, item["overrides"])
        self.assertIn("no entries", item["reason"])

    def test_secret_marker_never_appears_in_output(self):
        marker = "SECRET-MARKER-7f3c"
        source = skill_source("rpi-plan")
        self.install(self.package("cli", {"rpi-plan": source, "rpi-assess": skill_source("rpi-assess")}), "cli")
        line = header("rpi-plan", current(source))
        self.overlay("rpi-plan.md", (line + "\n# " + marker + "\n\n## Procedure\n\n" + marker + "\n\n## Declared overrides\n\n"
                                     '- Stock rule: "' + marker + '"\n  Override: ' + marker + "\n").encode())
        self.overlay("rpi-assess.md", ("<!-- rpi-overlay: skill=rpi-assess; written-against=" + marker + " -->\n").encode())
        self.overlay("rpi-status.md", marker.encode() + b"\xff\n")
        report = self.diagnose()
        self.assertEqual(3, len(report["project_overlays"]))
        self.assertNotIn(marker, report["stdout"])

    def test_diagnose_is_read_only(self):
        self.install(self.package("cli", {"rpi-plan": skill_source("rpi-plan")}), "cli")
        self.overlay("rpi-plan.md", b"# no header\n")
        (self.target / ".rpi/project/rpi-research.md").symlink_to("../../outside.md")
        before = overlay_tree(self.target)
        self.diagnose()
        self.assertEqual(before, overlay_tree(self.target))

    def test_symlinked_project_directory_and_bad_target_still_exit_zero(self):
        outside = self.base / "outside overlays"
        outside.mkdir()
        (outside / "rpi-plan.md").write_text(header("rpi-plan", "0" * 12) + "\n")
        (self.target / ".rpi").mkdir()
        (self.target / ".rpi/project").symlink_to(outside, target_is_directory=True)
        report = self.diagnose()
        self.assertEqual([".rpi/project"], [item["file"] for item in report["project_overlays"]])
        self.assertEqual("invalid", report["project_overlays"][0]["status"])
        self.assertIn("regular directory", report["project_overlays"][0]["fix"])
        missing = self.diagnose(target=self.base / "no such project")
        self.assertEqual("unreadable", missing["installation"]["status"])
        self.assertEqual([], missing["project_overlays"])

    def test_deeply_nested_manifest_still_exits_zero(self):
        manifest = self.target / ".rpi/copilot/manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("[" * 200000 + "]" * 200000)
        installation = self.diagnose()["installation"]
        self.assertEqual("unreadable", installation["status"])
        self.assertIn(" check ", installation["fix"])

    def test_unexpected_error_prints_minimal_report_and_exits_zero(self):
        import contextlib
        import io
        module = load_lifecycle()

        def broken(target):
            raise RuntimeError("SECRET-MARKER-guard")
        module.diagnose = broken
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = module.command(["diagnose", "--target", str(self.target)])
        self.assertEqual(0, code)
        report = json.loads(output.getvalue())
        self.assertEqual({"schema_version", "target", "installation", "project_overlays"}, set(report))
        self.assertEqual(INSTALLATION_FIELDS, set(report["installation"]))
        self.assertEqual("unreadable", report["installation"]["status"])
        self.assertIn("RuntimeError", report["installation"]["reason"])
        self.assertNotIn("SECRET-MARKER-guard", output.getvalue())
        self.assertIn(" check ", report["installation"]["fix"])
        self.assertEqual([], report["project_overlays"])

    def test_symlinked_rpi_directory_names_the_symlink(self):
        outside = self.base / "outside state"
        (outside / "project").mkdir(parents=True)
        (outside / "project/rpi-plan.md").write_text(header("rpi-plan", "0" * 12) + "\n")
        (self.target / ".rpi").symlink_to(outside, target_is_directory=True)
        items = self.diagnose()["project_overlays"]
        self.assertEqual([".rpi/project"], [item["file"] for item in items])
        link = str(self.target.resolve() / ".rpi")
        self.assertEqual("invalid", items[0]["status"])
        self.assertIn("symlink", items[0]["reason"])
        self.assertIn(link, items[0]["reason"])
        self.assertIn(link, items[0]["fix"])

    def test_distribution_forwards_diagnose_without_pyyaml(self):
        source = skill_source("rpi-plan")
        self.install(self.package("cli", {"rpi-plan": source}), "cli")
        self.overlay("rpi-plan.md", overlay_text("rpi-plan", current(source)))
        report = self.diagnose(script=DISTRIBUTION, flags=("-S",))
        self.assertEqual("present", report["project_overlays"][0]["status"])

    def test_engine_skill_sets_match_distribution_manifest(self):
        module = load_lifecycle()
        manifest = json.loads((ROOT / "templates/distribution.json").read_text())
        skills = {item["id"].split(":", 1)[1] for item in manifest["components"] if item["kind"] == "skill"}
        self.assertEqual(16, len(module.OVERLAY_SKILLS))
        self.assertEqual({"rpi-adopt", "rpi-bootstrap", "rpi-detach", "rpi-update"}, set(module.LIFECYCLE_SKILLS))
        self.assertLessEqual(set(module.OVERLAY_SKILLS) | set(module.LIFECYCLE_SKILLS), skills)
        self.assertFalse(set(module.OVERLAY_SKILLS) & set(module.LIFECYCLE_SKILLS))


if __name__ == "__main__":
    unittest.main()
