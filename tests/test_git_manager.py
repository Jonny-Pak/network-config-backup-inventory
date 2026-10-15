
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from git_manager import GitManager


class GitManagerTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.root = Path(self.temp_dir.name)
        self.manager = GitManager(
            self.root / "config_history"
        )

        self.backup = self.root / "backup.cfg"
        self.backup.write_text(
            "hostname R1-CISCO\n",
            encoding="utf-8"
        )

    def test_first_commit(self):
        result = self.manager.save_config(
            "R1-CISCO",
            self.backup
        )

        self.assertEqual(result["status"], "COMMITTED")
        self.assertTrue(result["commit"])
        self.assertTrue(
            (self.manager.repo_dir / "R1-CISCO.cfg").exists()
        )

    def test_unchanged_config(self):
        self.manager.save_config("R1-CISCO", self.backup)

        result = self.manager.save_config(
            "R1-CISCO",
            self.backup
        )

        self.assertEqual(result["status"], "UNCHANGED")
        self.assertIsNone(result["commit"])

    def test_changed_config(self):
        self.manager.save_config("R1-CISCO", self.backup)

        self.backup.write_text(
            "hostname R1-CISCO\n"
            "description CONFIG-CHANGED-TEST\n",
            encoding="utf-8"
        )

        result = self.manager.save_config(
            "R1-CISCO",
            self.backup
        )

        self.assertEqual(result["status"], "COMMITTED")

        history = self.manager.get_history("R1-CISCO")
        self.assertEqual(
            len(history.splitlines()),
            2
        )

    def test_missing_backup(self):
        with self.assertRaises(FileNotFoundError):
            self.manager.save_config(
                "R1-CISCO",
                self.root / "missing.cfg"
            )

    def test_invalid_device_name(self):
        with self.assertRaises(ValueError):
            self.manager.save_config(
                "../invalid",
                self.backup
            )


if __name__ == "__main__":
    unittest.main()
