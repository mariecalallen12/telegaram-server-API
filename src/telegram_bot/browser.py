"""Browser management for Telegram automation."""

import asyncio
import logging
from typing import Any, Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

logger = logging.getLogger(__name__)


class TelegramBrowser:
    """Manages Playwright browser instance for Telegram Web automation."""

    def __init__(self, headless: bool = False, timeout: int = 30000):
        """
        Initialize browser manager.

        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for operations in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_running = False

    async def launch(self) -> None:
        """Launch browser and create context."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                timezone_id="America/New_York",
            )

            # Remove webdriver property to avoid detection
            await self.context.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """
            )

            self.page = await self.context.new_page()
            self.is_running = True
            logger.info("Browser launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise

    async def goto_telegram(self, url: str = "https://web.telegram.org/a/") -> None:
        """
        Navigate to Telegram Web.

        Args:
            url: Telegram Web URL
        """
        if not self.page:
            raise RuntimeError("Browser not launched. Call launch() first.")

        try:
            await self.page.goto(url, wait_until="networkidle", timeout=self.timeout)
            logger.info(f"Navigated to {url}")
            # Wait a bit for page to fully load
            await self.page.wait_for_timeout(2000)
        except Exception as e:
            logger.error(f"Failed to navigate to Telegram: {e}")
            raise

    async def wait_for_element(
        self, selector: str, timeout: Optional[int] = None, visible: bool = True
    ) -> Any:
        """
        Wait for an element to appear on the page.

        Args:
            selector: CSS selector or text selector
            timeout: Maximum time to wait in milliseconds
            visible: Whether to wait for element to be visible

        Returns:
            ElementHandle if found
        """
        if not self.page:
            raise RuntimeError("Browser not launched. Call launch() first.")

        timeout = timeout or self.timeout
        try:
            if visible:
                element = await self.page.wait_for_selector(
                    selector, timeout=timeout, state="visible"
                )
            else:
                element = await self.page.wait_for_selector(selector, timeout=timeout)
            return element
        except Exception as e:
            logger.error(f"Element not found: {selector}")
            raise

    def get_page(self) -> Page:
        """
        Get current page object.

        Returns:
            Current Playwright page
        """
        if not self.page:
            raise RuntimeError("Browser not launched. Call launch() first.")
        return self.page

    async def load_context(self, storage_state: dict[str, Any]) -> None:
        """
        Load browser context from storage state.

        Args:
            storage_state: Storage state dictionary (cookies, localStorage, etc.)
        """
        if not self.playwright:
            await self.launch()

        if self.context:
            await self.context.close()

        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            storage_state=storage_state,
        )

        # Remove webdriver property
        await self.context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        )

        self.page = await self.context.new_page()
        logger.info("Browser context loaded from storage state")

    async def get_storage_state(self) -> dict[str, Any]:
        """
        Get current storage state (cookies, localStorage, etc.).

        Returns:
            Storage state dictionary
        """
        if not self.context:
            raise RuntimeError("Browser context not available")
        return await self.context.storage_state()

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.is_running = False
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.launch()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

