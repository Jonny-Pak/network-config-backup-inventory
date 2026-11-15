# Hướng dẫn chạy bản nâng cấp

Các lệnh PowerShell chạy tại `D:\Code\network-config-backup-inventory`.
Không cần kích hoạt môi trường ảo. Mã vẫn hỗ trợ Python 3.9 của project; có thể dùng Python 3.11/3.12 cho môi trường mới.

## 1. Cài thư viện và kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
```

## 2. Chạy demo không cần router

```powershell
.\.venv\Scripts\python.exe -X utf8 -m src.scheduler --once --demo
.\.venv\Scripts\python.exe -X utf8 -m src.main --demo
.\.venv\Scripts\python.exe -m streamlit run dashboard.py --server.address 127.0.0.1
```

Mở http://localhost:8501, chọn **Demo**. Lần đầu có 3 thiết bị và FIRST_BACKUP/COMMITTED; lần sau UNCHANGED, không thêm commit.
Demo dùng `config/devices.demo.yaml`, `samples/cisco.txt`, `samples/junos.txt`; toàn bộ kết quả nằm trong `demo/`, tách khỏi dữ liệu thật.
Để thử thay đổi, sửa `description MANAGEMENT` trong `samples/cisco.txt`, chạy demo lại. Hai Cisco dùng cùng mẫu nên đều đổi; Juniper giữ nguyên. Khôi phục mẫu sau khi demo.

## 3. Chuẩn bị chạy thật trong GNS3

1. Khởi động GNS3 VM/VMware và router; kiểm tra IP quản trị trong `config/devices.yaml`. Project hiện dùng `192.168.36.11` và `.12`, không dùng subnet ví dụ `.56` của chat cũ.
2. Kiểm tra đường mạng từ Windows:

```powershell
Test-NetConnection 192.168.36.11 -Port 22
Test-NetConnection 192.168.36.12 -Port 22
Copy-Item .env.example .env
```

Chỉnh `.env` bằng trình soạn thảo:

```dotenv
NET_USERNAME=backupuser
NET_PASSWORD=<mật khẩu của lab>
NET_SECRET=
BACKUP_ALLOWED_CIDRS=192.168.36.0/24
BACKUP_KNOWN_HOSTS=
BACKUP_HOUR=2
BACKUP_MINUTE=0
BACKUP_TIMEZONE=Asia/Ho_Chi_Minh
BACKUP_TIMEOUT_SECONDS=600
```

`NET_SECRET` chỉ cần khi Cisco phải vào enable. Scheduler cần username/password có sẵn, không hiển thị câu hỏi nhập mật khẩu. Chạy trực tiếp trên terminal có thể nhập nếu thiếu biến môi trường. Biến môi trường hệ điều hành ưu tiên hơn `.env`. Không đưa `.env` vào Git.

3. Xác minh host key: dùng console/nguồn quản trị tin cậy để lấy fingerprint. Kết nối thủ công:

```powershell
ssh backupuser@192.168.36.11
ssh backupuser@192.168.36.12
```

Chỉ chấp nhận key sau khi fingerprint trùng nguồn tin cậy. Chương trình đọc `~/.ssh/known_hosts`. Nếu dùng file khác hoặc chạy scheduler dưới tài khoản khác, đặt `BACKUP_KNOWN_HOSTS` tới file key đã xác minh. File tương đối được tính từ thư mục gốc project. Không tự bỏ kiểm tra key khi gặp lỗi. Với cổng khác 22, known_hosts phải có tên `[IP]:port`.

4. Chạy một lượt:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m src.main
# Hoặc qua bộ chạy có timeout:
.\.venv\Scripts\python.exe -X utf8 -m src.scheduler --once
```

Dashboard chọn **Thiết bị thật**. Xem `reports/latest.json`, CSV và `config_history/`. Mỗi thiết bị vẫn được xử lý độc lập khi router khác lỗi. Exit 0 chỉ khi backup/diff/Git/báo cáo thành công; exit 1 nếu lỗi; `src.main` exit 2 nếu đã có lượt chạy khác. Bộ chạy scheduler trả exit 1 khi job thất bại hoặc bị bỏ qua, và ghi lý do trong `scheduler_status.json`.

## 4. Scheduler tự động

```powershell
.\.venv\Scripts\python.exe -X utf8 -m src.scheduler
# Thử lịch bằng dữ liệu mẫu:
.\.venv\Scripts\python.exe -X utf8 -m src.scheduler --demo
```

