"""Local backup dashboard with explicit Demo and live-run controls."""
import json
from pathlib import Path
import streamlit as st
from src.secret_filter import redact_config
from src.run_backup import execute

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Network Backup Monitor", page_icon="🛜", layout="wide")
st.title("Network Backup Monitor")
st.caption("NETWORK CONFIGURATION & INVENTORY · Theo dõi sao lưu cấu hình")
mode = st.sidebar.radio("Nguồn dữ liệu", ["Demo", "Thiết bị thật"])
reports = (ROOT / "demo" if mode == "Demo" else ROOT) / "reports"

# Clear sensitive widget values on the rerun immediately after a live request.
if st.session_state.pop("_clear_live_credentials", False):
    for key in ("live_username", "live_password", "live_secret"):
        st.session_state[key] = ""


def trigger_backup(demo=False, credentials=None):
    try:
        result = execute(demo=demo, credentials=credentials)
    except Exception as error:
        result = {"status": "FAILED", "error_type": type(error).__name__,
                  "mode": "demo" if demo else "live"}
    st.session_state["_backup_action_result"] = result
    if not demo:
        st.session_state["_clear_live_credentials"] = True
    st.rerun()


st.sidebar.subheader("Chạy backup")
if mode == "Demo":
    st.sidebar.caption("Chạy trên dữ liệu mẫu offline; không kết nối thiết bị thật.")
    if st.sidebar.button("Chạy backup Demo", type="primary", use_container_width=True):
        with st.spinner("Đang chạy backup Demo…"):
            trigger_backup(demo=True)
else:
    st.sidebar.warning("Chế độ này kết nối SSH và ghi backup/Git vào thư mục thiết bị thật.")
    with st.sidebar.form("live_backup_form"):
        live_username = st.text_input("Tên đăng nhập SSH", key="live_username")
        live_password = st.text_input("Mật khẩu SSH", type="password", key="live_password")
        live_secret = st.text_input("Enable secret (nếu có)", type="password", key="live_secret")
        live_confirmed = st.checkbox(
            "Tôi đã kiểm tra inventory, allowlist và SSH host key",
            key="live_backup_confirmed",
        )
        live_submitted = st.form_submit_button(
            "Chạy backup thiết bị thật", type="primary", disabled=not live_confirmed,
            use_container_width=True,
        )
    if live_submitted:
        if bool(live_username.strip()) != bool(live_password):
            st.sidebar.error("Hãy nhập cả tên đăng nhập và mật khẩu, hoặc để cả hai trống để dùng .env.")
        else:
            credentials = None
            if live_username.strip() and live_password:
                credentials = (live_username.strip(), live_password, live_secret)
            with st.spinner("Đang kết nối và chạy backup thiết bị thật…"):
                trigger_backup(demo=False, credentials=credentials)

action_result = st.session_state.pop("_backup_action_result", None)
if action_result:
    action_mode = "Demo" if action_result.get("mode") == "demo" else "Thiết bị thật"
    if action_result.get("status") == "SUCCESS":
        st.sidebar.success(f"Backup {action_mode} hoàn tất.")
    elif action_result.get("error_type") == "ALREADY_RUNNING":
        st.sidebar.warning("Đã có một lượt backup đang chạy.")
    else:
        error_type = action_result.get("error_type") or "BACKUP_FAILED"
        st.sidebar.error(f"Backup {action_mode} chưa hoàn tất ({error_type}). Xem báo cáo bên dưới.")

st.sidebar.info("Báo cáo tự cập nhật mỗi 15 giây.")


def read_report(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


@st.fragment(run_every="15s")
def show_status():
    data = read_report(reports / "latest.json")
    job = read_report(reports / "scheduler_status.json")
    if job:
        st.caption(f"Scheduler: {job.get('status', '—')} · {job.get('finished_at_utc', '')} · UTC")
        if job.get('status') == 'FAILED':
            st.warning(f"Lượt chạy qua scheduler thất bại: {job.get('error_type', 'UNKNOWN')}. Báo cáo bên dưới có thể thuộc lượt trước; hãy đối chiếu thời gian.")
    if not data:
        st.info("Chưa có báo cáo hợp lệ. Chọn Demo rồi nhấn ‘Chạy backup Demo’ để tạo lượt thử đầu tiên.")
        return
    status = data.get("status", "UNKNOWN")
    stamp = data.get("finished_at_utc", "")
    st.subheader(f"Lần chạy gần nhất · {status}")
    st.caption(f"{stamp} · UTC · Chế độ: {data.get('mode', '')}")
    if data.get("error_type"):
        st.error(f"Lỗi khởi chạy: {data['error_type']}. Kiểm tra cấu hình và thông tin đăng nhập.")
    cols = st.columns(4)
    for col, label, key in zip(cols, ["Thiết bị", "Backup thành công", "Backup thất bại", "Thay đổi"], ["total", "success", "failed", "changed"]):
        col.metric(label, data.get(key, 0))
    records = data.get("devices", [])
    if not isinstance(records, list) or not records:
        return
    rows = [{k: v for k, v in r.items() if k != "Diff"} for r in records if isinstance(r, dict)]
    st.dataframe(rows, hide_index=True)
    selected = st.selectbox("Xem thay đổi cấu hình", [r["Device"] for r in rows])
    record = next(r for r in records if r["Device"] == selected)
    st.caption(f"{record.get('Change Status')} · Git {record.get('Git Status')} · Commit {record.get('Commit') or '—'}")
    diff = record.get("Diff", "")
    if diff:
        st.code(redact_config(diff)[0], language="diff")
    else:
        st.info("Không có diff trong lần chạy này.")
    st.subheader("Lịch sử các lần chạy")
    history = []
    for path in sorted(reports.glob("run_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
        previous = read_report(path)
        if previous:
            history.append({"Thời gian (UTC)": previous.get("finished_at_utc"),
                            "Trạng thái": previous.get("status"), "Thiết bị": previous.get("total"),
                            "Thành công": previous.get("success"), "Thay đổi": previous.get("changed")})
    st.dataframe(history, hide_index=True)


show_status()
