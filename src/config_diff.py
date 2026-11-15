
from pathlib import Path
import difflib
try:
    from .backup_manager import prepare_config
except ImportError:
    from backup_manager import prepare_config


def compare_configs(old_file, new_file):
    """So sánh hai file cấu hình Cisco."""

    old_path = Path(old_file)
    new_path = Path(new_file)

    if not old_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy: {old_path}")

    if not new_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy: {new_path}")

    old_lines = prepare_config(old_path.read_text(encoding="utf-8"))[0].splitlines(keepends=True)

    new_lines = prepare_config(new_path.read_text(encoding="utf-8"))[0].splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=old_path.name,
        tofile=new_path.name,
        lineterm="\n"
    )

    return "".join(diff)


def has_changes(old_file, new_file):
    """Kiểm tra hai cấu hình có khác nhau không."""
    return bool(compare_configs(old_file, new_file))
