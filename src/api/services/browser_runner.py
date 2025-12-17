"""Helpers for executing an operation with a loaded Telegram session."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, Optional

from telegram_bot.browser import TelegramBrowser
from telegram_bot.browser.browser_adapter import EnhancedBrowserAdapter
from telegram_bot.session import SessionManager
from telegram_bot.utils import extract_phone_number

logger = logging.getLogger(__name__)


@asynccontextmanager
async def browser_with_session(
    *,
    session_phone: str,
    headless: bool,
    proxy: str | None,
    use_enhanced_browser: bool,
    sessions_dir: str = "sessions",
) -> AsyncIterator[Any]:
    """Create a browser, load storage_state from the given session, and yield it.

    The browser is always closed at the end.
    """
    session_phone = extract_phone_number(session_phone)
    session_manager = SessionManager(sessions_dir=sessions_dir)
    session_data = session_manager.load_session(session_phone)
    if not session_data:
        raise FileNotFoundError(f"No session found for {session_phone}")

    browser: Any = (
        EnhancedBrowserAdapter(headless=headless, proxy=proxy)
        if use_enhanced_browser
        else TelegramBrowser(headless=headless)
    )

    try:
        await browser.launch()
        await browser.load_context(session_data["storage_state"])
        await browser.goto_telegram()
        yield browser
    finally:
        try:
            await browser.close()
        except Exception:
            logger.exception("Failed to close browser cleanly")


