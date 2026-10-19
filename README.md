# Hệ thống sao lưu cấu hình và quản lý thiết bị mạng

**Network Configuration Backup & Inventory** — Đồ án môn học **Quản trị mạng nâng cao**.

Ứng dụng Python giúp quản lý danh sách thiết bị, sao lưu cấu hình qua SSH, phát hiện thay đổi và lưu lịch sử bằng Git. Dự án phục vụ thực hành tự động hóa quản trị mạng với mô hình Cisco IOS trên GNS3.

## Thành viên nhóm

| STT | Họ và tên | Mã số sinh viên |
| --- | --- | --- |
| 1 | Lê Ngọc Thuận | 1250080192 |
| 2 | Lê Thanh Tính | 1250080199 |
| 3 | Dương Minh Triết | 1250080211 |

## Mục lục

- [Chức năng chính](#chức-năng-chính)
- [Quy trình hoạt động](#quy-trình-hoạt-động)
- [Mô hình thử nghiệm](#mô-hình-thử-nghiệm)
- [Cài đặt và sử dụng](#cài-đặt-và-sử-dụng)
- [Kết quả và lịch sử cấu hình](#kết-quả-và-lịch-sử-cấu-hình)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Kiểm thử](#kiểm-thử)
- [Xử lý sự cố](#xử-lý-sự-cố)
- [Bảo vệ dữ liệu](#bảo-vệ-dữ-liệu)
- [Phạm vi và hướng phát triển](#phạm-vi-và-hướng-phát-triển)

## Chức năng chính

| Chức năng | Mô tả |
| --- | --- |
| Quản lý thiết bị | Đọc danh sách từ YAML; kiểm tra tên, địa chỉ IP, loại thiết bị và cổng SSH; phát hiện tên hoặc địa chỉ kết nối trùng lặp. |
| Sao lưu qua SSH | Sử dụng Netmiko để thu thập cấu hình bằng lệnh `show running-config`. |
| Xử lý song song | Sao lưu nhiều thiết bị bằng `ThreadPoolExecutor`; chương trình chính sử dụng tối đa 3 luồng. |
| So sánh cấu hình | So sánh hai bản sao lưu gần nhất và hiển thị các dòng thay đổi bằng `difflib`. |
| Lưu lịch sử | Tự tạo kho Git cục bộ cho cấu hình; chỉ tạo commit khi nội dung khác phiên bản đã lưu. |
| Báo cáo và nhật ký | Xuất kết quả theo thiết bị ra CSV và ghi nhật ký hoạt động, lỗi kết nối. |

**Công nghệ:** Python, Netmiko, PyYAML, Git và các thư viện chuẩn của Python (`concurrent.futures`, `difflib`, `csv`, `logging`, `unittest`).

## Quy trình hoạt động

```mermaid
flowchart LR
    A[Đọc và kiểm tra YAML] --> B[Nhập thông tin SSH]
    B --> C[Sao lưu song song]
    C --> D[So sánh cấu hình]
    D --> E[Lưu lịch sử Git cục bộ]
    E --> F[Xuất báo cáo CSV]
```

Mỗi thiết bị có kết quả xử lý riêng. Khi một thiết bị sao lưu thất bại, chương trình bỏ qua bước so sánh và lưu Git của thiết bị đó, đồng thời tiếp tục xử lý các thiết bị còn lại.

## Mô hình thử nghiệm

```text
Máy Windows chạy Python (192.168.36.1)
                  |
             VMware VMnet1
                  |
              GNS3 Cloud
                  |
               SW-MGMT
              /       \
         R1-CISCO    R2-CISCO
      192.168.36.11  192.168.36.12
          SSH 22        SSH 22
```

| Thiết bị | Địa chỉ quản trị | Nền tảng | Cổng SSH |
| --- | --- | --- | --- |
| R1-CISCO | 192.168.36.11 | Cisco 3725 / Cisco IOS | 22 |
| R2-CISCO | 192.168.36.12 | Cisco 3725 / Cisco IOS | 22 |

Các địa chỉ trên thuộc mạng thử nghiệm. Khi sử dụng mô hình khác, cần cập nhật địa chỉ và cấu hình kết nối tương ứng.

Tài liệu chi tiết: [Thiết lập mạng GNS3](network/gns3-topology/network-setup.md) · [Kế hoạch địa chỉ IP](network/gns3-topology/ip-addressing.md).

## Cài đặt và sử dụng

### 1. Chuẩn bị môi trường

- Python 3.9 trở lên; chọn phiên bản Netmiko và PyYAML tương thích với Python đang dùng.
- Git có trong `PATH` của máy chạy chương trình.
- Thiết bị Cisco IOS đã bật SSH và tài khoản có quyền chạy `show running-config`.
- Kết nối mạng từ máy chạy Python đến địa chỉ quản trị của thiết bị.
- GNS3 và VMware nếu sử dụng mô hình thử nghiệm của dự án.

Các lệnh dưới đây sử dụng **PowerShell trên Windows** và được chạy tại thư mục gốc dự án.

### 2. Tải mã nguồn và cài thư viện

```powershell
git clone --branch develop https://github.com/Jonny-Pak/network-config-backup-inventory.git
cd network-config-backup-inventory
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install netmiko PyYAML
git --version
```

Các bước tiếp theo gọi trực tiếp Python trong môi trường ảo, không cần kích hoạt môi trường bằng script PowerShell.

### 3. Cấu hình danh sách thiết bị

Chỉnh sửa [config/devices.yaml](config/devices.yaml):

```yaml
devices:
  - name: R1-CISCO
    host: 192.168.36.11
    device_type: cisco_ios
    port: 22

  - name: R2-CISCO
    host: 192.168.36.12
    device_type: cisco_ios
    port: 22
```

| Trường | Quy tắc |
| --- | --- |
| `name` | Bắt buộc, duy nhất; chỉ gồm chữ cái không dấu, chữ số, dấu gạch ngang hoặc gạch dưới. |
| `host` | Bắt buộc, là địa chỉ IPv4 hoặc IPv6 hợp lệ. |
| `device_type` | Bắt buộc; mô hình hiện tại sử dụng `cisco_ios`. |
| `port` | Số nguyên từ 1 đến 65535; mặc định là `22` nếu bỏ qua. |

Không khai báo trùng cặp `host` và `port`. Các trường bổ sung như `vendor`, `model`, `location` có thể dùng để mô tả thiết bị.

Kiểm tra danh sách trước khi kết nối:

```powershell
.\.venv\Scripts\python.exe .\src\inventory.py
```

### 4. Kiểm tra kết nối SSH

Khởi động router, kiểm tra địa chỉ IP, trạng thái giao diện quản trị và cấu hình xác thực SSH. Sau đó kiểm tra cổng TCP:

```powershell
Test-NetConnection 192.168.36.11 -Port 22
Test-NetConnection 192.168.36.12 -Port 22
```

`TcpTestSucceeded : True` cho biết cổng có thể truy cập; kết quả này chưa xác nhận thông tin đăng nhập SSH hợp lệ.

### 5. Chạy chương trình

```powershell
.\.venv\Scripts\python.exe .\src\main.py
```

Chương trình hiển thị danh sách thiết bị và yêu cầu nhập tên đăng nhập, mật khẩu SSH. Một bộ thông tin đăng nhập được sử dụng cho các thiết bị trong lần chạy đó.

Sau khi hoàn tất, màn hình hiển thị kết quả sao lưu, thay đổi cấu hình, kết quả lưu Git và đường dẫn báo cáo CSV. Nếu có thiết bị sao lưu thất bại, chương trình kết thúc với mã lỗi `1`.

## Kết quả và lịch sử cấu hình

### Dữ liệu được tạo

| Thư mục | Nội dung |
| --- | --- |
| `backups/` | Bản sao lưu theo thiết bị và thời điểm, ví dụ `R1-CISCO_20261019_143000.cfg`. |
| `config_history/` | Kho Git cục bộ riêng, lưu cấu hình hiện tại của từng thiết bị trong tệp `<tên-thiết-bị>.cfg`. |
| `reports/` | Báo cáo `network_report_<thời-gian>.csv`, mã hóa UTF-8 có BOM để hỗ trợ Excel. |
| `logs/` | Nhật ký hoạt động của chương trình. |

### Trạng thái so sánh cấu hình

| Trạng thái | Ý nghĩa |
| --- | --- |
| `FIRST_BACKUP` | Mới có một bản sao lưu, chưa có phiên bản trước để so sánh. |
| `CHANGED` | Hai bản sao lưu gần nhất có nội dung khác nhau. |
| `UNCHANGED` | Hai bản sao lưu gần nhất giống nhau. |
| `NO_BACKUP` | Không tìm thấy bản sao lưu của thiết bị. |
| `SKIPPED` | Bỏ qua so sánh vì sao lưu thất bại. |
| `ERROR` | Có lỗi trong quá trình so sánh. |

Bước lưu Git so sánh bản sao lưu với cấu hình hiện tại trong `config_history/`. Trạng thái `COMMITTED` cho biết đã tạo phiên bản mới; `UNCHANGED` cho biết không cần tạo commit.

Tra cứu lịch sử toàn bộ cấu hình hoặc riêng một thiết bị:

```powershell
git -C config_history log --oneline
git -C config_history log --oneline -- R1-CISCO.cfg
```

Kho lịch sử cấu hình được khởi tạo với danh tính `Network Backup Bot`. Chương trình chỉ lưu lịch sử cục bộ, không tự động đẩy cấu hình lên GitHub.

### Báo cáo CSV

Mỗi dòng tương ứng một thiết bị, gồm các cột:

```csv
Device,IP,Backup Status,Change Status,Git Status,Commit,Error
R1-CISCO,192.168.36.11,SUCCESS,CHANGED,COMMITTED,<ma-commit>,
R2-CISCO,192.168.36.12,SUCCESS,UNCHANGED,UNCHANGED,,
```

Ví dụ trên minh họa cấu trúc báo cáo. Cột `Commit` chứa mã phiên bản mới nếu có; cột `Error` ghi thông tin lỗi khi xử lý thiết bị.

## Cấu trúc dự án

```text
network-config-backup-inventory/
├── config/
│   └── devices.yaml          # Danh sách và thông tin thiết bị
├── src/
│   ├── main.py               # Điều phối quy trình
│   ├── inventory.py          # Đọc và kiểm tra YAML
│   ├── ssh_connector.py      # Xác thực và kết nối SSH
│   ├── backup_manager.py     # Sao lưu nhiều thiết bị
│   ├── config_diff.py        # So sánh nội dung cấu hình
│   ├── change_detector.py    # Phát hiện thay đổi giữa các bản sao lưu
│   ├── git_manager.py        # Quản lý lịch sử Git cục bộ
│   ├── report_manager.py     # Xuất báo cáo CSV
│   └── logger_config.py      # Cấu hình nhật ký
├── tests/                    # Kiểm thử tự động và dữ liệu mẫu
├── network/gns3-topology/     # Tài liệu mô hình mạng
├── .gitignore
└── README.md
```

Ngoài các mô-đun chính, `src/` còn có các script hỗ trợ kiểm tra và sao lưu: `backup.py`, `test_connection.py`, `test_ssh.py`.

## Kiểm thử

Chạy bộ kiểm thử tự động:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Các nhóm kiểm thử bao gồm: kiểm tra danh sách thiết bị, quản lý sao lưu, so sánh cấu hình, phát hiện thay đổi, lưu lịch sử Git và xuất CSV. Các bài kiểm thử dùng dữ liệu mẫu hoặc mô phỏng kết nối; cần kiểm tra riêng với router GNS3 để đánh giá kết nối SSH thực tế.

## Xử lý sự cố

| Hiện tượng | Nội dung cần kiểm tra |
| --- | --- |
| Không tìm thấy thư viện Python | Cài Netmiko và PyYAML bằng đúng Python trong `.venv`. |
| Danh sách thiết bị không hợp lệ | Kiểm tra cấu trúc YAML, tên duy nhất, địa chỉ IP, loại thiết bị và cổng SSH. |
| SSH hết thời gian chờ | Kiểm tra router đã chạy, giao diện quản trị, định tuyến, tường lửa và cổng SSH. |
| Xác thực SSH thất bại | Kiểm tra tài khoản, mật khẩu và cấu hình xác thực trên router. |
| Cấu hình trả về rỗng hoặc báo lỗi | Kiểm tra quyền tài khoản và khả năng thực thi lệnh `show running-config`. |
| Lỗi lưu lịch sử Git | Kiểm tra `git --version`, quyền ghi vào `config_history/` và thông báo lỗi trong nhật ký. |

## Bảo vệ dữ liệu

Thông tin đăng nhập được nhập khi chạy; không đưa mật khẩu vào mã nguồn hoặc danh sách thiết bị. Bản sao lưu có thể chứa thông tin xác thực và cấu trúc mạng, vì vậy cần kiểm soát quyền truy cập và nơi lưu trữ.

Các thư mục `backups/`, `config_history/`, `reports/`, `logs/` và các tệp bí mật được loại trừ qua `.gitignore`. Quy tắc này không loại bỏ dữ liệu đã được Git theo dõi từ trước; cần kiểm tra nội dung trước khi commit hoặc chia sẻ.

## Phạm vi và hướng phát triển

Mô hình hiện tại tập trung vào hai router Cisco IOS trong GNS3. Bộ kiểm tra YAML chấp nhận `juniper_junos`, nhưng quy trình sao lưu vẫn sử dụng lệnh Cisco `show running-config`; cần bổ sung lệnh theo nền tảng trước khi sử dụng với Juniper.

Các hướng phát triển dự kiến:

- Lập lịch sao lưu và gửi thông báo kết quả.
- Bổ sung giao diện quản trị và thống kê trạng thái thiết bị.
- Mở rộng hỗ trợ nhiều nền tảng mạng với lệnh thu thập tương ứng.
- Lọc các dòng cấu hình biến động và dữ liệu nhạy cảm.
- Đánh giá hiệu năng với số lượng thiết bị lớn hơn và bổ sung quản lý bí mật.

Mã nguồn được quản lý tại [GitHub của dự án](https://github.com/Jonny-Pak/network-config-backup-inventory); nhánh `develop` chứa các chức năng đã tích hợp.
