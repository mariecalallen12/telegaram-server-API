# telegaram-server-API

## Telegram Automation Tool

Tool tự động hóa các thao tác trên Telegram Web sử dụng Playwright.

## Server API (FastAPI)

Repo hiện hỗ trợ chạy như **Server API** (Swagger/OpenAPI):
- Tài liệu: `docs/API.md`
- Swagger UI: `/docs`

Chạy nhanh:

```bash
pip install -r requirements.txt
playwright install chromium
python -m uvicorn api.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

## Tính năng

### Core Features
- ✅ Đăng nhập với số điện thoại và OTP
- ✅ Lưu và tái sử dụng session
- ✅ Kiểm tra số điện thoại có Telegram không
- ✅ Thêm bạn/contact
- ✅ Tạo nhóm
- ✅ Quản lý nhóm (thêm thành viên, liệt kê nhóm)

### Enhanced Features (tích hợp từ Strix)
- ✅ **Tab Management:** Quản lý nhiều tabs đồng thời
- ✅ **Telemetry & Tracing:** Tracking tất cả operations tự động
- ✅ **Notes Management:** Ghi chú và quản lý findings
- ✅ **Reporting System:** Tự động generate reports
- ✅ **Console Logs:** Capture và analyze console logs
- ✅ **Screenshots:** Tự động capture screenshots cho mỗi operation
- ✅ **Statistics:** Theo dõi performance và success rate

## Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Cấu hình (tùy chọn)

Tạo file `.env` và cấu hình các biến môi trường:

```bash
# Browser Configuration
# Sử dụng Enhanced Browser với tab management (mặc định: true)
USE_ENHANCED_BROWSER=true

# SOCKS5 Proxy Configuration (tùy chọn)
# Định dạng: ip:port:username:password
# Ví dụ: PROXY_SOCKS5=160.187.240.180:38102:ypMH7pF:b7Dnr
PROXY_SOCKS5=

# Optional: Browser timeout settings (in milliseconds)
# BROWSER_TIMEOUT=30000

# Optional: Logging level (DEBUG, INFO, WARNING, ERROR)
# LOG_LEVEL=INFO

# Optional: Custom paths
# SESSIONS_DIR=sessions
# NOTES_DIR=notes
# REPORTS_DIR=reports
# TELEGRAM_RUNS_DIR=telegram_runs
```

## Sử dụng

Repo đã chuyển sang mô hình **Server API**. Xem ví dụ gọi API trong `docs/API.md` hoặc mở Swagger UI tại `/docs`.

## Desktop/Installer

Phần Desktop GUI/Installer đã được **loại bỏ khỏi repo** để tập trung vào hệ thống **Server API**.

## Cấu trúc dự án

```
telegram-automation/
├── src/
│   ├── telegram_bot/
│   │   ├── __init__.py
│   │   ├── browser.py          # Browser management
│   │   ├── session.py          # Session management
│   │   ├── login.py            # Login flow
│   │   ├── contacts.py         # Contact operations
│   │   ├── groups.py           # Group operations
│   │   └── utils.py            # Utilities
│   └── cli.py                  # CLI interface
├── docs/                       # Server API docs
├── scripts/                    # Maintenance scripts (cleanup, etc.)
├── run_api.py                  # API entrypoint (from source)
├── sessions/                   # Saved sessions (auto-created)
├── requirements.txt
└── README.md
```

## Lưu ý quan trọng

1. **Telegram Anti-Bot:** Telegram có thể phát hiện automation. Tool này sử dụng các kỹ thuật để giảm thiểu phát hiện, nhưng không đảm bảo 100%.

2. **Session Management:** Session được lưu trong thư mục `sessions/`. Mỗi số điện thoại có một file session riêng.

3. **OTP Input:** Khi đăng nhập, bạn sẽ được yêu cầu nhập OTP trong terminal. Tool sẽ chờ tối đa 5 phút.

4. **Browser Mode:** Mặc định browser chạy ở chế độ visible (`headless=False`) để dễ debug và nhập OTP. Có thể dùng `--headless` flag để chạy headless.

5. **UI Changes:** Telegram Web có thể thay đổi UI. Nếu tool không hoạt động, có thể cần cập nhật selectors trong code.

## Troubleshooting

### Browser không mở

- Đảm bảo đã cài đặt Playwright: `playwright install chromium`
- Kiểm tra dependencies: `pip install -r requirements.txt`

### Login thất bại

- Kiểm tra số điện thoại đúng format (có country code, ví dụ: +855762923340)
- Đảm bảo OTP được nhập đúng và kịp thời
- Thử xóa session cũ và đăng nhập lại: Xóa file trong `sessions/` hoặc dùng `--force`

### Không tìm thấy elements

- Telegram có thể đã thay đổi UI
- Thử chạy với `headless=False` để xem browser và debug
- Kiểm tra logs để xem lỗi cụ thể

## License

MIT
