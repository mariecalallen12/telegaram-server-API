"""Contacts endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from telegram_bot.contacts import ContactManager
from telegram_bot.utils import extract_phone_number

from ..config import get_settings
from ..schemas.contacts import (
    AddContactRequest,
    AddContactResponse,
    CheckPhoneRequest,
    CheckPhoneResponse,
)
from ..services.browser_runner import browser_with_session

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/check-phone", response_model=CheckPhoneResponse)
async def check_phone(req: CheckPhoneRequest) -> CheckPhoneResponse:
    settings = get_settings()
    headless = req.headless if req.headless is not None else settings.default_headless

    try:
        async with browser_with_session(
            session_phone=req.session_phone,
            headless=headless,
            proxy=req.proxy,
            use_enhanced_browser=settings.use_enhanced_browser,
        ) as browser:
            mgr = ContactManager(browser)
            exists = await mgr.check_phone_exists(extract_phone_number(req.phone))
            return CheckPhoneResponse(exists=exists)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="session_not_found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=AddContactResponse)
async def add_contact(req: AddContactRequest) -> AddContactResponse:
    settings = get_settings()
    headless = req.headless if req.headless is not None else settings.default_headless

    try:
        async with browser_with_session(
            session_phone=req.session_phone,
            headless=headless,
            proxy=req.proxy,
            use_enhanced_browser=settings.use_enhanced_browser,
        ) as browser:
            mgr = ContactManager(browser)
            ok = await mgr.add_contact(
                extract_phone_number(req.phone),
                req.first_name,
                (req.last_name or "").strip(),
            )
            return AddContactResponse(success=ok)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="session_not_found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


