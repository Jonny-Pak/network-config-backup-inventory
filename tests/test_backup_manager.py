
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

import backup_manager


class BackupManagerTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.backup_patch = patch.object(
            backup_manager,
            "BACKUP_DIR",
            Path(self.temp_dir.name)
        )
        self.backup_patch.start()
        self.addCleanup(self.backup_patch.stop)

        self.device = {
            "name": "R1-CISCO",
            "host": "192.168.36.11",
            "device_type": "cisco_ios",
            "port": 22
        }

    @patch("backup_manager.ssh_connection")
    def test_backup_success(self, mock_connection):
        ssh = MagicMock()
        ssh.send_command.return_value = (
            "version 12.4\nhostname R1-CISCO\nend\n"
        )

        mock_connection.return_value.__enter__.return_value = ssh

        result = backup_manager.backup_device(
            self.device, "backupuser", "test-password"
        )

        self.assertEqual(result["status"], "success")
        self.assertTrue(Path(result["file"]).exists())
        self.assertIn(
            "hostname R1-CISCO",
            Path(result["file"]).read_text(encoding="utf-8")
        )

    @patch("backup_manager.ssh_connection")
    def test_empty_configuration(self, mock_connection):
        ssh = MagicMock()
        ssh.send_command.return_value = ""

        mock_connection.return_value.__enter__.return_value = ssh

        result = backup_manager.backup_device(
            self.device, "backupuser", "test-password"
        )

        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["file"])

    @patch("backup_manager.ssh_connection")
    def test_connection_failure(self, mock_connection):
        mock_connection.side_effect = RuntimeError("SSH timeout")

        result = backup_manager.backup_device(
            self.device, "backupuser", "test-password"
        )

        self.assertEqual(result["status"], "failed")
        self.assertIn("SSH timeout", result["error"])

    @patch("backup_manager.backup_device")
    def test_backup_all(self, mock_backup):
        devices = [
            self.device,
            {
                **self.device,
                "name": "R2-CISCO",
                "host": "192.168.36.12"
            }
        ]

        def fake_backup(device, username, password):
            return {
                "name": device["name"],
                "status": (
                    "success" if device["name"] == "R1-CISCO"
                    else "failed"
                ),
                "file": None,
                "error": None
            }

        mock_backup.side_effect = fake_backup

        results = backup_manager.backup_all(
            devices, "backupuser", "test-password",
            max_workers=2
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[1]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
