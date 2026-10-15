# Network Configuration Backup & Inventory

**Hệ thống tự động hóa thu thập, sao lưu và quản lý lịch sử cấu hình thiết bị mạng**

Đồ án môn học: **Quản trị mạng nâng cao**

## 1. Giới thiệu dự án

Network Configuration Backup & Inventory là hệ thống được phát triển bằng Python nhằm tự động hóa quá trình quản lý thông tin thiết bị mạng, kết nối SSH, sao lưu cấu hình và theo dõi các thay đổi cấu hình.

Hệ thống sử dụng **Netmiko** để kết nối đến router Cisco, hỗ trợ sao lưu đồng thời nhiều thiết bị, tự động phát hiện thay đổi giữa các phiên bản cấu hình và lưu lịch sử thay đổi bằng Git.

Ngoài ra, hệ thống hỗ trợ ghi nhật ký hoạt động và xuất báo cáo CSV, giúp người quản trị theo dõi tình trạng sao lưu cũng như kiểm tra lịch sử cấu hình của từng thiết bị.

### Mục tiêu

- Tự động thu thập cấu hình thiết bị mạng thông qua SSH.
- Quản lý danh sách thiết bị bằng Inventory.
- Sao lưu cấu hình nhiều thiết bị đồng thời.
- Phát hiện thay đổi giữa các bản sao lưu.
- Quản lý phiên bản cấu hình bằng Git.
- Ghi nhật ký và xử lý lỗi khi thiết bị không kết nối được.
- Xuất báo cáo CSV phục vụ quản trị và kiểm thử.

## 2. Công nghệ sử dụng

| Công nghệ | Vai trò |
|---|---|
| Python | Ngôn ngữ lập trình chính |
| Netmiko | Kết nối SSH và thu thập cấu hình Cisco |
| PyYAML | Đọc danh sách thiết bị trong Inventory |
| ThreadPoolExecutor | Sao lưu nhiều thiết bị đồng thời |
| difflib | So sánh cấu hình và phát hiện thay đổi |
| Git | Lưu lịch sử phiên bản cấu hình |
| CSV | Xuất báo cáo kết quả |
| logging | Ghi nhật ký hoạt động |
| unittest | Kiểm thử tự động |
| GNS3 | Mô phỏng hệ thống mạng |
| Cisco IOS | Hệ điều hành router mô phỏng |
| VMware | Cung cấp môi trường mạng ảo |
| Visual Studio Code | Môi trường phát triển |

## 3. Kiến trúc hệ thống

Quy trình hoạt động:

```text
           NETWORK INVENTORY
             devices.yaml
                  |
                  v
            SSH CONNECTION
              Netmiko
                  |
                  v
             BACKUP MANAGER
          ThreadPoolExecutor
                  |
                  v
            CONFIGURATION DIFF
                  |
                  v
             CHANGE DETECTION
                  |
                  v
              GIT AUTOMATION
                  |
                  v
              CSV REPORTING
                  |
                  v
               reports/
```

Hệ thống thực hiện các bước:

1. Đọc thông tin thiết bị từ Inventory.
2. Nhập thông tin xác thực SSH.
3. Kết nối và sao lưu cấu hình các router.
4. So sánh cấu hình mới với phiên bản trước.
5. Phát hiện trạng thái `CHANGED` hoặc `UNCHANGED`.
6. Lưu cấu hình thay đổi vào Git repository cục bộ.
7. Xuất báo cáo tổng hợp sang định dạng CSV.

## 4. Mô hình mạng thử nghiệm

Hệ thống được thử nghiệm trên GNS3 với hai router Cisco.

```text
                   WINDOWS HOST
                    Python App
                  192.168.36.1
                        |
                   VMware VMnet1
                        |
                    GNS3 Cloud
                        |
                     SW-MGMT
                     /     \
                    /       \
               R1-CISCO   R2-CISCO
             192.168.36.11 192.168.36.12
                  SSH 22     SSH 22
```

### Thông tin thiết bị

| Thiết bị | IP quản trị | Loại thiết bị | Giao thức |
|---|---|---|---|
| R1-CISCO | 192.168.36.11 | Cisco IOS | SSH / TCP 22 |
| R2-CISCO | 192.168.36.12 | Cisco IOS | SSH / TCP 22 |

Môi trường thử nghiệm sử dụng router Cisco c3725 với IOS 12.4 trong GNS3 và mạng Host-only VMware VMnet1.

