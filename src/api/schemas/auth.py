"""Auth/login schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuthStartRequest(BaseModel):
    phone: str = Field(..., description="Phone number with country code, e.g. +855762923340")
    force: bool = Field(default=False, description="Force new login even if a session exists")
    headless: bool | None = Field(default=None, description="Override server default headless mode")
    proxy: str | None = Field(default=None, description="SOCKS5 proxy in format ip:port:username:password")
    run_name: str | None = Field(default=None, description="Optional run name for tracing/reports")


class AuthStartResponse(BaseModel):
    job_id: str
    status: str


class AuthSubmitOtpRequest(BaseModel):
    job_id: str
    otp: str = Field(..., min_length=4, max_length=10)


class AuthSubmit2FARequest(BaseModel):
    job_id: str
    password: str = Field(..., min_length=1, max_length=256)


class AuthStatusResponse(BaseModel):
    job_id: str
    status: str
    phone: str | None = None
    run_name: str | None = None
    error: str | None = None


