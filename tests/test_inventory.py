
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from inventory import load_inventory


class InventoryTests(unittest.TestCase):

    def create_yaml(self, content):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)

        path = Path(temp.name) / "devices.yaml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_inventory(self):
        path = self.create_yaml("""
devices:
  - name: R1-CISCO
    host: 192.168.36.11
    device_type: cisco_ios
    port: 22
""")
        devices = load_inventory(path)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["name"], "R1-CISCO")

    def test_invalid_ip(self):
        path = self.create_yaml("""
devices:
  - name: R1-CISCO
    host: 999.168.36.11
    device_type: cisco_ios
""")
        with self.assertRaises(ValueError):
            load_inventory(path)

    def test_duplicate_device(self):
        path = self.create_yaml("""
devices:
  - name: R1-CISCO
    host: 192.168.36.11
    device_type: cisco_ios
  - name: R1-CISCO
    host: 192.168.36.12
    device_type: cisco_ios
""")
        with self.assertRaises(ValueError):
            load_inventory(path)


if __name__ == "__main__":
    unittest.main()
