
from inventory import load_inventory
from ssh_connector import get_credentials, execute_command


def main():
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
            print(f"[FAILED] {name}: {error}")

    print(f"\nKết quả: {success}/{len(devices)} thiết bị thành công")


if __name__ == "__main__":
    main()
