
import ipaddress
import re
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INVENTORY = BASE_DIR / "config" / "devices.yaml"

SUPPORTED_TYPES = {"cisco_ios", "juniper_junos"}


def load_inventory(file_path=DEFAULT_INVENTORY):
    """Đọc và kiểm tra danh sách thiết bị từ file YAML."""

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Không tìm thấy file Inventory: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("Inventory phải có dạng YAML object.")

    devices = data.get("devices")

    if not isinstance(devices, list) or not devices:
        raise ValueError("Danh sách devices phải là list không rỗng.")

    validated = []
    used_names = set()
    used_endpoints = set()

    for index, device in enumerate(devices, start=1):
        if not isinstance(device, dict):
            raise ValueError(
                f"Thiết bị thứ {index} phải là YAML object."
            )

        name = device.get("name")
        host = device.get("host")
        device_type = device.get("device_type")
        port = device.get("port", 22)

        if not isinstance(name, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]+", name
        ):
            raise ValueError(
                f"Thiết bị {index}: name không hợp lệ."
            )

        if name in used_names:
            raise ValueError(f"Trùng tên thiết bị: {name}")

        if not isinstance(host, str):
            raise ValueError(f"{name}: host phải là chuỗi IP.")

        try:
            ipaddress.ip_address(host)
        except ValueError as exc:
            raise ValueError(
                f"{name}: IP không hợp lệ: {host}"
            ) from exc

        if device_type not in SUPPORTED_TYPES:
            raise ValueError(
                f"{name}: device_type không hỗ trợ: {device_type}"
            )

        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError(f"{name}: port không hợp lệ.")

        endpoint = (host, port)

        if endpoint in used_endpoints:
            raise ValueError(
                f"Trùng IP và cổng SSH: {host}:{port}"
            )

        used_names.add(name)
        used_endpoints.add(endpoint)

        validated.append({
            **device,
            "name": name,
            "host": host,
            "device_type": device_type,
            "port": port,
        })

    return validated


def display_inventory(devices):
    """Hiển thị danh sách thiết bị mạng."""

    print("\n===== NETWORK DEVICE INVENTORY =====")
    print(f"Tổng số thiết bị: {len(devices)}\n")

    print(
        f"{'NAME':<16}"
        f"{'IP ADDRESS':<20}"
        f"{'TYPE':<18}"
        f"{'PORT':<8}"
    )

    print("-" * 62)

    for device in devices:
        print(
            f"{device['name']:<16}"
            f"{device['host']:<20}"
            f"{device['device_type']:<18}"
            f"{device['port']:<8}"
        )


if __name__ == "__main__":
    try:
        devices = load_inventory()
        display_inventory(devices)
        print("\nInventory hợp lệ!")
    except (FileNotFoundError, ValueError, yaml.YAMLError) as error:
        print(f"\nLỗi Inventory: {error}")
        raise SystemExit(1)
