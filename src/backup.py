
from netmiko import ConnectHandler
from getpass import getpass
from pathlib import Path
from datetime import datetime

from inventory import load_inventory

# Danh sách thiết bị cần backup
devices = load_inventory()

# Thư mục lưu file backup
backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)

username = "backupuser"
password = getpass("Nhập mật khẩu SSH Cisco: ")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

for device in devices:
    print(f"\nĐang backup {device['name']}...")

    try:
        connection_info = {
            "device_type": device["device_type"],
            "host": device["host"],
            "username": username,
            "password": password,
            "port": 22,
            "conn_timeout": 15,
            "auth_timeout": 20,
            "banner_timeout": 20,
        }

        with ConnectHandler(**connection_info) as ssh:
            ssh.disable_paging()

            config = ssh.send_command(
                "show running-config",
                read_timeout=90
            )

            if not config.strip():
                raise ValueError("Cấu hình trả về rỗng")

            filename = (
                f"{device['name']}_{timestamp}.cfg"
            )

            filepath = backup_dir / filename

            filepath.write_text(
                config,
                encoding="utf-8"
            )

            print(f"Backup thành công: {filepath}")

    except Exception as error:
        print(f"Backup thất bại: {device['name']}")
        print(f"Lỗi: {error}")

print("\nHoàn thành quá trình backup!")
