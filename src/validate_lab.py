"""Read-only SSH lab validation. Isolated evidence; no router configuration changes."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import sys

from .inventory import load_inventory
from .main import run
from .runtime import ROOT, load_environment, run_lock
from .report_manager import write_json
from .security import validate_target


def validate(devices, destination, failure_port):
    if len(devices) < 2:
        raise ValueError('At least two devices required')
    broken = devices[-1]
    validate_target(broken['host'])
    if failure_port == broken['port']:
        raise ValueError('Failure-test port must differ from actual SSH port')
    # Do not send credentials if the proposed failure endpoint is accepting TCP.
    try:
        with socket.create_connection((broken['host'], failure_port), timeout=2):
            raise ValueError('Failure-test port is open; choose a closed port')
    except (ConnectionRefusedError, socket.timeout):
        pass
    baseline = run(devices, destination)
    if baseline['status'] != 'SUCCESS':
        raise RuntimeError('Baseline backup failed; do not interpret fault test')
    repeated = run(devices, destination)
    faulty_inventory = [dict(device) for device in devices]
    faulty_inventory[-1]['port'] = failure_port
    failure = run(faulty_inventory, destination)
    unaffected = failure['devices'][:-1]
    checks = {
        'baseline_ssh': baseline['status'] == 'SUCCESS',
        'unchanged_no_extra_commit': repeated['status'] == 'SUCCESS' and all(
            r['Change Status'] == 'UNCHANGED' and r['Git Status'] == 'UNCHANGED' for r in repeated['devices']),
        'unreachable_endpoint_is_failed': failure['status'] == 'FAILED' and failure['devices'][-1]['Backup Status'] == 'FAILED',
        'other_routers_continue': all(r['Backup Status'] == 'SUCCESS' and not r['Error'] for r in unaffected),
        'failed_device_git_skipped': failure['devices'][-1]['Git Status'] == 'SKIPPED',
    }
    # Check only newly written test copies; never print a credential or its value.
    import os
    values = [os.getenv(k) for k in ('NET_PASSWORD', 'NET_SECRET') if os.getenv(k)]
    copies = list((destination / 'backups').glob('*.cfg')) + list((destination / 'config_history').glob('*.cfg'))
    checks['login_secrets_absent_from_test_copies'] = all(
        all(value not in file.read_text(encoding='utf-8') for value in values) for file in copies)
    summary = {
        'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks,
        'fault_method': 'Closed TCP port on the last router; router itself remains running',
        'fault_device': broken['name'], 'fault_port': failure_port,
        'baseline_run': baseline['run_id'], 'repeat_run': repeated['run_id'],
        'fault_run': failure['run_id'],
        'limitations': ['Not a physical power-off test', 'No authentication failure or Juniper test',
                        'Secret absence check covers configured login secrets, not every possible configuration secret'],
    }
    write_json(destination / 'summary.json', summary)
    lines = ['# Lab validation results', '', f"Status: {summary['status']}",
             f"Completed (UTC): {summary['finished_at_utc']}", '',
             '| Check | Result |', '| --- | --- |']
    lines.extend(f"| {name} | {'PASS' if passed else 'FAIL'} |" for name, passed in checks.items())
    lines.extend(['', 'Fault injection: closed TCP port on the last router, without stopping or reconfiguring it.',
                  'Evidence is separate from the normal dashboard reports and configuration history.',
                  'Still requires: physical power-off, authentication failure, Juniper and long-running daily schedule checks.'])
    (destination / 'RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return summary


def main(argv=None):
    load_environment()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--failure-port', type=int, default=65022)
    args = parser.parse_args(argv)
    if not 1 <= args.failure_port <= 65535:
        parser.error('Port must be 1..65535')
    destination = ROOT / 'validation' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    try:
        # Also exclude concurrent normal backups while reading the lab.
        with run_lock(ROOT):
            summary = validate(load_inventory(), destination, args.failure_port)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(f'Evidence: {destination / "RESULTS.md"}')
        return 0 if summary['status'] == 'PASS' else 1
    except Exception as error:
        print(f'Validation stopped: {type(error).__name__}. Check lab availability and configuration.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
