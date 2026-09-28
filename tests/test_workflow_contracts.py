"""Static contract checks for authored Copilot RPI workflows.

These checks validate instructions and scenario rubrics. Native agent behavior is
measured separately during qualification.
"""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "templates" / "skills"
FIXTURES = ROOT / "tests" / "fixtures" / "workflows"

OLD_PROMPTS = {
    "adopt", "bootstrap", "brainstorm", "debug", "describe-pr", "detach",
    "explore-release", "fix-ci", "implement", "plan", "pre-launch",
    "quality-review", "release", "remediate", "research", "status",
    "triage", "update-docs", "update", "validate",
}
NEW_WORKFLOWS = OLD_PROMPTS | {"assess", "tool-design"}


class WorkflowContracts(unittest.TestCase):
    def test_each_legacy_prompt_has_one_canonical_skill(self):
        prompts = {path.name.removesuffix(".prompt.md") for path in
                   (ROOT / "templates" / "prompts").glob("*.prompt.md")}
        self.assertEqual(OLD_PROMPTS, prompts)
        skills = {path.parent.name.removeprefix("rpi-") for path in
                  SKILLS.glob("rpi-*/SKILL.md")}
        self.assertEqual(NEW_WORKFLOWS, skills)
        self.assertTrue((SKILLS / "process-errors" / "SKILL.md").is_file())

    def test_skill_metadata_and_local_resources(self):
        for path in SKILLS.glob("*/SKILL.md"):
            with self.subTest(skill=path.parent.name):
                body = path.read_text()
                self.assertRegex(body, r"(?s)\A---\nname: [a-z][a-z0-9-]+\n")
                self.assertIn(f"name: {path.parent.name}\n", body)
                self.assertIn("description:", body)
                self.assertNotRegex(body, r"Model tier:|invoke this prompt in an? (Opus|Sonnet|Haiku) session")
                for target in re.findall(r"\]\((references/[^)#]+|scripts/[^)#]+)\)", body):
                    self.assertTrue((path.parent / target).is_file(), f"{path}: missing {target}")

    def test_six_behavioral_rubrics(self):
        files = sorted(FIXTURES.glob("*.json"))
        self.assertEqual(6, len(files))
        for path in files:
            with self.subTest(scenario=path.stem):
                case = json.loads(path.read_text())
                self.assertEqual(path.stem, case["id"])
                for field in ("request", "skill", "expected_artifact_fields", "required_clauses", "positive_example", "negative_example", "prohibited_claims"):
                    self.assertTrue(case[field], f"{path}: empty {field}")
                body = (SKILLS / case["skill"] / "SKILL.md").read_text().lower()
                for clause in case["required_clauses"]:
                    self.assertIn(clause.lower(), body, f"{path}: {clause}")

    def test_portable_authority_boundaries(self):
        combined = "\n".join(path.read_text().lower() for path in SKILLS.glob("*/SKILL.md"))
        self.assertNotIn("@copilot issues", combined)
        self.assertNotIn("enable auto-merge", combined)
        self.assertNotIn("use a fix-and-repush loop", combined)
        for name in ("rpi-implement", "rpi-triage", "rpi-remediate", "rpi-release"):
            body = (SKILLS / name / "SKILL.md").read_text().lower()
            self.assertIn("local", body)
            self.assertIn("authoriz", body)
        triage = (SKILLS / "rpi-triage" / "SKILL.md").read_text().lower()
        self.assertIn("stop at that read-only briefing", triage)
        self.assertIn("only after explicit remediation authorization", triage)


if __name__ == "__main__":
    unittest.main()
