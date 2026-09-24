# Hệ thống Quản lý Tồn kho - Cache-Aside Pattern Simulation

## Giới thiệu
Bài tập mô phỏng hệ thống quản lý tồn kho tại Tiki sử dụng Cache-Aside Pattern với Python (giả lập Redis và Database thông qua in-memory storage và các Exception Handler).

## Tính năng
- Đọc tồn kho với luồng Cache-Aside (kiểm tra cache -> nếu miss lấy từ DB và nạp vào cache).
- Cập nhật tồn kho (cập nhật DB -> xóa cache).
- Xử lý tình huống biên: chặn số lượng âm.
- Xử lý sự cố Redis: Fallback xuống DB khi Redis lỗi đọc, và sử dụng TTL / cơ chế dự phòng khi Redis lỗi xóa.

## Hướng dẫn chạy chương trình
```bash
python main.py
```