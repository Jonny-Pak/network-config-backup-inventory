
from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.inventory import load_inventory
from src.ssh_connector import get_credentials, execute_command
from src.runtime import load_environment


def main():
    load_environment()
    devices = load_inventory()
    username, password = get_credentials()

    success = 0

    for device in devices:
        name = device["name"]
        print(f"\nĐang kết nối {name} ({device['host']})...")

        try:
            output = execute_command(
                device,
                username,
                password,
                "show version"
            )

            print(f"[OK] {name}: SSH thành công")
            print("\n".join(output.splitlines()[:4]))
            success += 1

        except Exception as error:
            print(f"[FAILED] {name}: {type(error).__name__}")

    print(f"\nKết quả: {success}/{len(devices)} thiết bị thành công")


if __name__ == "__main__":
    main()
