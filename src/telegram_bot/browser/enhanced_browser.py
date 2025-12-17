"""Enhanced browser management with tab management system from Strix."""

import asyncio
import base64
import logging
import threading
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

logger = logging.getLogger(__name__)

MAX_PAGE_SOURCE_LENGTH = 20_000
MAX_CONSOLE_LOG_LENGTH = 30_000
MAX_INDIVIDUAL_LOG_LENGTH = 1_000
MAX_CONSOLE_LOGS_COUNT = 200
MAX_JS_RESULT_LENGTH = 5_000


class EnhancedBrowserInstance:
    """Enhanced browser instance with tab management and advanced features."""

    def __init__(self, headless: bool = False, proxy: Optional[str] = None):
        """
        Initialize enhanced browser instance.

        Args:
            headless: Whether to run browser in headless mode
            proxy: Proxy string in format "ip:port:username:password" for SOCKS5 proxy
        """
        self.headless = headless
        self.proxy = proxy
        self.is_running = True
        self._execution_lock = threading.Lock()

        # Parse proxy settings
        self.proxy_config = self._parse_proxy(proxy) if proxy else None

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.pages: dict[str, Page] = {}
        self.current_page_id: Optional[str] = None
        self._next_tab_id = 1

        self.console_logs: dict[str, list[dict[str, Any]]] = {}

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None

        self._start_event_loop()

    def _start_event_loop(self) -> None:
        """Start async event loop in separate thread."""

        def run_loop() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()

        while self._loop is None:
            threading.Event().wait(0.01)

    def _parse_proxy(self, proxy_string: str) -> dict[str, Any]:
        """
        Parse proxy string in format "ip:port:username:password"

        Args:
            proxy_string: Proxy string to parse

        Returns:
            Dictionary with proxy configuration
        """
        try:
            parts = proxy_string.split(":")
            if len(parts) != 4:
                raise ValueError(f"Invalid proxy format. Expected 'ip:port:username:password', got: {proxy_string}")

            ip, port, username, password = parts

            # Validate port is numeric
            port_int = int(port)

            return {
                "server": f"socks5://{ip}:{port_int}",
                "username": username,
                "password": password
            }
        except Exception as e:
            logger.error(f"Failed to parse proxy string '{proxy_string}': {e}")
            raise ValueError(f"Invalid proxy format: {proxy_string}. Expected 'ip:port:username:password'")

    def _run_async(self, coro: Any) -> dict[str, Any]:
        """Run async coroutine in event loop."""
        if not self._loop or not self.is_running:
            raise RuntimeError("Browser instance is not running")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=30)

    async def _setup_console_logging(self, page: Page, tab_id: str) -> None:
        """Setup console logging for a page."""
        self.console_logs[tab_id] = []

        def handle_console(msg: Any) -> None:
            text = msg.text
            if len(text) > MAX_INDIVIDUAL_LOG_LENGTH:
                text = text[:MAX_INDIVIDUAL_LOG_LENGTH] + "... [TRUNCATED]"

            log_entry = {
                "type": msg.type,
                "text": text,
                "location": msg.location,
                "timestamp": asyncio.get_event_loop().time(),
            }

            self.console_logs[tab_id].append(log_entry)

            if len(self.console_logs[tab_id]) > MAX_CONSOLE_LOGS_COUNT:
                self.console_logs[tab_id] = self.console_logs[tab_id][-MAX_CONSOLE_LOGS_COUNT:]

        page.on("console", handle_console)

    async def _launch_browser(self, url: Optional[str] = None) -> dict[str, Any]:
        """Launch browser and create initial page."""
        self.playwright = await async_playwright().start()

        # Prepare browser launch arguments
        launch_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ]

        # Add proxy arguments if configured
        if self.proxy_config:
            proxy_server = self.proxy_config["server"]
            launch_args.extend([
                f"--proxy-server={proxy_server}",
                "--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1",
            ])
            logger.info(f"Browser configured with proxy: {proxy_server}")

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=launch_args,
        )

        # Prepare context arguments
        context_args = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }

        # Add proxy configuration to context if available
        if self.proxy_config:
            context_args["proxy"] = {
                "server": self.proxy_config["server"],
                "username": self.proxy_config["username"],
                "password": self.proxy_config["password"]
            }
            logger.info(f"Context configured with proxy authentication for user: {self.proxy_config['username']}")

        self.context = await self.browser.new_context(**context_args)

        # Remove webdriver property to avoid detection
        await self.context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        )

        page = await self.context.new_page()
        tab_id = f"tab_{self._next_tab_id}"
        self._next_tab_id += 1
        self.pages[tab_id] = page
        self.current_page_id = tab_id

        await self._setup_console_logging(page, tab_id)

        if url:
            await page.goto(url, wait_until="domcontentloaded")

        return await self._get_page_state(tab_id)

    async def _get_page_state(self, tab_id: Optional[str] = None) -> dict[str, Any]:
        """Get current page state with screenshot."""
        if not tab_id:
            tab_id = self.current_page_id

        if not tab_id or tab_id not in self.pages:
            raise ValueError(f"Tab '{tab_id}' not found")

        page = self.pages[tab_id]

        await asyncio.sleep(0.5)  # Small delay for page stability

        screenshot_bytes = await page.screenshot(type="png", full_page=False)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        url = page.url
        title = await page.title()
        viewport = page.viewport_size

        all_tabs = {}
        for tid, tab_page in self.pages.items():
            try:
                all_tabs[tid] = {
                    "url": tab_page.url,
                    "title": await tab_page.title() if not tab_page.is_closed() else "Closed",
                }
            except Exception:
                all_tabs[tid] = {"url": "Unknown", "title": "Closed"}

        return {
            "screenshot": screenshot_b64,
            "url": url,
            "title": title,
            "viewport": viewport,
            "tab_id": tab_id,
            "all_tabs": all_tabs,
        }

    def launch(self, url: Optional[str] = None) -> dict[str, Any]:
        """Launch browser."""
        with self._execution_lock:
            if self.browser is not None:
                raise ValueError("Browser is already launched")
            return self._run_async(self._launch_browser(url))

    def goto(self, url: str, tab_id: Optional[str] = None) -> dict[str, Any]:
        """Navigate to URL."""
        with self._execution_lock:
            return self._run_async(self._goto(url, tab_id))

    async def _goto(self, url: str, tab_id: Optional[str] = None) -> dict[str, Any]:
        """Internal goto implementation."""
        if not tab_id:
            tab_id = self.current_page_id

        if not tab_id or tab_id not in self.pages:
            raise ValueError(f"Tab '{tab_id}' not found")

        page = self.pages[tab_id]
        await page.goto(url, wait_until="domcontentloaded")
        return await self._get_page_state(tab_id)

    def new_tab(self, url: Optional[str] = None) -> dict[str, Any]:
        """Create new tab."""
        with self._execution_lock:
            return self._run_async(self._new_tab(url))

    async def _new_tab(self, url: Optional[str] = None) -> dict[str, Any]:
        """Internal new tab implementation."""
        if not self.context:
            raise ValueError("Browser not launched")

        page = await self.context.new_page()
        tab_id = f"tab_{self._next_tab_id}"
        self._next_tab_id += 1
        self.pages[tab_id] = page
        self.current_page_id = tab_id

        await self._setup_console_logging(page, tab_id)

        if url:
            await page.goto(url, wait_until="domcontentloaded")

        return await self._get_page_state(tab_id)

    def switch_tab(self, tab_id: str) -> dict[str, Any]:
        """Switch to different tab."""
        with self._execution_lock:
            return self._run_async(self._switch_tab(tab_id))

    async def _switch_tab(self, tab_id: str) -> dict[str, Any]:
        """Internal switch tab implementation."""
        if tab_id not in self.pages:
            raise ValueError(f"Tab '{tab_id}' not found")

        self.current_page_id = tab_id
        return await self._get_page_state(tab_id)

    def close_tab(self, tab_id: str) -> dict[str, Any]:
        """Close a tab."""
        with self._execution_lock:
            return self._run_async(self._close_tab(tab_id))

    async def _close_tab(self, tab_id: str) -> dict[str, Any]:
        """Internal close tab implementation."""
        if tab_id not in self.pages:
            raise ValueError(f"Tab '{tab_id}' not found")

        if len(self.pages) == 1:
            raise ValueError("Cannot close the last tab")

        page = self.pages.pop(tab_id)
        await page.close()

        if tab_id in self.console_logs:
            del self.console_logs[tab_id]

        if self.current_page_id == tab_id:
            self.current_page_id = next(iter(self.pages.keys()))

        return await self._get_page_state(self.current_page_id)

    def list_tabs(self) -> dict[str, Any]:
        """List all tabs."""
        with self._execution_lock:
            return self._run_async(self._list_tabs())

    async def _list_tabs(self) -> dict[str, Any]:
        """Internal list tabs implementation."""
        tab_info = {}
        for tid, tab_page in self.pages.items():
            try:
                tab_info[tid] = {
                    "url": tab_page.url,
                    "title": "Unknown" if tab_page.is_closed() else "Active",
                    "is_current": tid == self.current_page_id,
                }
            except Exception:
                tab_info[tid] = {"url": "Unknown", "title": "Closed", "is_current": False}

        return {
            "tabs": tab_info,
            "total_count": len(tab_info),
            "current_tab": self.current_page_id,
        }

    def get_console_logs(self, tab_id: Optional[str] = None, clear: bool = False) -> dict[str, Any]:
        """Get console logs for a tab."""
        with self._execution_lock:
            return self._run_async(self._get_console_logs(tab_id, clear))

    async def _get_console_logs(
        self, tab_id: Optional[str] = None, clear: bool = False
    ) -> dict[str, Any]:
        """Internal get console logs implementation."""
        if not tab_id:
            tab_id = self.current_page_id

        if not tab_id or tab_id not in self.pages:
            raise ValueError(f"Tab '{tab_id}' not found")

        logs = self.console_logs.get(tab_id, [])

        total_length = sum(len(str(log)) for log in logs)
        if total_length > MAX_CONSOLE_LOG_LENGTH:
            truncated_logs: list[dict[str, Any]] = []
            current_length = 0

            for log in reversed(logs):
                log_length = len(str(log))
                if current_length + log_length <= MAX_CONSOLE_LOG_LENGTH:
                    truncated_logs.insert(0, log)
                    current_length += log_length
                else:
                    break

            if len(truncated_logs) < len(logs):
                truncation_notice = {
                    "type": "info",
                    "text": (
                        f"[TRUNCATED: {len(logs) - len(truncated_logs)} older logs "
                        f"removed to stay within {MAX_CONSOLE_LOG_LENGTH} character limit]"
                    ),
                    "location": {},
                    "timestamp": 0,
                }
                truncated_logs.insert(0, truncation_notice)

            logs = truncated_logs

        if clear:
            self.console_logs[tab_id] = []

        state = await self._get_page_state(tab_id)
        state["console_logs"] = logs
        return state

    def execute_js(self, js_code: str, tab_id: Optional[str] = None) -> dict[str, Any]:
        """Execute JavaScript code."""
        with self._execution_lock:
            return self._run_async(self._execute_js(js_code, tab_id))

    async def _execute_js(self, js_code: str, tab_id: Optional[str] = None) -> dict[str, Any]:
        """Internal execute JS implementation."""
        if not tab_id:
            tab_id = self.current_page_id

        if not tab_id or tab_id not in self.pages:
            raise ValueError(f"Tab '{tab_id}' not found")

        page = self.pages[tab_id]

        try:
            result = await page.evaluate(js_code)
        except Exception as e:
            result = {
                "error": True,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }

        result_str = str(result)
        if len(result_str) > MAX_JS_RESULT_LENGTH:
            result = result_str[:MAX_JS_RESULT_LENGTH] + "... [JS result truncated]"

        state = await self._get_page_state(tab_id)
        state["js_result"] = result
        return state

    def get_page(self, tab_id: Optional[str] = None) -> Page:
        """Get Playwright page object."""
        if not tab_id:
            tab_id = self.current_page_id

        if not tab_id or tab_id not in self.pages:
            raise ValueError(f"Tab '{tab_id}' not found")

        return self.pages[tab_id]

    async def load_context(self, storage_state: dict[str, Any]) -> None:
        """Load browser context from storage state."""
        if not self.playwright:
            await self._launch_browser()

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

        await self.context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        )

        page = await self.context.new_page()
        tab_id = f"tab_{self._next_tab_id}"
        self._next_tab_id += 1
        self.pages[tab_id] = page
        self.current_page_id = tab_id

        await self._setup_console_logging(page, tab_id)

    async def get_storage_state(self) -> dict[str, Any]:
        """Get current storage state."""
        if not self.context:
            raise RuntimeError("Browser context not available")
        return await self.context.storage_state()

    def close(self) -> None:
        """Close browser and cleanup."""
        with self._execution_lock:
            self.is_running = False
            if self._loop:
                asyncio.run_coroutine_threadsafe(self._close_browser(), self._loop)
                self._loop.call_soon_threadsafe(self._loop.stop)

                if self._loop_thread:
                    self._loop_thread.join(timeout=5)

    async def _close_browser(self) -> None:
        """Internal close browser implementation."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")

    def is_alive(self) -> bool:
        """Check if browser is alive."""
        return (
            self.is_running
            and self.browser is not None
            and self.browser.is_connected()
        )

