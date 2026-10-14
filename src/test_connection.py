
from netmiko import ConnectHandler
from getpass import getpass

# Thông tin router Cisco R1
router = {
    "device_type": "cisco_ios",
    "host": "192.168.36.11",
    "username": "backupuser",
    "password": getpass("Nhập mật khẩu SSH Cisco R1: "),
    "port": 22,
    "conn_timeout": 15,
    "auth_timeout": 20,
    "banner_timeout": 20,
}

try:
    print("Đang kết nối SSH đến R1-CISCO...")

    with ConnectHandler(**router) as connection:
        print("Đăng nhập SSH thành công!")

        hostname = connection.find_prompt()
        print("Hostname:", hostname)

        version = connection.send_command(
            "show version",
            read_timeout=60
        )

        print("\n===== SHOW VERSION =====")
        print(version)

except Exception as error:
    print("\nKết nối thất bại!")
    print(type(error).__name__, ":", error)
