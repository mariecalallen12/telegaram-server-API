"""Session management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from telegram_bot.session import SessionManager
from telegram_bot.utils import extract_phone_number

from ..schemas.sessions import SessionDeleteResponse, SessionListResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions() -> SessionListResponse:
    sm = SessionManager()
    return SessionListResponse(sessions=sm.list_sessions())


@router.delete("/{phone}", response_model=SessionDeleteResponse)
async def delete_session(phone: str) -> SessionDeleteResponse:
    sm = SessionManager()
    phone = extract_phone_number(phone)
    deleted = sm.delete_session(phone)
    if not deleted:
        raise HTTPException(status_code=404, detail="session_not_found")
    return SessionDeleteResponse(deleted=True)


