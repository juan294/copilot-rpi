"""Permanent Copilot catalog IDs and the upstream meaning crosswalk."""

import json
import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_RULE_IDS = sorted(set(range(1, 96)) - {67, 69, 80})
# Reviewed Copilot catalog identity at the P1 boundary. These digests cover
# ordered permanent ID and title pairs independently of the editable crosswalk.
ERROR_IDENTITY_SHA256 = "df55b5e315cc8bf3525ffc34bac0a95138ad89957710bd8f53c6c1088b6a2a06"
RULE_IDENTITY_SHA256 = "fa2c189bcd783576f540fc9e87b620276f31e9e359f4935164c2a232b7ac1792"
EXPECTED_ERROR_MAP = {
    1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10, 8: 11,
    9: 12, 10: 13, 11: 14, 12: 15, 18: 38, 19: 33, 20: 44,
    21: 45, 22: 46, 23: 47, 24: 48, 25: 49, 26: 50, 27: 51,
    28: 52, 29: 53, 30: 54, 31: 55, 32: 56, 33: 57, 34: 58,
    35: 59, 36: 60, 37: 61, 38: 62, 39: 63, 40: 64,
}
EXPECTED_RULE_MAP = {
    1: 5, 2: 14, 3: 49, 4: 51, 5: 6, 6: 7, 7: 8, 8: 15,
    9: 33, 10: 48, 11: 52, 12: 9, 13: 10, 14: 56, 15: 57,
    16: 12, 17: 13, 18: 54, 19: 50, 26: 4, 27: 11, 28: 53,
    29: 55, 30: 62, 31: 63, 32: 64, 33: 65, 34: 66, 36: 72,
    37: 58, 38: 68, 39: 38, 40: 60, 41: 61, 42: 70, 43: 71,
    44: 73, 45: 84, 46: 74, 47: 75, 48: 78, 49: 79, 50: 31,
    51: 81, 52: 82, 53: 76, 54: 77, 55: 83,
}


def ids(path: Path, pattern: str) -> list[int]:
    return [int(value) for value in re.findall(pattern, path.read_text(), re.MULTILINE)]


def identity_digest(rows: list[dict]) -> str:
    pairs = "".join(f"{row['id']}\0{row['title']}\n" for row in sorted(rows, key=lambda row: row["id"]))
    return hashlib.sha256(pairs.encode()).hexdigest()


