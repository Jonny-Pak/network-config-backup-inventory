import unittest
from unittest.mock import patch
from src import scheduler, validate_lab


class ScheduledProbeTests(unittest.TestCase):
    def test_date_trigger_executes_only_after_scheduler_starts(self):
        with patch.object(scheduler, 'BlockingScheduler') as factory, \
                patch.object(scheduler, 'execute', return_value={'status': 'SUCCESS'}) as execute, \
                patch.object(scheduler, 'write_json') as save:
            engine = factory.return_value
            def start():
                execute.assert_not_called()
                engine.add_job.call_args.args[0]()
            engine.start.side_effect = start
            self.assertEqual(scheduler.scheduled_test(5, demo=True), 0)
            execute.assert_called_once_with(demo=True)
            self.assertEqual(save.call_args.args[1]['trigger'], 'date')
            self.assertEqual(str(engine.add_job.call_args.args[1].run_date.tzinfo), 'UTC')
            engine.shutdown.assert_called_once_with(wait=False)

    def test_scheduled_failure_exits_nonzero(self):
        with patch.object(scheduler, 'BlockingScheduler') as factory, \
                patch.object(scheduler, 'execute', return_value={'status': 'FAILED'}), \
                patch.object(scheduler, 'write_json'):
            engine = factory.return_value
            engine.start.side_effect = lambda: engine.add_job.call_args.args[0]()
            self.assertEqual(scheduler.scheduled_test(5), 1)

    def test_rejects_invalid_or_conflicting_probe_options(self):
        for arguments in (['--test-after', '0'], ['--test-after', '3601'], ['--test-after', '5', '--once']):
            with self.subTest(arguments=arguments), self.assertRaises(SystemExit) as error:
                scheduler.main(arguments)
            self.assertEqual(error.exception.code, 2)

    def test_fault_probe_refuses_open_port_before_login(self):
        devices = [{'name': 'R1', 'host': '192.168.36.11', 'port': 22},
                   {'name': 'R2', 'host': '192.168.36.12', 'port': 22}]
        with patch.object(validate_lab, 'validate_target'), \
                patch.object(validate_lab.socket, 'create_connection'), \
                patch.object(validate_lab, 'run') as backup:
            with self.assertRaises(ValueError):
                validate_lab.validate(devices, None, 65022)
            backup.assert_not_called()
