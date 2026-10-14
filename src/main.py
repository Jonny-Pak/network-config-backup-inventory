
import logging

from inventory import load_inventory, display_inventory
from ssh_connector import get_credentials
from backup_manager import backup_all
from logger_config import setup_logging


def main():
    logger = setup_logging()

    try:
        # Bước 1: Đọc và hiển thị danh sách thiết bị
        devices = load_inventory()
        display_inventory(devices)

        # Bước 2: Lấy thông tin đăng nhập SSH
        username, password = get_credentials()

        # Bước 3: Thực hiện backup nhiều thiết bị
        print("\n===== START NETWORK BACKUP =====")
        logger.info("Bắt đầu sao lưu %d thiết bị", len(devices))

        results = backup_all(
            devices,
            username,
            password,
            max_workers=3
        )

        # Bước 4: Ghi log kết quả từng thiết bị
        for result in results:
            if result["status"] == "success":
                logger.info(
                    "BACKUP SUCCESS | %s",
                    result["name"]
                )
            else:
                logger.error(
                    "BACKUP FAILED | %s | %s",
                    result["name"],
                    result["error"]
                )

        # Bước 5: Thống kê kết quả
        success = sum(
            result["status"] == "success"
            for result in results
        )

        failed = len(devices) - success

        print("\n===== BACKUP REPORT =====")

        for result in results:
            print(
                f"{result['name']}: "
                f"{result['status'].upper()}"
            )

        print(f"\nTổng thiết bị: {len(devices)}")
        print(f"Thành công: {success}")
        print(f"Thất bại: {failed}")

        logger.info(
            "Hoàn thành backup: %d/%d thiết bị thành công",
            success,
            len(devices)
        )

        # Trả về mã lỗi nếu có thiết bị backup thất bại
        if failed > 0:
            raise SystemExit(1)

    except (FileNotFoundError, ValueError) as error:
        logger.error("Lỗi chương trình: %s", error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