class CatalogCrosswalkTests(unittest.TestCase):
    def test_copilot_ids_are_permanent_and_complete(self):
        self.assertEqual(
            ids(ROOT / "patterns/agent-errors.md", r"^## Error #(\d+):"),
            list(range(1, 41)),
        )
        self.assertEqual(
            sorted(ids(ROOT / "patterns/quick-reference.md", r"^(\d+)\. \*\*")),
            list(range(1, 56)),
        )

    def test_crosswalk_covers_each_local_and_upstream_id_once(self):
        crosswalk = json.loads((ROOT / "docs/upstream-catalog-crosswalk.json").read_text())
        for kind, expected in (("errors", range(1, 41)), ("rules", range(1, 56))):
            rows = crosswalk[f"copilot_{kind}"]
            self.assertEqual(sorted(row["id"] for row in rows), list(expected))
            for row in rows:
                self.assertIn(row["disposition"], {"retained", "adapted", "deferred", "retired"})
                self.assertTrue(row["rationale"])
                self.assertTrue(row["upstream_ids"] or row["disposition"] == "deferred")
        for kind, source_ids in (("errors", list(range(1, 65))), ("rules", UPSTREAM_RULE_IDS)):
            upstream = crosswalk[f"upstream_{kind}"]
            self.assertEqual(sorted(row["id"] for row in upstream), sorted(source_ids))
            for row in upstream:
                self.assertIn(row["disposition"], {"adopted", "adapted", "deferred", "inapplicable"})
                self.assertTrue(row["rationale"])
            local = crosswalk[f"copilot_{kind}"]
            for row in local:
                for upstream_id in row["upstream_ids"]:
                    reverse = next(item for item in upstream if item["id"] == upstream_id)
                    self.assertIn(row["id"], reverse["copilot_ids"])

    def test_catalog_policy_has_no_automatic_remote_or_model_tier_default(self):
        rules = (ROOT / "patterns/quick-reference.md").read_text()
        self.assertNotIn("Pin a model tier to every workflow", rules)
        self.assertNotIn("fix and re-push", rules)
        self.assertNotIn("auto-merge patch/minor", rules)
        methodology = "\n".join(path.read_text() for path in (ROOT / "methodology").glob("*.md"))
        self.assertNotIn("Every prompt in this blueprint declares a **model tier**", methodology)
        self.assertNotIn("background process owns the push outcome", methodology)
        self.assertNotIn("Pushes all branches in one burst", methodology)

    def test_crosswalk_titles_and_meaning_links_match_catalogs(self):
        crosswalk = json.loads((ROOT / "docs/upstream-catalog-crosswalk.json").read_text())
        for kind, pattern, expected_map in (
            ("errors", r"^## Error #(\d+): (.+)$", EXPECTED_ERROR_MAP),
            ("rules", r"^(\d+)\. \*\*(.+?)\*\*", EXPECTED_RULE_MAP),
        ):
            filename = "agent-errors.md" if kind == "errors" else "quick-reference.md"
            body = (ROOT / "patterns" / filename).read_text()
            titles = {int(number): title for number, title in re.findall(pattern, body, re.MULTILINE)}
            local = crosswalk[f"copilot_{kind}"]
            self.assertEqual({row["id"]: row["title"] for row in local}, titles)
            self.assertEqual(
                {row["id"]: row["upstream_ids"][0] for row in local if row["upstream_ids"]},
                expected_map,
            )
            source_body = (ROOT / "upstream" / "snapshots" / "patterns" / filename).read_text()
            source_pattern = r"^## Error #(\d+): (.+)$" if kind == "errors" else r"^(\d+)\. (.+?) ->"
            source_titles = {int(number): title for number, title in re.findall(source_pattern, source_body, re.MULTILINE)}
            upstream = crosswalk[f"upstream_{kind}"]
            self.assertEqual({row["id"]: row["title"] for row in upstream}, source_titles)
        rules = {row["id"]: row for row in crosswalk["copilot_rules"]}
        self.assertIn("preserve", rules[6]["title"].lower())
        self.assertIn("integrate", rules[6]["title"].lower())

    def test_permanent_id_title_identity_rejects_simultaneous_swaps(self):
        crosswalk = json.loads((ROOT / "docs/upstream-catalog-crosswalk.json").read_text())
        for kind, expected in (("errors", ERROR_IDENTITY_SHA256), ("rules", RULE_IDENTITY_SHA256)):
            rows = crosswalk[f"copilot_{kind}"]
            self.assertEqual(identity_digest(rows), expected)
            swapped = [row.copy() for row in rows]
            swapped[0]["title"], swapped[1]["title"] = swapped[1]["title"], swapped[0]["title"]
            # Model the same incorrect edit in both the catalog headings and
            # crosswalk: their mutual agreement cannot replace this baseline.
            filename = "agent-errors.md" if kind == "errors" else "quick-reference.md"
            pattern = r"^## Error #(\d+): (.+)$" if kind == "errors" else r"^(\d+)\. \*\*(.+?)\*\*"
            body = (ROOT / "patterns" / filename).read_text()
            catalog_titles = {int(number): title for number, title in re.findall(pattern, body, re.MULTILINE)}
            catalog_titles[1], catalog_titles[2] = catalog_titles[2], catalog_titles[1]
            self.assertEqual(catalog_titles, {row["id"]: row["title"] for row in swapped})
            self.assertNotEqual(identity_digest(swapped), expected)


if __name__ == "__main__":
    unittest.main()
