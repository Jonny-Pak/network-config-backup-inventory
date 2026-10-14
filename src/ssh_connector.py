
import os
from contextlib import contextmanager
from getpass import getpass

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)


def get_credentials():
    """Lấy thông tin SSH, không lưu mật khẩu trong source code."""
    username = os.getenv("NET_USERNAME") or input(
        "SSH username [backupuser]: "
    ).strip() or "backupuser"

    password = os.getenv("NET_PASSWORD")
    if password is None:
        password = getpass("Nhập mật khẩu SSH: ")

    if not password:
        raise ValueError("Mật khẩu SSH không được để trống.")

    return username, password


@contextmanager
def ssh_connection(device, username, password):
    """Kết nối SSH và tự đóng phiên khi hoàn thành."""
    connection_info = {
        "device_type": device["device_type"],
        "host": device["host"],
        "port": device.get("port", 22),
        "username": username,
        "password": password,
        "conn_timeout": 15,
        "auth_timeout": 20,
        "banner_timeout": 20,
    }

    try:
        with ConnectHandler(**connection_info) as connection:
            yield connection
    except NetmikoAuthenticationException as error:
        raise RuntimeError(
            f"{device['name']}: Sai tài khoản hoặc mật khẩu SSH"
        ) from error
    except NetmikoTimeoutException as error:
        raise RuntimeError(
            f"{device['name']}: Không kết nối được hoặc SSH timeout"
        ) from error


def execute_command(device, username, password, command):
    """Kết nối đến thiết bị, thực thi lệnh và trả về kết quả."""
    with ssh_connection(device, username, password) as connection:
        return connection.send_command(command, read_timeout=90)
