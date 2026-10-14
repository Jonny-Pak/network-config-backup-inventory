# Checklist nghiệm thu / bàn giao Thành viên 1

| ID | Kiểm tra | Kết quả hiện tại | Minh chứng đề xuất |
|---|---|---|---|
| NET-01 | VMware, GNS3 VM hoạt động | Đạt | Ảnh GNS3 VM |
| NET-02 | 2 router c3725 khởi động | Đạt | Console `show version` |
| NET-03 | R1/R2 có IP và thông mạng | Đạt | `show ip int brief`, ping 5/5 |
| NET-04 | VMnet1, GNS3 VM eth0, Cloud kết nối | Đạt | `ip -br addr`, topology |
| NET-05 | Windows mở cổng 22 router | Đạt với R1; R2 SSH được | `Test-NetConnection`, SSH prompt |
| NET-06 | SSH login R1/R2 | Đạt | Ảnh prompt (che thông tin nhạy cảm) |
| NET-07 | Netmiko lấy `show version` R1 | Đạt | Log `test_connection.py` |
| NET-08 | Python backup R1 & R2 | Đạt theo log chương trình | Log backup 2/2, tên file |
| NET-09 | Kiểm tra nội dung hai `.cfg` | Chưa có bằng chứng nội dung | Xác minh hostname và cấu hình, không đăng tải raw CFG |
| NET-10 | Đưa tài liệu và topology an toàn lên GitHub | Chưa thực hiện | Link PR/commit |

## Dữ liệu bàn giao cho TV2

- `config/devices.yaml`: danh sách 2 thiết bị và Netmiko `device_type=cisco_ios`.
- `network/ip-addressing.md`: sơ đồ / IP truy cập lab.
- Thông tin đăng nhập: trao đổi qua kênh riêng, không lưu trong Git.
- Python lab có thể cần `paramiko>=3.4,<4` với IOS 12.4; xác nhận đúng phiên bản đã chạy trong môi trường nhóm.

## Dữ liệu bàn giao cho TV3

- Kịch bản đổi `description` của FastEthernet0/0 trên R1 để kích hoạt diff.
- Tiêu chí test: backup lần 1, không thay đổi, thay đổi cấu hình, lỗi SSH, thiết bị down.
- Đề xuất lưu repo private; không commit backup có secret khi chưa redaction.

## Lưu trữ bằng chứng

Lưu ảnh minh chứng không chứa mật khẩu tại `network/gns3-topology/` hoặc thư mục ảnh riêng. Không commit ảnh màn hình có token hoặc dữ liệu nhạy cảm.
