
from pathlib import Path

from inventory import load_inventory, display_inventory
from ssh_connector import get_credentials
from backup_manager import backup_all
from logger_config import setup_logging
from change_detector import detect_changes
from git_manager import GitManager
from report_manager import export_csv_report


# Đường dẫn tuyệt đối đến thư mục gốc dự án
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"
GIT_HISTORY_DIR = PROJECT_ROOT / "config_history"
REPORT_DIR = PROJECT_ROOT / "reports"


def main():
    logger = setup_logging()

    try:
        # Bước 1: Đọc và hiển thị danh sách thiết bị
        devices = load_inventory()
        display_inventory(devices)

        # Bước 2: Lấy thông tin đăng nhập SSH
        username, password = get_credentials()

        # Bước 3: Backup nhiều thiết bị
        print("\n===== START NETWORK BACKUP =====")
        logger.info(
            "Bắt đầu sao lưu %d thiết bị",
            len(devices)
        )

        results = backup_all(
            devices,
            username,
            password,
            max_workers=3
        )

        # Bước 4: Ghi log kết quả backup
        for result in results:
            device_name = result["name"]

            if result["status"] == "success":
                logger.info(
                    "BACKUP SUCCESS | %s",
                    device_name
                )
            else:
                logger.error(
                    "BACKUP FAILED | %s | %s",
                    device_name,
                    result.get("error", "Unknown error")
                )

        # Bước 5: Thống kê kết quả backup
        success = sum(
            result["status"] == "success"
            for result in results
        )

        failed = len(results) - success

        print("\n===== BACKUP REPORT =====")

        for result in results:
            print(
                f"{result['name']}: "
                f"{result['status'].upper()}"
            )

        print(f"\nTổng thiết bị: {len(results)}")
        print(f"Thành công: {success}")
        print(f"Thất bại: {failed}")

        logger.info(
            "Hoàn thành backup: %d/%d thiết bị thành công",
            success,
            len(results)
        )

        # Bước 6: Khởi tạo dữ liệu báo cáo CSV
        report_records = {}

        for result in results:
            device_name = result["name"]

            report_records[device_name] = {
                "Device": device_name,
                "IP": result.get("host", ""),
                "Backup Status": result["status"].upper(),
                "Change Status": "SKIPPED",
                "Git Status": "SKIPPED",
                "Commit": "",
                "Error": result.get("error", "") or ""
            }

        # Bước 7: Phát hiện thay đổi cấu hình
        print("\n===== CONFIGURATION CHANGE REPORT =====")

        for result in results:
            device_name = result["name"]

            if result["status"] != "success":
                print(
                    f"[SKIPPED] {device_name}: Backup failed"
                )
                continue

            try:
                change = detect_changes(
                    device_name,
                    backup_dir=BACKUP_DIR
                )

                status = change["status"]

                # Cập nhật trạng thái Change Detection
                report_records[device_name][
                    "Change Status"
                ] = status

                print(f"[{status}] {device_name}")

                if status == "CHANGED":
                    print(change["diff"])

                    logger.info(
                        "CONFIG CHANGED | %s",
                        device_name
                    )

                elif status == "UNCHANGED":
                    logger.info(
                        "CONFIG UNCHANGED | %s",
                        device_name
                    )

                elif status == "FIRST_BACKUP":
                    logger.info(
                        "FIRST BACKUP | %s",
                        device_name
                    )

                elif status == "NO_BACKUP":
                    logger.warning(
                        "NO BACKUP | %s",
                        device_name
                    )

            except Exception as error:
                report_records[device_name][
                    "Change Status"
                ] = "ERROR"

                report_records[device_name][
                    "Error"
                ] = str(error)

                logger.error(
                    "CHANGE DETECTION FAILED | %s | %s",
                    device_name,
                    error
                )

                print(
                    f"[ERROR] {device_name}: {error}"
                )

        # Bước 8: Tự động lưu lịch sử cấu hình bằng Git
        print("\n===== GIT AUTOMATION REPORT =====")

        try:
            git_manager = GitManager(
                repo_dir=GIT_HISTORY_DIR
            )

        except Exception as error:
            logger.error(
                "GIT INITIALIZATION FAILED | %s",
                error
            )

            print(
                f"[GIT ERROR] Initialization: {error}"
            )

            git_manager = None

        for result in results:
            device_name = result["name"]

            # Không lưu Git nếu backup thất bại
            if result["status"] != "success":
                print(
                    f"[SKIPPED] {device_name}: Backup failed"
                )
                continue

            if git_manager is None:
                report_records[device_name][
                    "Git Status"
                ] = "ERROR"

                report_records[device_name][
                    "Error"
                ] = "Git initialization failed"

                print(
                    f"[SKIPPED] {device_name}: Git unavailable"
                )
                continue

            try:
                backup_file = result["file"]

                git_result = git_manager.save_config(
                    device_name,
                    backup_file
                )

                git_status = git_result["status"]

                # Cập nhật báo cáo CSV
                report_records[device_name][
                    "Git Status"
                ] = git_status

                report_records[device_name][
                    "Commit"
                ] = git_result.get("commit") or ""

                print(
                    f"[GIT {git_status}] {device_name}"
                )

                if git_status == "COMMITTED":
                    commit_hash = git_result["commit"]

                    print(
                        f"Commit: {commit_hash[:7]}"
                    )

                    logger.info(
                        "GIT COMMITTED | %s | %s",
                        device_name,
                        commit_hash
                    )

                elif git_status == "UNCHANGED":
                    logger.info(
                        "GIT UNCHANGED | %s",
                        device_name
                    )

            except Exception as error:
                report_records[device_name][
                    "Git Status"
                ] = "ERROR"

                report_records[device_name][
                    "Error"
                ] = str(error)

                logger.error(
                    "GIT AUTOMATION FAILED | %s | %s",
                    device_name,
                    error
                )

                print(
                    f"[GIT ERROR] {device_name}: {error}"
                )

        # Bước 9: Xuất báo cáo CSV
        print("\n===== CSV REPORT =====")

        try:
            csv_file = export_csv_report(
                list(report_records.values()),
                report_dir=REPORT_DIR
            )

            print(
                f"[CSV SUCCESS] {csv_file}"
            )

            logger.info(
                "CSV REPORT CREATED | %s",
                csv_file
            )

        except Exception as error:
            logger.error(
                "CSV REPORT FAILED | %s",
                error
            )

            print(
                f"[CSV ERROR] {error}"
            )

        # Bước 10: Trả mã lỗi nếu backup thất bại
        if failed > 0:
            raise SystemExit(1)

    except (FileNotFoundError, ValueError) as error:
        logger.error(
            "Lỗi chương trình: %s",
            error
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
