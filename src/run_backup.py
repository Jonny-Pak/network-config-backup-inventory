"""Launch existing src.main, write sanitized *job* summary for Streamlit."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import subprocess
import sys
from .runtime import load_environment
from .report_manager import write_json

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'


def execute(demo=False, credentials=None):
    load_environment()
    reports = ROOT / 'demo' / 'reports' if demo else REPORTS
    reports.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc)
    timeout = int(os.getenv('BACKUP_TIMEOUT_SECONDS', '600'))
    if timeout <= 0:
        raise ValueError('BACKUP_TIMEOUT_SECONDS must be positive')
    # No stdout/stderr persistence: existing application might print credentials.
    try:
        command = [sys.executable, '-X', 'utf8', '-m', 'src.main']
        child_env = os.environ.copy()
        if demo:
            command.append('--demo')
        if credentials is not None:
            username, password, secret = credentials
            child_env['NET_USERNAME'] = username
            child_env['NET_PASSWORD'] = password
            child_env['NET_SECRET'] = secret
        proc = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=timeout, env=child_env)
        code = proc.returncode
        status = 'SUCCESS' if code == 0 else 'SKIPPED' if code == 2 else 'FAILED'
        error_type = None if code == 0 else 'ALREADY_RUNNING' if code == 2 else 'NONZERO_EXIT'
    except subprocess.TimeoutExpired:
        code, status, error_type = None, 'FAILED', 'TIMEOUT'
    except Exception:
        code, status, error_type = None, 'FAILED', 'STARTUP_ERROR'
    report = {'started_at_utc': start.isoformat(), 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
              'status': status, 'returncode': code, 'error_type': error_type,
              'mode': 'demo' if demo else 'live'}
    write_json(reports / 'scheduler_status.json', report)
    return report


if __name__ == '__main__':
    result = execute()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'SUCCESS' else 1)
