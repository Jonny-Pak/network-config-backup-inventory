
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from config_diff import compare_configs, has_changes


class ConfigDiffTests(unittest.TestCase):

    def setUp(self):
        fixtures = ROOT / "tests" / "fixtures"
        self.old = fixtures / "r1_old.cfg"
        self.new = fixtures / "r1_new.cfg"

    def test_detect_changes(self):
        self.assertTrue(has_changes(self.old, self.new))

    def test_no_changes(self):
        self.assertFalse(has_changes(self.old, self.old))

    def test_diff_content(self):
        diff = compare_configs(self.old, self.new)
        self.assertIn("- description OLD-CONFIG", diff)
        self.assertIn("+ description NEW-CONFIG", diff)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            compare_configs("missing.cfg", self.new)


if __name__ == "__main__":
    unittest.main()
