"""Utility functions for Telegram automation."""

import asyncio
import logging
import re
import time
from functools import wraps
from typing import Any, Callable

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class ElementNotFoundError(Exception):
    """Raised when an element is not found on the page."""

    pass


class LoginError(Exception):
    """Raised when login fails."""

    pass


class SessionExpiredError(Exception):
    """Raised when session has expired."""

    pass


async def wait_for_selector(
    page: Page, selector: str, timeout: int = 30000, visible: bool = True
) -> Any:
    """
    Wait for a selector to appear on the page.

    Args:
        page: Playwright page object
        selector: CSS selector or text selector
        timeout: Maximum time to wait in milliseconds
        visible: Whether to wait for element to be visible

    Returns:
        ElementHandle if found

    Raises:
        ElementNotFoundError: If element is not found within timeout
    """
    try:
        if visible:
            element = await page.wait_for_selector(selector, timeout=timeout, state="visible")
        else:
            element = await page.wait_for_selector(selector, timeout=timeout)
        return element
    except PlaywrightTimeoutError as e:
        logger.error(f"Element not found: {selector}")
        raise ElementNotFoundError(f"Element not found: {selector}") from e


async def safe_click(page: Page, selector: str, timeout: int = 30000, retries: int = 3) -> bool:
    """
    Safely click an element with retry logic.

    Args:
        page: Playwright page object
        selector: CSS selector or text selector
        timeout: Maximum time to wait in milliseconds
        retries: Number of retry attempts

    Returns:
        True if click was successful
    """
    for attempt in range(retries):
        try:
            element = await wait_for_selector(page, selector, timeout=timeout)
            await element.click()
            await page.wait_for_timeout(500)  # Small delay after click
            return True
        except (ElementNotFoundError, PlaywrightTimeoutError) as e:
            if attempt == retries - 1:
                logger.error(f"Failed to click element after {retries} attempts: {selector}")
                raise
            logger.warning(f"Click attempt {attempt + 1} failed, retrying...")
            await page.wait_for_timeout(1000)
    return False


def extract_phone_number(phone: str) -> str:
    """
    Extract and format phone number.

    Args:
        phone: Phone number in various formats

    Returns:
        Formatted phone number with country code
    """
    # Remove all non-digit characters except +
    cleaned = re.sub(r"[^\d+]", "", phone)

    # Ensure it starts with +
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    return cleaned


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry a function on failure.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}, retrying..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}, retrying..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

