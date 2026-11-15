import unittest
from src.secret_filter import redact_config
from src.security import validate_target
from unittest.mock import patch

class TestSecurity(unittest.TestCase):
    def test_cisco_secrets(self):
        raw = 'hostname R1\nenable secret 5 abcxyz\nusername admin secret 9 $$$abc\nsnmp-server community public RO\n'
        cleaned, count, _ = redact_config(raw)
        self.assertIn('hostname R1', cleaned)
        for secret in ('abcxyz', '$$$abc', 'public'):
            self.assertNotIn(secret, cleaned)
        self.assertGreaterEqual(count, 3)
    def test_junos(self):
        cleaned, _, _ = redact_config('set system root-authentication encrypted-password "$6$abc"\n')
        self.assertNotIn('$6$abc', cleaned)
    def test_ip_allowlist(self):
        with patch.dict('os.environ', {'BACKUP_ALLOWED_CIDRS': '192.168.56.0/24'}):
            self.assertEqual(validate_target('192.168.56.11'), '192.168.56.11')
            with self.assertRaises(PermissionError):
                validate_target('8.8.8.8')

if __name__ == '__main__':
    unittest.main()