**Lưu ý:** Các địa chỉ IP trên chỉ là địa chỉ private trong môi trường mô phỏng. Khi triển khai trên môi trường khác, cần điều chỉnh Inventory và cấu hình kết nối cho phù hợp.

## 5. Cấu trúc thư mục dự án

```text
network-config-backup-inventory/
|
|-- config/
|   |-- devices.yaml
|
|-- src/
|   |-- __init__.py
|   |-- main.py
|   |-- inventory.py
|   |-- ssh_connector.py
|   |-- backup_manager.py
|   |-- config_diff.py
|   |-- change_detector.py
|   |-- git_manager.py
|   |-- report_manager.py
|   |-- logger_config.py
|   |-- backup.py
|   |-- test_connection.py
|   |-- test_ssh.py
|
|-- tests/
|   |-- fixtures/
|   |   |-- r1_old.cfg
|   |   |-- r1_new.cfg
|   |
|   |-- test_inventory.py
|   |-- test_backup_manager.py
|   |-- test_config_diff.py
|   |-- test_change_detector.py
|   |-- test_git_manager.py
|   |-- test_report_manager.py
|
|-- network/
|-- backups/
|-- config_history/
|-- reports/
|-- logs/
|
|-- .gitignore
|-- README.md
```

Các thư mục `backups/`, `config_history/`, `reports/` và `logs/` được tạo hoặc sử dụng trong quá trình chạy và không được đưa lên repository mã nguồn công khai.

## 6. Hướng dẫn cài đặt

### 6.1. Yêu cầu môi trường

- Windows 10 hoặc Windows 11.
- Python 3.9 trở lên trong phạm vi tương thích của các thư viện.
- Git.
- Visual Studio Code.
- GNS3.
- Router Cisco hoặc thiết bị SSH được cấp quyền quản trị.
- Kết nối mạng từ máy chạy Python đến các thiết bị.

### 6.2. Clone repository

Mở PowerShell:

```powershell
git clone https://github.com/Jonny-Pak/network-config-backup-inventory.git

cd network-config-backup-inventory
```

### 6.3. Tạo môi trường Python

```powershell
python -m venv .venv
```

Kích hoạt môi trường:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn chạy script, có thể kích hoạt bằng Command Prompt hoặc điều chỉnh chính sách thực thi phù hợp với máy tính.

### 6.4. Cài đặt thư viện

Các thư viện bên ngoài chính được sử dụng:

```powershell
python -m pip install netmiko PyYAML
```

Những thư viện như `csv`, `difflib`, `logging`, `subprocess`, `pathlib` và `unittest` có sẵn trong Python.

Nếu repository có file `requirements.txt` được duy trì đầy đủ, nên sử dụng:

```powershell
python -m pip install -r requirements.txt
```

Đảm bảo Git có thể được gọi từ Terminal:

```powershell
git --version
```

## 7. Cấu hình Inventory

Danh sách thiết bị được quản lý tại:

```text
config/devices.yaml
```

Trong môi trường thử nghiệm, Inventory chứa hai thiết bị:

| Name | Host | Device Type | Port |
|---|---|---|---|
| R1-CISCO | 192.168.36.11 | cisco_ios | 22 |
| R2-CISCO | 192.168.36.12 | cisco_ios | 22 |

Khi thêm thiết bị mới, cập nhật file YAML theo cấu trúc mà `src/inventory.py` hỗ trợ.

Không lưu mật khẩu SSH trực tiếp trong Inventory hoặc đẩy thông tin đăng nhập lên GitHub.

## 8. Hướng dẫn chạy chương trình

### 8.1. Chuẩn bị thiết bị GNS3

Khởi động hai router và bảo đảm:

- Router đã được cấu hình địa chỉ IP quản trị.
- Interface quản trị hoạt động.
- SSH đã được bật và cấu hình xác thực.
- Máy Windows có thể kết nối đến thiết bị qua mạng quản trị.

Kiểm tra cổng SSH bằng PowerShell:

```powershell
Test-NetConnection 192.168.36.11 -Port 22
Test-NetConnection 192.168.36.12 -Port 22
```

Kết quả mong đợi:

```text
TcpTestSucceeded : True
```

Đây chỉ là kiểm tra cổng TCP; việc xác thực SSH cần được kiểm chứng riêng.

### 8.2. Chạy chương trình chính

Tại thư mục gốc dự án:

```powershell
python .\src\main.py
```

Chương trình hiển thị danh sách thiết bị và yêu cầu thông tin đăng nhập SSH.

