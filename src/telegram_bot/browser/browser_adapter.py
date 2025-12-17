"""Adapter to make EnhancedBrowserInstance compatible with TelegramBrowser interface."""

import asyncio
import logging
from typing import Any, Optional

from playwright.async_api import Page

from .enhanced_browser import EnhancedBrowserInstance

logger = logging.getLogger(__name__)


class EnhancedBrowserAdapter:
    """
    Adapter to make EnhancedBrowserInstance compatible with TelegramBrowser interface.
    
    This allows existing modules (login, contacts, groups) to use Enhanced Browser
    features while maintaining backward compatibility.
    """

    def __init__(self, headless: bool = False, timeout: int = 30000, proxy: Optional[str] = None):
        """
        Initialize adapter.

        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for operations in milliseconds
            proxy: Proxy string in format "ip:port:username:password" for SOCKS5 proxy
        """
        self.headless = headless
        self.timeout = timeout
        self.proxy = proxy
        self.enhanced_browser = EnhancedBrowserInstance(headless=headless, proxy=proxy)
        self.is_running = False
        self._current_tab_id: Optional[str] = None

    async def launch(self) -> None:
        """Launch browser and create context."""
        try:
            # Launch enhanced browser (sync method that runs async internally)
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.enhanced_browser.launch, "https://web.telegram.org/a/"
            )
            self._current_tab_id = result.get("tab_id")
            self.is_running = True
            logger.info("Enhanced browser launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch enhanced browser: {e}")
            raise

    async def goto_telegram(self, url: str = "https://web.telegram.org/a/") -> None:
        """
        Navigate to Telegram Web.

        Args:
            url: Telegram Web URL
        """
        if not self.is_running:
            await self.launch()

        try:
            loop = asyncio.get_event_loop()
            if self._current_tab_id:
                await loop.run_in_executor(
                    None, self.enhanced_browser.goto, url, self._current_tab_id
                )
            else:
                # Create new tab if no current tab
                result = await loop.run_in_executor(None, self.enhanced_browser.new_tab, url)
                self._current_tab_id = result.get("tab_id")
            logger.info(f"Navigated to {url}")
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
        if not self.is_running:
            raise RuntimeError("Browser not launched. Call launch() first.")

        page = self.get_page()
        timeout = timeout or self.timeout
        try:
            if visible:
                element = await page.wait_for_selector(
                    selector, timeout=timeout, state="visible"
                )
            else:
                element = await page.wait_for_selector(selector, timeout=timeout)
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
        if not self.is_running:
            raise RuntimeError("Browser not launched. Call launch() first.")

        if not self._current_tab_id:
            raise RuntimeError("No active tab. Call launch() or goto_telegram() first.")

        return self.enhanced_browser.get_page(tab_id=self._current_tab_id)

    async def load_context(self, storage_state: dict[str, Any]) -> None:
        """
        Load browser context from storage state.

        Args:
            storage_state: Storage state dictionary (cookies, localStorage, etc.)
        """
        try:
            # load_context is async in EnhancedBrowserInstance
            await self.enhanced_browser.load_context(storage_state)
            # Get the current tab ID after loading context
            loop = asyncio.get_event_loop()
            tabs = await loop.run_in_executor(None, self.enhanced_browser.list_tabs)
            if tabs.get("tabs"):
                self._current_tab_id = tabs.get("current_tab")
            self.is_running = True
            logger.info("Browser context loaded from storage state")
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            raise

    async def get_storage_state(self) -> dict[str, Any]:
        """
        Get current storage state (cookies, localStorage, etc.).

        Returns:
            Storage state dictionary
        """
        if not self.enhanced_browser.context:
            raise RuntimeError("Browser context not available")
        return await self.enhanced_browser.get_storage_state()

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        try:
            # close() is sync in EnhancedBrowserInstance
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.enhanced_browser.close)
            self.is_running = False
            self._current_tab_id = None
            logger.info("Enhanced browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.launch()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

