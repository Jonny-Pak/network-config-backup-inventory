# Network Backup & Inventory — GNS3 Lab

This is a read-only SSH backup baseline for authorized lab devices. Supported Netmiko platform types: `cisco_ios`, `juniper_junos`.

## Ubuntu setup

```bash
sudo apt update && sudo apt install -y python3-venv git
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env locally, never commit it
# edit devices.yaml to match your actual management topology
git init
git config user.name "Network Lab"
git config user.email "lab@example.invalid"
python backup.py --demo
python backup.py       # after SSH reachability & credentials are ready
```

On Windows PowerShell, use `py -m venv .venv`, `.venv\Scripts\Activate.ps1`, then the same pip and Python commands. Copy `.env.example` to `.env` manually or use `Copy-Item`.

## View results

- `configs/R1-CISCO.cfg`: latest sanitized snapshot
- `diffs/R1-CISCO.diff`: diff between last and current run (only rewritten when changed)
- `reports/report_*.json` and `.csv`: per-run status, ignored by Git
- `git log --oneline` / `git show HEAD` / `git diff HEAD~1 HEAD -- configs/`

## Demo diff

1. Run `python backup.py --demo`.
2. Edit `samples/cisco.txt` and add `description DEMO-CHANGE` under an interface.
3. Re-run `python backup.py --demo`.
4. Inspect `diffs/R1-CISCO.diff` and `git log --oneline`.

## Scheduling (Ubuntu)

Use `crontab -e` to set a daily task (replace `<PROJECT_PATH>` with an absolute path):

```cron
0 2 * * * cd <PROJECT_PATH> && <PROJECT_PATH>/.venv/bin/python <PROJECT_PATH>/backup.py >> <PROJECT_PATH>/backup.log 2>&1
```

## Security / limitations

- Run against your own or authorized devices only; never commit `.env`.
- The sample redaction is intentionally basic, may miss vendor-specific credentials or keys. Audit it before using real configurations or pushing to remote Git. Keep Git repository private and filesystem access restricted. Historic Git commits retain information unless history is rewritten; avoid pushing raw configuration snapshots.
- This is a starter, not a complete CMDB. `version` is recorded in the per-run report (first three lines of `show version`), not permanently in a database.
- `diffs/` tracks only the most recent changed comparison for each device. Git keeps earlier versions.
- No automatic SSH host key pinning implemented; use only within isolated, trusted lab networks. Harden host key verification for production.
- The sample cisco.txt is used for both Cisco devices and is synthetic; no real device has been contacted by --demo.