Mặc định 02:00 giờ Việt Nam; chỉnh `.env` rồi khởi động lại scheduler. Máy phải thức và tiến trình phải hoạt động. `Ctrl+C` dừng scheduler. Không chạy thêm lịch khác cho cùng dữ liệu; khóa hệ điều hành vẫn chặn các lượt trùng từ nhiều terminal/process. Khóa tự giải phóng nếu tiến trình chết; không cần xóa file `.backup.lock`.

Muốn tự chạy khi đăng nhập, tạo tác vụ Windows Task Scheduler với:

- Program: `D:\Code\network-config-backup-inventory\.venv\Scripts\python.exe`
- Arguments: `-X utf8 -m src.scheduler`
- Start in: `D:\Code\network-config-backup-inventory`
- Trigger: At log on; chọn cùng tài khoản có `.env` và known_hosts, chọn không khởi tạo thêm instance khi tác vụ đang chạy.

Đây là hướng dẫn; chưa tạo tác vụ tự khởi động trên máy. Dashboard chạy ở terminal riêng và chỉ lắng nghe localhost, không có nút điều khiển router.

## 5. Bổ sung Juniper

Thêm thiết bị vào `config/devices.yaml` khi đã có image hợp lệ, IP và SSH hoạt động:

```yaml
  - name: J1-JUNIPER
    host: 192.168.36.13
    device_type: juniper_junos
    port: 22
```

Mở rộng allowlist nếu subnet khác; xác minh host key và quyền tài khoản như Cisco. Adapter dùng `show configuration | display set | no-more`, Cisco dùng `show running-config`. Cần xác minh lệnh trên image thực tế. Demo/mô phỏng Juniper đã có, chưa có kết quả kiểm thử router Junos thật.

## 6. Các file và trách nhiệm

| File | Công việc |
| --- | --- |
| `src/main.py` | Điều phối một lượt, thống kê từng thiết bị, báo cáo JSON/CSV, mã thoát |
| `src/backup_manager.py` | Đa luồng, chọn lệnh Cisco/Junos, lọc trước khi ghi, timestamp microsecond |
| `src/secret_filter.py` | Che secret theo mẫu, PEM private key và dòng nghi nhạy cảm |
| `src/security.py` | IP allowlist và kiểm tra SSH host key nghiêm ngặt |
| `src/ssh_connector.py` | Thông tin đăng nhập, SSH, enable Cisco khi có NET_SECRET |
| `src/runtime.py` | Đường dẫn, `.env`, khóa hệ điều hành Windows/Linux |
| `src/run_backup.py` | Chạy tiến trình backup có timeout và ghi trạng thái scheduler |
| `src/scheduler.py` | Lịch hằng ngày có múi giờ, `--once`, `--demo` |
| `src/change_detector.py`, `src/config_diff.py` | So sánh bản đã lọc, theo timestamp tên file, bỏ header IOS biến động |
| `src/git_manager.py` | Lọc lần nữa trước Git, commit riêng file cấu hình đã chọn |
| `dashboard.py` | Chạy backup Demo hoặc thiết bị thật qua form; đọc JSON, thống kê router, diff, commit, 30 lượt gần nhất, cập nhật 15 giây |
| `tests/test_upgrade.py` | Kiểm thử tích hợp, timeout, khóa nhiều process, redaction, Junos, Git |

File `config/setting.yaml` và `src/security_manager.py` có sẵn nhưng trống được giữ nguyên; cấu hình nâng cấp dùng `.env` để tránh hai nguồn cấu hình.

## 7. Bảo mật và giới hạn

- Backup và Git mới đều là bản đã che secret để đọc/diff, không đủ để khôi phục đầy đủ thiết bị. Chưa triển khai kho cấu hình gốc mã hóa.
- Bộ lọc dựa trên mẫu không đảm bảo nhận diện mọi bí mật trên mọi phiên bản. Cột Warnings là số dòng mơ hồ bị che hoàn toàn. Không thay thế kiểm tra dữ liệu trước khi chia sẻ.
- Không tự sửa/xóa backup và Git history cũ. Secret từng được lưu vẫn có thể tồn tại trong những bản đó; bổ sung bộ lọc không xóa lịch sử cũ.
- Chỉ lưu loại lỗi vào báo cáo, không lưu stdout/stderr của SSH hay exception thô có thể chứa credential. Kiểm tra lỗi theo loại: PermissionError thường là allowlist; FileNotFoundError có thể là file key; SSHException thường cần kiểm tra known_hosts; xác thực/timeout được bọc RuntimeError.
- Scheduler chạy nền trong tiến trình, không tự sống qua reboot. Có timeout toàn lượt; báo cáo scheduler là nguồn xác định TIMEOUT, báo cáo thiết bị có thể thuộc lượt hoàn thành trước.
- Secret thay đổi sau khi che có thể không tạo diff; đây là hành vi của bản dùng để kiểm tra cấu hình.
- Dashboard chưa có đăng nhập và chỉ nên dùng qua localhost; chưa triển khai cảnh báo email hay khôi phục cấu hình.

