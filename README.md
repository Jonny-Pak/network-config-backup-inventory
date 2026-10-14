# Network Configuration Backup & Inventory – Network Lab

**Môn học:** Quản trị mạng nâng cao  
**Đề tài:** Tự động hóa thu thập và sao lưu cấu hình Cisco/Juniper sử dụng Netmiko/Paramiko, phân tích diff và lưu trữ Git.  
**Phần bàn giao này:** Thành viên 1 – Hạ tầng GNS3/VMware/Cisco.

## Hiện trạng kiểm thử (14/10/2026)

- Hai router Cisco c3725 (IOS 12.4) hoạt động trong GNS3.
- IP quản trị: `192.168.36.11` (R1) và `192.168.36.12` (R2).
- Windows VMnet1: `192.168.36.1/24`, GNS3 VM eth0: `192.168.36.128/24`.
- Windows SSH thành công vào R1 và R2 bằng tài khoản `backupuser` (không lưu mật khẩu vào repository).
- Python Netmiko kết nối R1, lấy `show version` thành công; script backup chạy thành công hai thiết bị và tạo file `.cfg`.
- Chưa có thiết bị Juniper trong topology thực nghiệm hiện tại.

## Tài liệu

- [Địa chỉ IP và sơ đồ mạng](network/ip-addressing.md)
- [Các bước dựng lab / cấu hình SSH / kiểm tra](network/network-setup.md)
- [Inventory YAML](config/devices.yaml)
- [Checklist nghiệm thu và bàn giao](docs/handover-checklist.md)
- `network/gns3-topology/`: đặt file **project GNS3 đã kiểm tra không chứa image, secrets** hoặc ảnh chụp topology ở đây; hiện chưa có file project gốc vì chưa được cung cấp.

## Cách sử dụng với mã nguồn của nhóm

1. Cài Python và tạo `.venv` bằng `python -m venv .venv`.
2. Cài Netmiko trong `.venv`; thử Paramiko 3.x cho IOS 12.4 nếu Paramiko mới gây lỗi KEX.
3. Thành viên 2 bổ sung module load `config/devices.yaml`, không hard-code danh sách trong `backup.py`.
4. Chạy thử trên mạng host-only; giữ secret trong `.env` (không commit) hoặc nhập tương tác.
5. Không đẩy các file cấu hình router thực tế trong `backups/` lên GitHub khi chưa có redaction/kiểm soát truy cập.

## Phân công

| Người | Trách nhiệm |
|---|---|
| TV1 | GNS3, VMware, c3725, IP/SSH, topology và tài liệu mạng |
| TV2 | Python, Inventory parser, Netmiko, backup nhiều thiết bị |
| TV3 | Diff, Git commit, scheduler, báo cáo và kiểm thử tích hợp |

## GitHub

Dùng nhánh `feature/gns3-network` để gửi Pull Request vào `main`. Không commit `.venv`, mật khẩu, file backup gốc, Cisco image hoặc máy ảo. Đảm bảo xem `git status` và `git diff --cached` trước khi push.
