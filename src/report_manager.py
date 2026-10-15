
import csv
from datetime import datetime
from pathlib import Path


def export_csv_report(records, report_dir="reports"):
    """Xuất báo cáo tổng hợp backup, thay đổi và Git."""

    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    csv_file = report_path / f"network_report_{timestamp}.csv"

    fieldnames = [
        "Device",
        "IP",
        "Backup Status",
        "Change Status",
        "Git Status",
        "Commit",
        "Error"
    ]

    with csv_file.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(records)

    return csv_file
