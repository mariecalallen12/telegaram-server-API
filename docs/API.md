# API Usage (Telegram Automation API)

Swagger/OpenAPI: mở `http://<host>:<port>/docs`

## Run server (dev)

```bash
pip install -r requirements.txt
playwright install chromium
python -m uvicorn api.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

Hoặc chạy bằng entrypoint tiện dụng (tự add `src/` vào `PYTHONPATH`):

```bash
python run_api.py
```

## Auth flow (OTP/2FA qua API)

### 1) Start login

```bash
curl -X POST http://127.0.0.1:8000/auth/start ^
  -H "Content-Type: application/json" ^
  -d "{\"phone\":\"+855762923340\",\"force\":false,\"headless\":true}"
```

Response (ví dụ):
- `status=waiting_for_otp`: cần submit OTP
- `status=completed`: đã login (dùng saved session)

### 2) Poll status

```bash
curl http://127.0.0.1:8000/auth/status/<job_id>
```

### 3) Submit OTP

```bash
curl -X POST http://127.0.0.1:8000/auth/submit-otp ^
  -H "Content-Type: application/json" ^
  -d "{\"job_id\":\"<job_id>\",\"otp\":\"12345\"}"
```

Nếu trả `waiting_for_2fa` thì tiếp tục bước 4.

### 4) Submit 2FA (nếu cần)

```bash
curl -X POST http://127.0.0.1:8000/auth/submit-2fa ^
  -H "Content-Type: application/json" ^
  -d "{\"job_id\":\"<job_id>\",\"password\":\"your_2fa_password\"}"
```

## Sessions

- `GET /sessions`
- `DELETE /sessions/{phone}`

## Contacts

### Check phone exists

```bash
curl -X POST http://127.0.0.1:8000/contacts/check-phone ^
  -H "Content-Type: application/json" ^
  -d "{\"phone\":\"+1234567890\",\"session_phone\":\"+855762923340\"}"
```

### Add contact

```bash
curl -X POST http://127.0.0.1:8000/contacts/add ^
  -H "Content-Type: application/json" ^
  -d "{\"phone\":\"+1234567890\",\"first_name\":\"John\",\"last_name\":\"Doe\",\"session_phone\":\"+855762923340\"}"
```

## Groups

- `POST /groups/create`
- `POST /groups/add-members`
- `GET /groups/list?session_phone=...`
- `GET /groups/info?session_phone=...&group_name=...`

## Runs / Reports

- `GET /runs`
- `GET /runs/{run_name}`
- `GET /reports`

## Notes

- `POST /notes`
- `GET /notes`
- `GET /notes/{note_id}`
- `PATCH /notes/{note_id}`
- `DELETE /notes/{note_id}`


