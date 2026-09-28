"""The finding parser rejects malformed or undisposed findings."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "templates/scripts/validate-findings.py"
BUNDLED = ROOT / "templates/skills/rpi-remediate/scripts/validate-findings.py"
SPEC = importlib.util.spec_from_file_location("copilot_findings", MODULE)
findings = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(findings)

VALID = """## Backend
#### BE-H1 Query has unbounded cost
- **Severity:** high
- **Time horizon:** Before launch
- **Evidence type:** [evidence]
- **Files:** src/query.py:42
- **What's happening:** Rows grow without limit.
- **Why it matters:** Latency rises.
- **Recommendation:** Bound the result.
- **Regression risk:** Existing pagination must retain order.
- **Expected impact:** Stable latency.
- **Effort estimate:** M
"""


class FindingsTest(unittest.TestCase):
    def test_valid_report_and_invalid_id(self):
        self.assertEqual([], findings.validate_text(VALID))
        self.assertTrue(findings.validate_text(VALID.replace("BE-H1", "be-h1")))

    def test_missing_required_field_and_file_line(self):
        report = VALID.replace("- **Recommendation:** Bound the result.\n", "")
        report = report.replace("src/query.py:42", "src/query.py")
        errors = findings.validate_text(report)
        self.assertTrue(any("Recommendation" in reason for _, reason in errors))
        self.assertTrue(any("file:line" in reason for _, reason in errors))

    def test_dispositions_match_report_and_require_evidence(self):
        items = [{"id": "BE-H1", "disposition": "resolved", "evidence": "tests/query.py:18"}]
        self.assertEqual([], findings.validate_dispositions(VALID, items))
        self.assertTrue(findings.validate_dispositions(VALID, []))
        self.assertTrue(findings.validate_dispositions(VALID, [{**items[0], "evidence": ""}]))
        self.assertTrue(findings.validate_dispositions(VALID, [{**items[0], "disposition": "strategic"}]))
        self.assertEqual([], findings.validate_dispositions(VALID, [{"id": "BE-H1", "disposition": "architectural_exception", "evidence": "owner decision", "owner_review": "approved"}]))

    def test_malformed_report_blocks_disposition(self):
        malformed = VALID.replace("src/query.py:42", "no reference")
        errors = findings.validate_dispositions(malformed, [{"id": "BE-H1", "disposition": "resolved", "evidence": "ok"}])
        self.assertTrue(any("file:line" in reason for _, reason in errors))

    def test_cli_blocks_bad_report_and_recovers_with_disposition(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.md"
            decisions = Path(directory) / "decisions.json"
            decisions.write_text(json.dumps([{"id": "BE-H1", "disposition": "resolved", "evidence": "tests/test_query.py:12"}]))
            report.write_text(VALID.replace("src/query.py:42", "src/query.py"))
            command = [sys.executable, str(MODULE), str(report), "--dispositions", str(decisions)]
            self.assertNotEqual(0, subprocess.run(command, capture_output=True).returncode)
            report.write_text(VALID)
            self.assertEqual(0, subprocess.run(command, capture_output=True).returncode)

    def test_bundled_validator_requires_final_dispositions(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.md"
            decisions = Path(directory) / "decisions.json"
            report.write_text(VALID)
            decisions.write_text("[]")
            command = [sys.executable, str(BUNDLED), str(report), "--dispositions", str(decisions)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(1, result.returncode)
            self.assertIn("finding disposition gap", result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
