# Deployment / Runbook

## Prerequisites
- Python 3.10+ (khuyến nghị)
- Playwright browser: `playwright install chromium`

## Environment variables
Các biến quan trọng (đặt trong `.env`):

- `USE_ENHANCED_BROWSER=true|false`
- `PROXY_SOCKS5=ip:port:user:pass` (tuỳ chọn)
- `LOG_LEVEL=INFO` (tuỳ chọn)

## Run (dev)

```bash
python -m uvicorn api.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

## Run (prod - basic)

```bash
python -m uvicorn api.main:app --app-dir src --host 0.0.0.0 --port 8000
```

## Windows notes
- Nên chạy dưới account có quyền mở Chromium và ghi file vào `sessions/`, `reports/`, `telegram_runs/`, `notes/`.
- Nếu chạy dạng service, đảm bảo working directory là root project để đường dẫn tương đối hoạt động đúng.

## Operational notes
- Automation dùng Telegram Web selectors: nếu Telegram đổi UI, cần cập nhật selectors trong `src/telegram_bot/*`.
- Giới hạn concurrency: hiện job login giữ browser trong RAM theo process; tránh tạo quá nhiều job song song trên máy yếu.


