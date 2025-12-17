# Architecture

## Overview
Hệ thống được tách thành 2 lớp:
- `src/telegram_bot/`: domain/library (Playwright automation, session, reports, notes).
- `src/api/`: FastAPI server bọc các use-case thành REST API.

## Login job flow (OTP/2FA via API)

```mermaid
sequenceDiagram
participant Client
participant API as FastAPI
participant JM as JobManager
participant Browser as Browser
participant TG as TelegramWeb

Client->>API: POST /auth/start
API->>JM: create_login_job()
JM->>Browser: launch()
Browser->>TG: goto_telegram()
JM-->>API: status=waiting_for_otp (job_id)

Client->>API: POST /auth/submit-otp
API->>JM: submit_otp(job_id, otp)
JM->>TG: enter_otp(otp)
alt 2FA required
JM-->>API: status=waiting_for_2fa
Client->>API: POST /auth/submit-2fa
API->>JM: submit_2fa(job_id, password)
JM->>TG: handle_2fa(password)
end
JM->>Browser: get_storage_state()
JM->>JM: save_session()
JM-->>API: status=completed
```

## Stateless endpoints (contacts/groups)
Các endpoint như `/contacts/*`, `/groups/*` chạy theo kiểu “stateless”:
- Load session file trong `sessions/`
- Mở browser -> load context -> thực thi -> đóng browser

Điểm này giúp API dễ vận hành hơn (mỗi request độc lập) nhưng sẽ tốn chi phí mở browser.


