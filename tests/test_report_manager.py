
import sys
import csv
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from report_manager import export_csv_report


class ReportManagerTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.report_dir = Path(self.temp_dir.name) / "reports"

        self.records = [
            {
                "Device": "R1-CISCO",
                "IP": "192.168.36.11",
                "Backup Status": "SUCCESS",
                "Change Status": "CHANGED",
                "Git Status": "COMMITTED",
                "Commit": "abc123",
                "Error": ""
            },
            {
                "Device": "R2-CISCO",
                "IP": "192.168.36.12",
                "Backup Status": "SUCCESS",
                "Change Status": "UNCHANGED",
                "Git Status": "UNCHANGED",
                "Commit": "",
                "Error": ""
            }
        ]

    def read_report(self, path):
        with path.open(
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:
            return list(csv.DictReader(file))

    def test_csv_created(self):
        path = export_csv_report(
            self.records,
            self.report_dir
        )

        self.assertTrue(path.is_file())
        self.assertEqual(path.suffix, ".csv")

    def test_csv_content(self):
        path = export_csv_report(
            self.records,
            self.report_dir
        )

        rows = self.read_report(path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Device"], "R1-CISCO")
        self.assertEqual(rows[0]["Change Status"], "CHANGED")
        self.assertEqual(rows[0]["Commit"], "abc123")
        self.assertEqual(rows[1]["Git Status"], "UNCHANGED")

    def test_empty_report(self):
        path = export_csv_report(
            [],
            self.report_dir
        )

        rows = self.read_report(path)
        self.assertEqual(rows, [])

    def test_unique_filename(self):
        first = export_csv_report(
            self.records,
            self.report_dir
        )

        second = export_csv_report(
            self.records,
            self.report_dir
        )

        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
