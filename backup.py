"""Read-only network configuration backup with per-device diffs and Git history."""
import argparse
import concurrent.futures
import csv
import datetime as dt
import difflib
import json
import os
import re
import subprocess
from pathlib import Path

import yaml
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
CONFIGS = BASE / 'configs'
DIFFS = BASE / 'diffs'
REPORTS = BASE / 'reports'
COMMANDS = {
    'cisco_ios': ('show running-config', 'show version'),
    'juniper_junos': ('show configuration | display set | no-more', 'show version | no-more'),
}
# Conservative baseline; expand for your device and compliance requirements.
SECRET_LINE = re.compile(
    r'(?i)(^|\s)(username\s+\S+\s+(?:password|secret)\b|'
    r'enable\s+(?:password|secret)\b|snmp-server\s+community\b|'
    r'(?:password|pre-shared-key|secret|authentication-key|private-key)\s+\S+|'
    r'set\s+system\s+login\s+user\s+\S+\s+authentication\b)'
)


def run_git(*args, check=True):
    return subprocess.run(['git', '-C', str(BASE), *args], capture_output=True,
                          text=True, check=check)


def sanitize(content):
    lines = []
    for line in content.splitlines():
        if SECRET_LINE.search(line):
            lines.append('! [REDACTED SENSITIVE LINE]')
        else:
            lines.append(line.rstrip())
    return '\n'.join(lines).strip() + '\n'


def load_devices():
    data = yaml.safe_load((BASE / 'devices.yaml').read_text(encoding='utf-8'))
    devices = data.get('devices', [])
    if not isinstance(devices, list) or not devices:
        raise ValueError('devices.yaml must have a nonempty devices list')
    names = set()
    for dev in devices:
        name = dev.get('name', '')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name) or name in names:
            raise ValueError(f'Invalid/duplicate name: {name}')
        if dev.get('device_type') not in COMMANDS:
            raise ValueError(f'Unsupported device type: {dev.get("device_type")}')
        if not dev.get('host'):
            raise ValueError(f'Missing host for {name}')
        names.add(name)
    return devices


def collect(device, demo=False):
    platform = device['device_type']
    if demo:
        filename = 'junos.txt' if platform == 'juniper_junos' else 'cisco.txt'
        return (BASE / 'samples' / filename).read_text(encoding='utf-8'), 'DEMO sample'
    from netmiko import ConnectHandler
    params = dict(device_type=platform, host=device['host'],
                  port=device.get('port', 22), username=os.environ['NET_USERNAME'],
                  password=os.environ['NET_PASSWORD'], conn_timeout=12,
                  auth_timeout=12, banner_timeout=12)
    if platform == 'cisco_ios' and os.getenv('NET_SECRET'):
        params['secret'] = os.environ['NET_SECRET']
    with ConnectHandler(**params) as ssh:
        if platform == 'cisco_ios' and os.getenv('NET_SECRET'):
            ssh.enable()
        commands = COMMANDS[platform]
        cfg = ssh.send_command(commands[0], read_timeout=90)
        version = ssh.send_command(commands[1], read_timeout=45)
    return cfg, version


def handle(device, demo=False):
    name = device['name']
    row = dict(name=name, host=device['host'], platform=device['device_type'],
               status='FAILED', changed=False, error='', version='')
    try:
        raw, version = collect(device, demo)
        if not raw.strip() or re.search(r'(?im)^\s*(%\s*invalid|error:|syntax error)', raw):
            raise ValueError('Empty or error response to configuration command')
        content = sanitize(raw)
        path = CONFIGS / (name + '.cfg')
        old = path.read_text(encoding='utf-8') if path.exists() else ''
        row['changed'] = content != old
        if row['changed']:
            path.write_text(content, encoding='utf-8')
            diff = ''.join(difflib.unified_diff(old.splitlines(keepends=True),
                content.splitlines(keepends=True), fromfile=f'{name}/previous',
                tofile=f'{name}/current'))
            (DIFFS / (name + '.diff')).write_text(diff, encoding='utf-8')
        row['version'] = ' | '.join(version.splitlines()[:3])[:300]
        row['status'] = 'OK'
    except Exception as exc:
        row['error'] = f'{type(exc).__name__}: {exc}'[:350]
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='use offline sample data')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--no-git', action='store_true')
    args = parser.parse_args()
    load_dotenv(BASE / '.env')
    devices = load_devices()
    if not args.demo and not (os.getenv('NET_USERNAME') and os.getenv('NET_PASSWORD')):
        parser.error('Set NET_USERNAME and NET_PASSWORD in .env before live backup')
    for folder in (CONFIGS, DIFFS, REPORTS):
        folder.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 16))) as pool:
        rows = list(pool.map(lambda d: handle(d, args.demo), devices))
    stamp = dt.datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')
    report = dict(time=dt.datetime.now().astimezone().isoformat(), demo=args.demo,
                  total=len(rows), successful=sum(x['status']=='OK' for x in rows), devices=rows)
    (REPORTS / f'report_{stamp}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    with (REPORTS / f'report_{stamp}.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    if not args.no_git and any(x['changed'] for x in rows):
        try:
            run_git('rev-parse', '--is-inside-work-tree')
            run_git('add', '--', 'configs', 'diffs')
            status = run_git('diff', '--cached', '--quiet', check=False)
            if status.returncode == 1:
                run_git('commit', '-m', 'Backup configuration ' + stamp)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            print(f'Git warning: {exc}. Run git init and set author details.')
    for row in rows:
        print(f"{row['name']}: {row['status']} changed={row['changed']} {row['error']}")
    print(f"SUCCESS {report['successful']}/{report['total']}; report: {stamp}")
    if report['successful'] != report['total']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
