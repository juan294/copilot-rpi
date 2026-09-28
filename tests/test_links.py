import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check-links.py"


class LinkCheckTests(unittest.TestCase):
    def run_check(self, content: str, other: bool = False) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(content)
            if other:
                (root / "target.md").write_text("# Target\n")
            return subprocess.run(
                ["python3", str(SCRIPT), "--root", directory],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_existing_relative_link_passes(self) -> None:
        self.assertEqual(0, self.run_check("[target](target.md)\n", True).returncode)

    def test_missing_relative_link_fails_with_source(self) -> None:
        result = self.run_check("[missing](lost.md)\n")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("README.md:1", result.stdout)

    def test_external_and_valid_anchor_links_pass(self) -> None:
        self.assertEqual(
            0,
            self.run_check("# Title\n[web](https://example.com) [here](#title)\n").returncode,
        )

    def test_missing_anchor_fails(self) -> None:
        result = self.run_check("# Title\n[bad](#absent)\n")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("README.md:2", result.stdout)

    def test_ignored_runtime_file_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Readme\n")
            (root / ".rpi/local").mkdir(parents=True)
            (root / ".rpi/local/runtime.md").write_text("[bad](gone.md)\n")
            result = subprocess.run(
                ["python3", str(SCRIPT), "--root", directory],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
