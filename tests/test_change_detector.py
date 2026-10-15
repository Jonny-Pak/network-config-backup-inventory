
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from change_detector import detect_changes


class ChangeDetectorTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_backup(self, filename, content):
        file = self.path / filename
        file.write_text(content, encoding="utf-8")
        return file

    def test_no_backup(self):
        result = detect_changes("R1-CISCO", self.path)
        self.assertEqual(result["status"], "NO_BACKUP")

    def test_first_backup(self):
        self.create_backup(
            "R1-CISCO_001.cfg",
            "hostname R1-CISCO\n"
        )

        result = detect_changes("R1-CISCO", self.path)
        self.assertEqual(result["status"], "FIRST_BACKUP")

    def test_unchanged(self):
        self.create_backup(
            "R1-CISCO_001.cfg",
            "hostname R1-CISCO\n"
        )
        self.create_backup(
            "R1-CISCO_002.cfg",
            "hostname R1-CISCO\n"
        )

        result = detect_changes("R1-CISCO", self.path)
        self.assertEqual(result["status"], "UNCHANGED")

    def test_changed(self):
        self.create_backup(
            "R1-CISCO_001.cfg",
            "hostname R1-CISCO\n"
        )
        self.create_backup(
            "R1-CISCO_002.cfg",
            "hostname R1-CISCO-NEW\n"
        )

        result = detect_changes("R1-CISCO", self.path)
        self.assertEqual(result["status"], "CHANGED")
        self.assertIn("R1-CISCO-NEW", result["diff"])


if __name__ == "__main__":
    unittest.main()
