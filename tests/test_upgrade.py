import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src import main, backup_manager, scheduler, run_backup
from src.runtime import run_lock, AlreadyRunning, ROOT
from src.secret_filter import redact_config
from src.ssh_connector import ssh_connection, get_credentials
from src.git_manager import GitManager
from src.change_detector import detect_changes


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.device = {"name": "J1", "host": "192.168.36.13", "device_type": "juniper_junos"}

    def test_junos_command_and_redaction_before_disk(self):
        connection = MagicMock()
        connection.send_command.return_value = 'set system root-authentication encrypted-password "PRIVATE_VALUE"\nset system host-name J1\n'
        with patch.object(backup_manager, 'ssh_connection') as connect:
            connect.return_value.__enter__.return_value = connection
            result = backup_manager.backup_device(self.device, 'user', 'pass', self.path)
        self.assertEqual(result['status'], 'success')
        connection.send_command.assert_called_once_with('show configuration | display set | no-more', read_timeout=90)
        self.assertNotIn('PRIVATE_VALUE', Path(result['file']).read_text())

    def test_exceptions_do_not_leak_credentials(self):
        with patch.object(backup_manager, 'ssh_connection', side_effect=RuntimeError('PASSWORD_SHOULD_NOT_APPEAR')):
            result = backup_manager.backup_device(self.device, 'user', 'pass', self.path)
        self.assertNotIn('PASSWORD_SHOULD_NOT_APPEAR', json.dumps(result))
        self.assertEqual(list(self.path.glob('*.cfg')), [])

    def test_allowlist_precedes_connect_and_strict_keys(self):
        with patch.dict(os.environ, {'BACKUP_ALLOWED_CIDRS': '192.168.36.0/24', 'BACKUP_KNOWN_HOSTS': ''}), patch('src.ssh_connector.ConnectHandler') as connect:
            with self.assertRaises(PermissionError):
                with ssh_connection({**self.device, 'host': '8.8.8.8'}, 'u', 'p'):
                    pass
            connect.assert_not_called()
            with ssh_connection(self.device, 'u', 'p'):
                pass
            self.assertTrue(connect.call_args.kwargs['ssh_strict'])
            self.assertTrue(connect.call_args.kwargs['system_host_keys'])

    def test_unattended_no_prompt(self):
        with patch.dict(os.environ, {}, clear=True), patch('sys.stdin.isatty', return_value=False), patch('builtins.input') as prompt:
            with self.assertRaises(ValueError):
                get_credentials()
            prompt.assert_not_called()

    def test_redaction_blocks_idempotent_and_unknown_secret(self):
        raw = '-----BEGIN PRIVATE KEY-----\nPRIVATE_MATERIAL\n-----END PRIVATE KEY-----\ncustom token PRIVATE_TOKEN\nusername admin privilege 15 secret 9 PRIVATE_HASH\n'
        clean = redact_config(raw)[0]
        for value in ('PRIVATE_MATERIAL', 'PRIVATE_TOKEN', 'PRIVATE_HASH'):
            self.assertNotIn(value, clean)
        self.assertEqual(clean, redact_config(clean)[0])

    def test_cross_process_lock_released(self):
        code = "from pathlib import Path; from src.runtime import run_lock; import sys;\nwith run_lock(Path(sys.argv[1])): pass"
        with run_lock(self.path):
            result = subprocess.run([sys.executable, '-c', code, str(self.path)], cwd=ROOT, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
        with run_lock(self.path):
            pass

    def test_scheduler_failure_exit_and_demo_forwarding(self):
        with patch.object(scheduler, 'execute', return_value={'status': 'FAILED'}) as execute:
            self.assertEqual(scheduler.main(['--once', '--demo']), 1)
            execute.assert_called_once_with(demo=True)

    def test_runner_timeout_report(self):
        with patch.object(run_backup, 'REPORTS', self.path), patch.object(run_backup.subprocess, 'run', side_effect=subprocess.TimeoutExpired('backup', 1)):
            report = run_backup.execute()
        self.assertEqual(report['error_type'], 'TIMEOUT')
        self.assertEqual(json.loads((self.path / 'scheduler_status.json').read_text())['status'], 'FAILED')

    def test_demo_pipeline_unchanged_and_changed_git(self):
        devices = [self.device, {**self.device, 'name': 'R1', 'device_type': 'cisco_ios'}]
        first = main.run(devices, self.path, demo=True)
        self.assertEqual(first['status'], 'SUCCESS')
        self.assertEqual([r['Change Status'] for r in first['devices']], ['FIRST_BACKUP'] * 2)
        second = main.run(devices, self.path, demo=True)
        self.assertTrue(all(r['Git Status'] == 'UNCHANGED' for r in second['devices']))
        # Change only the source sample returned for Cisco; do not edit real fixtures.
        read_text = Path.read_text
        def changed_read(path, *args, **kwargs):
            value = read_text(path, *args, **kwargs)
            return value.replace('description MANAGEMENT', 'description CHANGED') if path == ROOT / 'samples' / 'cisco.txt' else value
        with patch.object(Path, 'read_text', changed_read):
            third = main.run(devices, self.path, demo=True)
        self.assertEqual(third['changed'], 1)
        self.assertEqual(third['devices'][1]['Git Status'], 'COMMITTED')
        for path in self.path.rglob('*.cfg'):
            self.assertNotIn('DEMO_ONLY_', path.read_text())

    def test_partial_failure_keeps_other_device_and_report(self):
        devices = [self.device, {**self.device, 'name': 'R1'}]
        source = self.path / 'R1_001.cfg'
        source.write_text('hostname R1\n')
        results = [{'name': 'J1', 'host': '192.168.36.13', 'status': 'failed', 'error': 'TimeoutError'},
                   {'name': 'R1', 'status': 'success', 'file': str(source)}]
        with patch.object(main, 'backup_all', return_value=results):
            report = main.run(devices, self.path, demo=True)
        self.assertEqual(report['status'], 'FAILED')
        self.assertEqual(report['failed'], 1)
        self.assertEqual(report['success'], 1)
        self.assertEqual(report['devices'][1]['Git Status'], 'COMMITTED')
        self.assertEqual(len(report['devices']), 2)

    def test_git_sanitizes_and_excludes_unrelated_staging(self):
        manager = GitManager(self.path / 'history')
        unrelated = manager.repo_dir / 'unrelated.txt'
        unrelated.write_text('do not commit')
        manager._git('add', '--', unrelated.name)
        source = self.path / 'raw.cfg'
        source.write_text('hostname R1\nenable secret 5 PRIVATE_HASH\n')
        manager.save_config('R1', source)
        self.assertNotIn('PRIVATE_HASH', (manager.repo_dir / 'R1.cfg').read_text())
        self.assertNotIn('unrelated.txt', manager._git('show', '--format=', '--name-only', 'HEAD'))

    def test_git_retries_snapshot_after_commit_failure(self):
        manager = GitManager(self.path / 'history')
        source = self.path / 'raw.cfg'
        source.write_text('hostname R1\n')
        original = manager._git
        def fail_commit(*args):
            if args[0] == 'commit':
                raise RuntimeError('temporary failure')
            return original(*args)
        with patch.object(manager, '_git', side_effect=fail_commit):
            with self.assertRaises(RuntimeError):
                manager.save_config('R1', source)
        self.assertEqual(manager.save_config('R1', source)['status'], 'COMMITTED')

    def test_daily_schedule_timezone_and_overlap_policy(self):
        with patch.dict(os.environ, {'BACKUP_TIMEZONE': 'Asia/Ho_Chi_Minh', 'BACKUP_HOUR': '2', 'BACKUP_MINUTE': '0'}), patch.object(scheduler, 'BlockingScheduler') as engine:
            scheduler.main(['--demo'])
        call = engine.return_value.add_job.call_args
        self.assertEqual(str(call.args[1].timezone), 'Asia/Ho_Chi_Minh')
        self.assertEqual(call.kwargs['max_instances'], 1)
        self.assertTrue(call.kwargs['coalesce'])
        self.assertTrue(call.kwargs['kwargs']['demo'])

    def test_timestamp_order_ignores_mtime_and_other_names(self):
        (self.path / 'R1_001.cfg').write_text('hostname old\n')
        (self.path / 'R1_002.cfg').write_text('hostname new\n')
        (self.path / 'R1_OTHER_003.cfg').write_text('hostname unrelated\n')
        os.utime(self.path / 'R1_001.cfg', (2000000000, 2000000000))
        result = detect_changes('R1', self.path)
        self.assertTrue(result['latest'].endswith('R1_002.cfg'))
        with self.assertRaises(ValueError):
            detect_changes('../R1', self.path)


if __name__ == '__main__':
    unittest.main()