Sau đó, hệ thống tự động thực hiện Backup, Change Detection, Git Automation và CSV Reporting.

## 9. Các chức năng chính

### 9.1. Inventory Management

Đọc danh sách thiết bị từ file YAML, kiểm tra dữ liệu và hiển thị:

- Tên thiết bị.
- Địa chỉ IP.
- Loại thiết bị.
- Cổng SSH.

### 9.2. SSH Configuration Backup

Kết nối tới thiết bị Cisco bằng Netmiko và thu thập `running-config`.

Hỗ trợ sao lưu đồng thời thông qua `ThreadPoolExecutor`.

Ví dụ:

```text
===== BACKUP REPORT =====
R1-CISCO: SUCCESS
R2-CISCO: SUCCESS

Tổng thiết bị: 2
Thành công: 2
Thất bại: 0
```

Các bản sao lưu được lưu vào thư mục:

```text
backups/
```

Ví dụ tên file:

```text
R1-CISCO_20261015_220125.cfg
R2-CISCO_20261015_220125.cfg
```

### 9.3. Configuration Diff

Sử dụng thư viện Python `difflib` để so sánh cấu hình cũ với cấu hình mới.

Ví dụ:

```diff
 interface FastEthernet0/0
- description MANAGEMENT-NETWORK
+ description CONFIG-CHANGED-TEST
```

Chương trình hiển thị những dòng được thêm, xóa hoặc thay đổi giữa hai phiên bản.

### 9.4. Change Detection

Hệ thống hỗ trợ các trạng thái:

| Trạng thái | Ý nghĩa |
|---|---|
| CHANGED | Cấu hình thay đổi |
| UNCHANGED | Cấu hình không thay đổi |
| FIRST_BACKUP | Chỉ có một phiên bản backup |
| NO_BACKUP | Không tìm thấy bản backup |
| SKIPPED | Bỏ qua vì backup thất bại |

### 9.5. Git Automation

Sau khi backup thành công, hệ thống lưu phiên bản cấu hình vào Git repository cục bộ tại:

```text
config_history/
```

Cơ chế hoạt động:

- Nếu chưa có phiên bản cấu hình, tạo commit đầu tiên.
- Nếu cấu hình thay đổi, tạo commit mới.
- Nếu cấu hình không thay đổi, không tạo commit trùng.
- Nếu backup thất bại, bỏ qua thao tác Git cho thiết bị đó.

Ví dụ:

```text
===== GIT AUTOMATION REPORT =====
[GIT COMMITTED] R1-CISCO
[GIT UNCHANGED] R2-CISCO
```

Kiểm tra lịch sử:

```powershell
git -C config_history log --oneline
```

Kiểm tra riêng thiết bị:

```powershell
git -C config_history log --oneline -- R1-CISCO.cfg
```

**Quan trọng:** Repository lịch sử cấu hình chỉ được sử dụng cục bộ trong phạm vi thử nghiệm. Hệ thống không tự động push nội dung backup lên GitHub.

### 9.6. CSV Reporting

Sau mỗi lần chạy, hệ thống xuất báo cáo CSV vào:

```text
reports/
```

Báo cáo có các trường:

| Trường | Mô tả |
|---|---|
| Device | Tên thiết bị |
| IP | Địa chỉ IP quản trị |
| Backup Status | Trạng thái backup |
| Change Status | Trạng thái thay đổi cấu hình |
| Git Status | Kết quả Git Automation |
| Commit | Mã Git commit mới, nếu có |
| Error | Thông tin lỗi, nếu có |

Ví dụ:

```csv
Device,IP,Backup Status,Change Status,Git Status,Commit,Error
R1-CISCO,192.168.36.11,SUCCESS,UNCHANGED,UNCHANGED,,
R2-CISCO,192.168.36.12,SUCCESS,UNCHANGED,UNCHANGED,,
```

File CSV được mã hóa UTF-8 có BOM để hỗ trợ hiển thị tiếng Việt trong Excel.

### 9.7. Logging và xử lý lỗi

Hệ thống ghi lại các hoạt động như:

- Bắt đầu và kết thúc backup.
- Kết nối SSH thành công hoặc thất bại.
- Kết quả sao lưu cấu hình.
- Phát hiện thay đổi.
- Tạo Git commit.
- Xuất báo cáo CSV.

Thiết bị gặp lỗi SSH không ngăn chương trình tiếp tục xử lý những thiết bị còn lại.

## 10. Kiểm thử hệ thống

Dự án sử dụng Python `unittest`.

