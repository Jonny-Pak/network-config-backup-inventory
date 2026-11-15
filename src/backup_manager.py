
from datetime import datetime
from pathlib import Path

try:
    from .ssh_connector import ssh_connection
    from .secret_filter import redact_config
except ImportError:
    from ssh_connector import ssh_connection
    from secret_filter import redact_config
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"


COMMANDS = {
    "cisco_ios": "show running-config",
    "juniper_junos": "show configuration | display set | no-more",
}


def prepare_config(config):
    """Sanitize before any disk write and remove volatile IOS headers."""
    lines = [line.rstrip() for line in config.splitlines()
             if not re.match(r"^\s*(Building configuration|Current configuration\s*:|! Last configuration change|! NVRAM config last updated)", line)]
    return redact_config("\n".join(lines))


def backup_device(device, username, password, backup_dir=None, demo=False):
    """Backup cấu hình một thiết bị qua SSH."""
    name = device["name"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    result = {
        "name": name,
        "host": device["host"],
        "status": "failed",
        "file": None,
        "error": None,
    }

    try:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise ValueError("Tên thiết bị không hợp lệ")
        command = COMMANDS[device["device_type"]]
        if demo:
            sample = "junos.txt" if device["device_type"] == "juniper_junos" else "cisco.txt"
            config = (BASE_DIR / "samples" / sample).read_text(encoding="utf-8")
        else:
            with ssh_connection(device, username, password) as ssh:
                ssh.disable_paging()
                config = ssh.send_command(command, read_timeout=90)

        if not config.strip():
            raise ValueError("Cấu hình trả về rỗng")

        if config.lstrip().startswith(("%", "error:", "syntax error")):
            raise ValueError(
                "Thiết bị trả về thông báo lỗi thay vì cấu hình"
            )

        config, count, warnings = prepare_config(config)
        destination = Path(backup_dir) if backup_dir is not None else BACKUP_DIR
        destination.mkdir(parents=True, exist_ok=True)
        filename = f"{name}_{timestamp}.cfg"
        filepath = destination / filename

        filepath.write_text(config, encoding="utf-8")

        result["status"] = "success"
        result["file"] = str(filepath)
        result.update(redacted_count=count, warnings=warnings)

    except Exception as error:
        # Third-party exceptions can echo passwords or raw configuration.
        result["error"] = type(error).__name__

    return result



def backup_all(devices, username, password, max_workers=3, backup_dir=None, demo=False):
    """Backup nhiều thiết bị song song bằng ThreadPoolExecutor."""

    if not devices:
        return []

    results = [None] * len(devices)

    worker_count = min(max_workers, len(devices))
    if worker_count < 1:
        raise ValueError("max_workers must be positive")
    options = {} if backup_dir is None and not demo else {"backup_dir": backup_dir, "demo": demo}

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_index = {
            executor.submit(
                backup_device,
                device,
                username,
                password,
                **options
            ): index
            for index, device in enumerate(devices)
        }

        for future in as_completed(future_to_index):
            index = future_to_index[future]

            try:
                results[index] = future.result()
            except Exception as error:
                device = devices[index]
                logging.error(
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

