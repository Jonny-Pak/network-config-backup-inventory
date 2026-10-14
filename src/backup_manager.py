
from datetime import datetime
from pathlib import Path

from ssh_connector import ssh_connection
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"


def backup_device(device, username, password):
    """Backup cấu hình một thiết bị qua SSH."""
    name = device["name"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = {
        "name": name,
        "host": device["host"],
        "status": "failed",
        "file": None,
        "error": None,
    }

    try:
        print(f"Đang backup {name}...")

        with ssh_connection(device, username, password) as ssh:
            ssh.disable_paging()

            config = ssh.send_command(
                "show running-config",
                read_timeout=90,
            )

        if not config.strip():
            raise ValueError("Cấu hình trả về rỗng")

        if config.lstrip().startswith("%"):
            raise ValueError(
                "Thiết bị trả về thông báo lỗi thay vì cấu hình"
            )

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{name}_{timestamp}.cfg"
        filepath = BACKUP_DIR / filename

        filepath.write_text(config, encoding="utf-8")

        result["status"] = "success"
        result["file"] = str(filepath)

        print(f"[OK] {name}: {filepath}")

    except Exception as error:
        result["error"] = str(error)
        print(f"[FAILED] {name}: {error}")

    return result



def backup_all(devices, username, password, max_workers=3):
    """Backup nhiều thiết bị song song bằng ThreadPoolExecutor."""

    if not devices:
        return []

    results = [None] * len(devices)

    worker_count = min(max_workers, len(devices))

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_index = {
            executor.submit(
                backup_device,
                device,
                username,
                password
            ): index
            for index, device in enumerate(devices)
        }

        for future in as_completed(future_to_index):
            index = future_to_index[future]

            try:
                results[index] = future.result()
            except Exception as error:
                device = devices[index]
                logging.exception(
                    "Lỗi khi backup thiết bị %s",
                    device["name"]
                )

                results[index] = {
                    "name": device["name"],
                    "host": device["host"],
                    "status": "failed",
                    "file": None,
                    "error": type(error).__name__,
                }

    return results

