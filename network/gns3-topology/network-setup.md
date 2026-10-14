# Hướng dẫn triển khai hạ tầng – Thành viên 1

## 1. Mục tiêu

Cung cấp hai router Cisco c3725 chạy trên GNS3 và sẵn sàng phục vụ chương trình Python/Netmiko của nhóm: đăng nhập SSH, `show version`, `show running-config` và lưu tệp sao lưu.

## 2. Môi trường thực nghiệm

| Hạng mục | Mô tả |
|---|---|
| Máy chủ | Windows + VS Code |
| Ảo hóa | VMware Workstation; GNS3 VM |
| Giả lập | GNS3, Dynamips |
| Router | 2 × Cisco c3725, IOS 12.4(15)T14 ADVENTERPRISEK9 (theo output đã cung cấp) |
| Switch | GNS3 Ethernet switch `SW-MGMT` |
| Automation | Python / Netmiko / Paramiko (Paramiko 3.x dùng trong lab cũ) |
| SSH | TCP 22, `cisco_ios` Netmiko driver |

> Không chia sẻ image Cisco IOS lên GitHub. Việc sử dụng image cần tuân thủ quyền cấp phép.

## 3. Tạo topology GNS3

1. Mở GNS3 project `Network-Backup-Inventory`.
2. Tạo hai router c3725 (Dynamips) tên `R1-CISCO` và `R2-CISCO`.
3. Thêm Ethernet Switch tên `SW-MGMT`.
4. Nối `FastEthernet0/0` của mỗi router tới switch.
5. Tạo Cloud trên **GNS3 VM**, chọn interface **eth0** (VMnet1; đã xác nhận bằng `ip -br addr`).
6. Nối Cloud eth0 tới SW-MGMT. Không chọn eth1 NAT.
7. Lưu project, sau đó khởi động router và mở Console.

## 4. Mẫu cấu hình router R1 (đối chiếu với cấu hình đang chạy)

```cisco
conf t
hostname R1-CISCO
ip domain-name lab.local
username backupuser privilege 15 secret <MAT_KHAU_LAB_RIENG>
interface FastEthernet0/0
 description MANAGEMENT-NETWORK
 ip address 192.168.36.11 255.255.255.0
 no shutdown
exit
! Nếu chưa có SSH: tạo RSA key qua "crypto key generate rsa"
! IOS cũ có thể yêu cầu khóa RSA 1024-bit trong môi trường lab.
ip ssh version 2
line vty 0 4
 login local
 transport input ssh
end
write memory
```

R2 cấu hình tương tự nhưng thay `hostname R2-CISCO`, IP `192.168.36.12`.

> Đây là **mẫu tái lập**, không phải bản sao nguyên văn `show running-config`. Mật khẩu thật không ghi trong file này. IOS 12.4 và mật mã cũ chỉ dùng trong lab cô lập, không dùng production.

## 5. Kiểm tra trên router

Trên từng router:

```cisco
show ip interface brief
show ip ssh
show version
show running-config
```

Từ R1: `ping 192.168.36.12`; từ R2: `ping 192.168.36.11`.

## 6. Kiểm tra từ Windows

```powershell
ping 192.168.36.11
ping 192.168.36.12
Test-NetConnection 192.168.36.11 -Port 22
Test-NetConnection 192.168.36.12 -Port 22
```

SSH trên IOS cũ có thể chỉ đề xuất `diffie-hellman-group1-sha1`, `ssh-rsa`, `aes128-cbc`, `hmac-sha1`; dùng riêng cho phiên kết nối tới router trong mạng lab, không bật các thuật toán yếu trên toàn hệ thống:

```powershell
ssh -oKexAlgorithms=+diffie-hellman-group1-sha1 -oHostKeyAlgorithms=+ssh-rsa -oCiphers=+aes128-cbc -oMACs=+hmac-sha1 backupuser@192.168.36.11
```

Đổi IP thành `.12` cho R2. Không lưu mật khẩu trong lệnh hoặc tài liệu.

## 7. Kiểm thử Netmiko

- Tạo `.venv` riêng cho Python.
- Trong lab c3725 này, Paramiko 3.x đã giúp xử lý lỗi `no acceptable kex algorithm` với bản mới hơn; cần pin và kiểm thử tổ hợp phiên bản Netmiko–Paramiko trong nhóm, không khẳng định hỗ trợ mọi môi trường.
- Chạy `src/test_connection.py` và `src/backup.py` trên Windows; kết quả thực tế báo backup thành công cả 2 router ngày 14/10/2026.
- Tránh push cấu hình nguyên gốc, mật khẩu, khóa SSH hoặc địa chỉ thông tin quản trị nhạy cảm ra repository công khai.

## 8. Sự cố và hướng xử lý

| Vấn đề | Kiểm tra / xử lý |
|---|---|
| IOSv không chạy | KVM bị giới hạn; dùng c3725/Dynamips để tránh nested virtualization |
| Router không ping | IP, mask, cáp, `no shutdown`, cùng switch, IP trùng |
| Windows không thấy router | Cloud server GNS3 VM, interface eth0, VMnet1, firewall, DHCP |
| SSH port 22 đóng | `show ip ssh`, username, RSA key, VTY transport |
| SSH OpenSSH báo mismatch | IOS cũ, bật thuật toán tương thích riêng cho phiên SSH lab |
| Netmiko báo KEX | Kiểm tra Paramiko; bản 3.x đã hoạt động trong lab |
| Netmiko báo authentication | Kiểm tra username/password riêng trên cả hai router |
| Backup file rỗng/thiếu | Kiểm tra `show running-config`, timeout và phân trang |

## 9. Kết quả nghiệm thu đã xác nhận

- R1/R2 ping được nhau (đã gửi output 5/5).
- Windows đăng nhập SSH vào R1 và R2 (đã kiểm tra).
- `test_connection.py` Netmiko thành công với R1, lấy `show version`.
- `backup.py` chạy thành công R1, R2 và tạo file CFG được báo tên từ chương trình.

## 10. Công việc tiếp theo

- Thành viên 2: đọc `config/devices.yaml` thay cho danh sách IP viết cứng; chuẩn hóa backup, xử lý lỗi và báo cáo.
- Thành viên 3: quản lý Git, diff, scheduling; thiết kế redaction/an toàn backup trước khi đưa snapshot vào Git riêng tư.
