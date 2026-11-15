"""Backup -> sanitized snapshots -> diff -> Git -> per-device reports."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid
import json

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inventory import load_inventory, display_inventory
from src.ssh_connector import get_credentials
from src.backup_manager import backup_all
from src.change_detector import detect_changes
from src.git_manager import GitManager
from src.report_manager import export_csv_report, write_json
from src.runtime import ROOT, load_environment, run_lock, AlreadyRunning


def run(devices, output_root, demo=False):
    """Return a report; partial backup/Git failure is a failed run."""
    started = datetime.now(timezone.utc).isoformat()
    username, password = ("demo", "") if demo else get_credentials()
    results = backup_all(devices, username, password, backup_dir=output_root / "backups", demo=demo)
    records = []
    try:
        git = GitManager(output_root / "config_history")
    except Exception:
        git = None
    for result in results:
        record = {
            "Device": result["name"], "IP": result.get("host", ""),
            "Platform": next(d["device_type"] for d in devices if d["name"] == result["name"]),
            "Backup Status": result["status"].upper(), "Change Status": "SKIPPED",
            "Git Status": "SKIPPED", "Commit": "", "Error": result.get("error") or "",
            "Diff": "", "Redacted": result.get("redacted_count", 0),
            "Warnings": result.get("warnings", 0),
        }
        if result["status"] == "success":
            try:
                change = detect_changes(result["name"], output_root / "backups")
                record.update({"Change Status": change["status"], "Diff": change.get("diff", "")})
            except Exception as error:
                record.update({"Change Status": "ERROR", "Error": type(error).__name__})
            try:
                if git is None:
                    raise RuntimeError("Git unavailable")
                saved = git.save_config(result["name"], result["file"])
                record.update({"Git Status": saved["status"], "Commit": saved.get("commit") or ""})
            except Exception as error:
                record.update({"Git Status": "ERROR", "Error": type(error).__name__})
        records.append(record)
    success = sum(r["Backup Status"] == "SUCCESS" for r in records)
    report = {
        "run_id": uuid.uuid4().hex, "mode": "demo" if demo else "live",
        "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS" if all(r["Backup Status"] == "SUCCESS" and not r["Error"] for r in records) else "FAILED",
        "total": len(records), "success": success, "failed": len(records) - success,
        "changed": sum(r["Change Status"] == "CHANGED" for r in records), "devices": records,
    }
    reports = output_root / "reports"
    export_csv_report(records, reports)
    write_json(reports / ("run_" + report["run_id"] + ".json"), report)
    write_json(reports / "latest.json", report)
    logs = output_root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "backup.log").open("a", encoding="utf-8") as log:
        log.write(json.dumps(report, ensure_ascii=False) + "\n")
    for record in records:
        print(f"{record['Device']}: {record['Backup Status']} | {record['Change Status']} | Git {record['Git Status']}")
    print(f"{report['status']}: {success}/{len(records)} | {reports / 'latest.json'}")
    return report


def execute_once(args, output_root):
    """Publish even startup failures while still holding the run lock."""
    try:
        path = args.inventory or ROOT / "config" / ("devices.demo.yaml" if args.demo else "devices.yaml")
        devices = load_inventory(path)
        display_inventory(devices)
        report = run(devices, output_root, args.demo)
        return 0 if report["status"] == "SUCCESS" else 1
    except Exception as error:
        report = {"status": "FAILED", "error_type": type(error).__name__,
                  "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                  "mode": "demo" if args.demo else "live", "devices": []}
        write_json(output_root / "reports" / "latest.json", report)
        print(f"FAILED: {type(error).__name__}. Check inventory, credentials, allowlist and trusted host keys.")
        return 1


def main(argv=None):
    load_environment()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Offline samples, separate demo/ data")
    parser.add_argument("--inventory", type=Path, help="Alternative inventory YAML")
    args = parser.parse_args(argv)
    output_root = ROOT / "demo" if args.demo else ROOT
    try:
        with run_lock(output_root):
            return execute_once(args, output_root)
    except AlreadyRunning:
        print("SKIPPED: another backup is running")
        return 2
    except Exception as error:
        print(f"FAILED: {type(error).__name__} while accessing the backup directory.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
