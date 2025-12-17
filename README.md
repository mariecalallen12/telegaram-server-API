# Telegram Automation API (FastAPI + Playwright)

Server API (FastAPI) để tự động hoá các thao tác trên **Telegram Web** bằng **Playwright**.

- **Swagger/OpenAPI**: `/docs`
- **Tài liệu usage**: `docs/API.md`
- **Kiến trúc**: `docs/ARCHITECTURE.md`
- **Runbook/triển khai**: `docs/DEPLOYMENT.md`

## Tính năng chính

- **Auth/login flow qua API**: start login → submit OTP → (tuỳ chọn) submit 2FA → lưu session.
- **Sessions**: liệt kê/xoá session theo số điện thoại.
- **Contacts**: check số có Telegram, add contact.
- **Groups**: tạo nhóm, add members, list groups, group info.
- **Runs/Reports/Notes**: lưu vết chạy và artefacts phục vụ theo dõi/debug.

## Cài đặt

Yêu cầu:
- Python 3.10+ (khuyến nghị)

Cài dependencies và browser:

```bash
pip install -r requirements.txt
playwright install chromium
```

## Chạy server

Dev (hot reload):

```bash
python -m uvicorn api.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

Hoặc chạy entrypoint tiện dụng (tự thêm `src/` vào `PYTHONPATH`):

```bash
python run_api.py
```

## Cấu hình (tuỳ chọn)

Tạo file `.env` để cấu hình (ví dụ):

```bash
USE_ENHANCED_BROWSER=true
PROXY_SOCKS5=
LOG_LEVEL=INFO
```

## API nhanh

Xem ví dụ chi tiết trong `docs/API.md`. Tóm tắt endpoints:

- **Health/Version**: `GET /health`, `GET /version`
- **Auth**: `POST /auth/start`, `GET /auth/status/{job_id}`, `POST /auth/submit-otp`, `POST /auth/submit-2fa`
- **Sessions**: `GET /sessions`, `DELETE /sessions/{phone}`
- **Contacts**: `POST /contacts/check-phone`, `POST /contacts/add`
- **Groups**: `POST /groups/create`, `POST /groups/add-members`, `GET /groups/list`, `GET /groups/info`
- **Runs/Reports**: `GET /runs`, `GET /runs/{run_name}`, `GET /reports`
- **Notes**: `POST /notes`, `GET /notes`, `GET /notes/{note_id}`, `PATCH /notes/{note_id}`, `DELETE /notes/{note_id}`

## Cấu trúc dự án

```
telegram-automation/
├── src/
│   ├── api/                    # FastAPI server (routers/schemas/services)
│   └── telegram_bot/           # Automation domain (Playwright, sessions, reports, notes)
├── docs/                       # API/Architecture/Deployment docs
├── scripts/                    # Maintenance scripts
├── run_api.py                  # Entrypoint chạy từ source
├── requirements.txt
└── README.md
```

## Lưu ý vận hành

- **Telegram UI thay đổi**: selectors có thể cần cập nhật theo Telegram Web.
- **Dữ liệu runtime**: `sessions/`, `notes/`, `reports/`, `telegram_runs/` là thư mục runtime (đã được ignore trong `.gitignore`).
- **Chạy trên Windows/service**: đảm bảo working directory là root project để đường dẫn tương đối hoạt động đúng (xem `docs/DEPLOYMENT.md`).

## License

MIT