Chạy toàn bộ bài kiểm thử:

```powershell
python -m unittest discover -s tests -v
```

### Kết quả kiểm thử đã thực hiện

| Module | Số bài kiểm thử | Kết quả |
|---|---:|---|
| Inventory | 3 | PASS |
| Backup Manager | 4 | PASS |
| Configuration Diff | 4 | PASS |
| Change Detection | 4 | PASS |
| Git Automation | 5 | PASS |
| CSV Reporting | 4 | PASS |
| **Tổng cộng** | **24** | **PASS** |

Kết quả ghi nhận trong môi trường thử nghiệm:

```text
Ran 24 tests in 2.420s

OK
```

Ngoài Unit Test, hệ thống đã được thử nghiệm trên hai router Cisco trong GNS3 với các tình huống:

- Backup thành công cả hai router.
- Thiết bị gặp lỗi SSH timeout.
- Phát hiện cấu hình thay đổi.
- Phát hiện cấu hình không thay đổi.
- Tạo Git commit khi cấu hình thay đổi.
- Không tạo commit trùng.
- Xuất báo cáo CSV thành công.

## 11. Phân công thành viên

| Thành viên | Công việc |
|---|---|
| Thành viên 1 | Thiết kế mô hình mạng GNS3, cấu hình Cisco Router, SSH và kết nối mạng quản trị |
| Thành viên 2 | Inventory Manager, SSH Connector, Backup Manager, Multi-threading và Logging |
| Thành viên 3 | Configuration Diff, Change Detection, Git Automation, Change History và CSV Reporting |

Các chức năng được phát triển theo nhánh riêng và hợp nhất vào nhánh `main` qua Git.

## 12. Bảo mật dữ liệu

Các bản backup cấu hình có thể chứa thông tin nhạy cảm như mật khẩu, khóa xác thực, thông tin giao diện và cấu trúc mạng.

Do đó:

- Không lưu thông tin đăng nhập trực tiếp trong mã nguồn.
- Không commit file `.env` chứa bí mật.
- Không push bản backup thực tế lên repository công khai.
- Không push thư mục Git history chứa cấu hình thiết bị.
- Chỉ sử dụng thiết bị thuộc môi trường được cấp quyền quản trị.
- Kiểm tra dữ liệu nhạy cảm trước khi lưu lịch sử cấu hình lâu dài.

Những thư mục được loại trừ khỏi repository mã nguồn:

```gitignore
/backups/
/config_history/
/logs/
/reports/
```

Lưu ý: `.gitignore` không bảo vệ các file đã được Git theo dõi hoặc đưa vào commit từ trước.

## 13. Kết quả đạt được

Dự án đã triển khai và kiểm thử được các chức năng:

- Quản lý danh sách thiết bị mạng.
- Kết nối SSH đến Cisco Router.
- Tự động backup cấu hình.
- Sao lưu nhiều thiết bị đồng thời.
- Phát hiện sự thay đổi cấu hình.
- Lưu lịch sử phiên bản bằng Git.
- Xuất báo cáo CSV.
- Ghi nhật ký và xử lý lỗi.
- Hoàn thành 24 bài Unit Test.

## 14. Hạn chế và hướng phát triển

### Hạn chế

- Môi trường thử nghiệm hiện gồm hai router Cisco trong GNS3.
- Chưa đánh giá hiệu năng trên mạng sản xuất hoặc số lượng lớn thiết bị.
- Việc so sánh cấu hình dựa trên nội dung văn bản, có thể ghi nhận cả những thay đổi không mang ý nghĩa cấu hình.
- Chưa có giao diện web quản trị.
- Chưa có lịch sao lưu tự động.
- Chưa triển khai hệ thống quản lý bí mật chuyên dụng.

### Hướng phát triển

- Tự động backup theo lịch.
- Gửi thông báo qua email hoặc Telegram.
- Xây dựng dashboard quản trị.
- Hỗ trợ thêm switch, router và firewall từ nhiều nhà sản xuất.
- Lưu trữ cấu hình đã được bảo vệ trong hệ thống quản lý phiên bản riêng tư.
- Nâng cao khả năng lọc dữ liệu nhạy cảm.
- Bổ sung thống kê hiệu năng và tỷ lệ backup thành công.

## 15. Repository

GitHub:

https://github.com/Jonny-Pak/network-config-backup-inventory

Dự án được xây dựng nhằm phục vụ học tập, nghiên cứu và thực hành tự động hóa quản trị mạng trong môi trường mô phỏng.