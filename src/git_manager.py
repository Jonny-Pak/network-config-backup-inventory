
import subprocess
from pathlib import Path


class GitManager:
    """Quản lý lịch sử cấu hình trong Git repository cục bộ."""

    def __init__(self, repo_dir="config_history"):
        self.repo_dir = Path(repo_dir).resolve()
        self.repo_dir.mkdir(parents=True, exist_ok=True)

        # Không cho phép dùng nhầm Git repository cha
        if not (self.repo_dir / ".git").is_dir():
            self._git("init")
            self._git("config", "user.name", "Network Backup Bot")
            self._git(
                "config",
                "user.email",
                "network-backup@localhost"
            )




    def _git(self, *args):
        result = subprocess.run(
            ["git", "-C", str(self.repo_dir), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Git command failed: git {' '.join(args)}\n"
                f"Exit code: {result.returncode}\n"
                f"Git error: {result.stderr.strip()}"
            )

        return result.stdout.strip()



    def save_config(self, device_name, backup_file):
        """Lưu cấu hình và commit nếu có thay đổi."""

        # Chỉ cho phép tên thiết bị an toàn
        if not device_name or not all(
            c.isalnum() or c in "-_"
            for c in device_name
        ):
            raise ValueError("Tên thiết bị không hợp lệ")

        source = Path(backup_file)

        if not source.is_file():
            raise FileNotFoundError(source)

        destination = self.repo_dir / f"{device_name}.cfg"

        new_content = source.read_bytes()

        if (
            destination.exists()
            and destination.read_bytes() == new_content
        ):
            return {
                "device": device_name,
                "status": "UNCHANGED",
                "commit": None
            }

        destination.write_bytes(new_content)

        self._git("add", "--", destination.name)

        self._git(
            "commit",
            "-m",
            f"Backup configuration: {device_name}"
        )

        commit_hash = self._git("rev-parse", "HEAD")

        return {
            "device": device_name,
            "status": "COMMITTED",
            "commit": commit_hash
        }


    def get_history(self, device_name, limit=10):
        """Lấy lịch sử commit của một thiết bị."""

        if not device_name or not all(
            c.isalnum() or c in "-_"
            for c in device_name
        ):
            raise ValueError("Tên thiết bị không hợp lệ")

        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit phải là số nguyên dương")

        return self._git(
            "log",
            f"-{limit}",
            "--format=%h | %ad | %s",
            "--date=short",
            "--",
            f"{device_name}.cfg"
        )

