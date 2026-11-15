
from pathlib import Path
import re

try:
    from .config_diff import compare_configs
except ImportError:
    from config_diff import compare_configs


def detect_changes(device_name, backup_dir="backups"):
    """So sánh hai bản backup mới nhất của một thiết bị."""

    backup_path = Path(backup_dir)
    if not isinstance(device_name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", device_name):
        raise ValueError("Tên thiết bị không hợp lệ")

    # Lấy danh sách backup của thiết bị
    files = sorted(
        (p for p in backup_path.glob(f"{device_name}_*.cfg")
         if re.fullmatch(re.escape(device_name) + r"_\d+(?:_\d+)*\.cfg", p.name)),
        key=lambda file: file.name,
        reverse=True
    )

    if len(files) == 0:
        return {
            "device": device_name,
            "status": "NO_BACKUP",
            "diff": ""
        }

    if len(files) == 1:
        return {
            "device": device_name,
            "status": "FIRST_BACKUP",
            "diff": ""
        }

    newest = files[0]
    previous = files[1]

    diff = compare_configs(previous, newest)

    return {
        "device": device_name,
        "status": "CHANGED" if diff else "UNCHANGED",
        "previous": str(previous),
        "latest": str(newest),
        "diff": diff
    }