## 8. Checklist kiểm chứng trên thiết bị thật

| Tình huống | Kết quả cần xác nhận |
| --- | --- |
| Backup lần đầu | SUCCESS, FIRST_BACKUP, Git COMMITTED, file không còn secret |
| Chạy lại không đổi | UNCHANGED và không thêm commit |
| Đổi interface description | CHANGED, diff đúng và commit mới |
| Tắt một router | Router đó FAILED, router khác tiếp tục, exit 1 |
| Sai password | FAILED, không có mật khẩu trong báo cáo |
| Host key thay đổi/không tin cậy | Từ chối kết nối |
| IP ngoài allowlist | Từ chối trước khi mở SSH |
| Chạy hai lượt đồng thời | Lượt sau SKIPPED, không ghi đè snapshot |
| Juniper | Đúng lệnh display set và kết quả trên Junos thật |
| Lịch tự động | Chạy đúng múi giờ và xuất báo cáo từng thiết bị |

Tài liệu API đối chiếu: [APScheduler 3.x](https://apscheduler.readthedocs.io/en/3.x/userguide.html), [Streamlit fragment](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment), [Netmiko SSH](https://ktbyers.github.io/netmiko/docs/netmiko/).

## 9. Kiểm thử tiếp theo: lịch chạy và lỗi kết nối

Thử một lượt được scheduler tự kích hoạt sau 5 giây (khác với chạy ngay bằng `--once`):

```powershell
.\.venv\Scripts\python.exe -X utf8 -m src.scheduler --test-after 5
```

Tiến trình đợi đến thời điểm hẹn, thực hiện backup rồi tự dừng. Minh chứng gồm thời điểm hẹn, thời điểm bắt đầu và kết quả trong `reports/scheduled_test.json`; dashboard vẫn đọc kết quả live bình thường. Chế độ này không sửa giờ chạy trong `.env` và không tạo tác vụ Windows. Để giữ lịch hằng ngày hoạt động, chạy `python -m src.scheduler` và giữ máy thức/tiến trình hoạt động.

Chạy kiểm tra mạng có lỗi mà không tắt router:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m src.validate_lab
```

Chương trình tạo thư mục `validation/<thời-gian>/`, backup cả hai router, chạy lại khi không đổi, rồi thử thiết bị cuối bằng cổng TCP đóng `65022`. R1 vẫn phải thành công; R2 phải thất bại và bỏ qua Git. Kiểm tra này không thay đổi IP, mật khẩu, interface hay cổng SSH thật trong inventory. Không thay báo cáo live hiện tại bằng kết quả lỗi. Nếu cổng thử đang mở, chương trình dừng trước khi gửi thông tin đăng nhập. Kết quả là `RESULTS.md`, `summary.json`, các báo cáo và Git riêng trong thư mục validation. Kiểm tra secret chỉ đối chiếu mật khẩu đăng nhập/enable đã cấu hình với các bản thử mới, không khẳng định mọi secret đều được phát hiện.

Nếu cần minh chứng router tắt thật khi bảo vệ:

1. Trong GNS3, chỉ dừng R2; giữ R1 và switch quản trị hoạt động.
2. Chạy `python -m src.scheduler --once`.
3. Chụp dashboard: một thành công, một thất bại, R2 Git SKIPPED; mã thoát khác 0 là kết quả mong đợi.
4. Khởi động lại R2, chờ SSH sẵn sàng và backup lại; cả hai phải thành công.

Kiểm thử cổng đóng và tắt router thật là hai tình huống khác nhau; ghi đúng phương pháp trong báo cáo. Chưa tự thực hiện tắt R2 hoặc thử sai mật khẩu trên thiết bị.
