"""Login module for Telegram Web automation."""

import asyncio
import logging
from typing import Optional, Union

from playwright.async_api import Page

from .browser import TelegramBrowser
from .browser.browser_adapter import EnhancedBrowserAdapter
from .session import SessionManager
from .telemetry import get_global_tracer
from .utils import ElementNotFoundError, LoginError, SessionExpiredError, safe_click, wait_for_selector

logger = logging.getLogger(__name__)


class TelegramLogin:
    """Handles Telegram Web login flow."""

    def __init__(self, browser: Union[TelegramBrowser, EnhancedBrowserAdapter], session_manager: SessionManager):
        """
        Initialize login handler.

        Args:
            browser: TelegramBrowser instance
            session_manager: SessionManager instance
        """
        self.browser = browser
        self.session_manager = session_manager
        self.tracer = get_global_tracer()

    async def login_with_phone(
        self,
        phone: str,
        use_saved_session: bool = True,
        force_new: bool = False,
        *,
        stop_at_otp: bool = False,
    ) -> bool:
        """
        Login to Telegram Web with phone number.

        Args:
            phone: Phone number with country code (e.g., +855762923340)
            use_saved_session: Whether to use saved session if available
            force_new: Force new login even if session exists
            stop_at_otp: If True, stop the flow after the OTP input is ready and return False.
                This is useful for server/API flows where OTP is submitted in a later request.

        Returns:
            True if login successful
        """
        # Log operation start
        if self.tracer:
            self.tracer.log_operation("login", "login_with_phone", status="started", details={"phone": phone})

        # Try to use saved session first
        if use_saved_session and not force_new:
            if await self._try_saved_session(phone):
                logger.info(f"Successfully logged in using saved session for {phone}")
                if self.tracer:
                    self.tracer.log_operation("login", "login_with_phone", status="completed", details={"phone": phone, "used_saved_session": True})
                return True

        # Start new login flow
        logger.info(f"Starting new login flow for {phone}")
        await self.browser.goto_telegram()

        try:
            # Wait for page to load and find login elements
            await self._wait_for_login_page()

            # Enter phone number
            await self.enter_phone_number(phone)

            # Wait for OTP input to appear. In CLI/GUI, OTP can be obtained interactively.
            await self.wait_for_otp_input_field()
            if stop_at_otp:
                # API flow will submit OTP later.
                return False

            otp = await self.wait_for_otp_input()
            await self.enter_otp(otp)

            # Check for 2FA password prompt
            if await self._check_2fa_required():
                logger.info("2FA password required")
                if self.tracer:
                    self.tracer.log_operation("login", "2fa_required", status="started", details={"phone": phone})
                
                # Wait for user to enter 2FA password
                password = await self.wait_for_2fa_password()
                
                # Handle 2FA
                if await self.handle_2fa(password):
                    logger.info("2FA successful")
                    if self.tracer:
                        self.tracer.log_operation("login", "2fa_completed", status="completed", details={"phone": phone})
                else:
                    error_msg = "2FA verification failed"
                    if self.tracer:
                        self.tracer.log_error("login", "2fa_failed", error_msg)
                    raise LoginError(error_msg)

            # Check if login was successful
            if await self.check_login_success():
                # Save session
                storage_state = await self.browser.get_storage_state()
                self.session_manager.save_session(phone, storage_state)
                logger.info(f"Login successful for {phone}")
                if self.tracer:
                    self.tracer.log_operation("login", "login_with_phone", status="completed", details={"phone": phone, "used_saved_session": False})
                return True
            else:
                error_msg = "Login verification failed"
                if self.tracer:
                    self.tracer.log_error("login", "login_with_phone", error_msg)
                raise LoginError(error_msg)

        except Exception as e:
            logger.error(f"Login failed: {e}")
            if self.tracer:
                self.tracer.log_error("login", "login_with_phone", str(e))
            raise LoginError(f"Login failed: {e}") from e

    async def _try_saved_session(self, phone: str) -> bool:
        """
        Try to use saved session.

        Args:
            phone: Phone number

        Returns:
            True if session is valid and loaded successfully
        """
        session_data = self.session_manager.load_session(phone)
        if not session_data:
            return False

        try:
            storage_state = session_data.get("storage_state")
            if not storage_state:
                return False

            # Load context with saved session
            await self.browser.load_context(storage_state)
            await self.browser.goto_telegram()

            # Wait a bit for page to load
            page = self.browser.get_page()
            await page.wait_for_timeout(3000)

            # Check if we're logged in by looking for chat list or other logged-in indicators
            if await self.check_login_success():
                return True
            else:
                logger.warning("Saved session appears to be expired")
                return False

        except Exception as e:
            logger.warning(f"Failed to use saved session: {e}")
            return False

    async def _wait_for_login_page(self) -> None:
        """Wait for login page to load."""
        page = self.browser.get_page()

        # Common selectors for Telegram Web login page
        # These may need to be updated if Telegram changes their UI
        selectors = [
            'input[type="tel"]',  # Phone input
            'input[placeholder*="phone"]',  # Phone input by placeholder
            'input[placeholder*="Phone"]',  # Phone input by placeholder
            'button:has-text("Next")',  # Next button
            'button:has-text("Continue")',  # Continue button
        ]

        found = False
        for selector in selectors:
            try:
                await wait_for_selector(page, selector, timeout=10000)
                found = True
                break
            except ElementNotFoundError:
                continue

        if not found:
            # Try to find any input field
            try:
                await wait_for_selector(page, "input", timeout=10000)
            except ElementNotFoundError:
                raise LoginError("Could not find login page elements")

        await page.wait_for_timeout(1000)  # Additional wait for page stability

    async def enter_phone_number(self, phone: str) -> None:
        """
        Enter phone number in the login form.

        Args:
            phone: Phone number with country code
        """
        page = self.browser.get_page()

        # Find phone input field
        selectors = [
            'input[type="tel"]',
            'input[placeholder*="phone" i]',
            'input[placeholder*="Phone" i]',
            'input[name*="phone" i]',
        ]

        phone_input = None
        for selector in selectors:
            try:
                phone_input = await wait_for_selector(page, selector, timeout=5000)
                break
            except ElementNotFoundError:
                continue

        if not phone_input:
            raise LoginError("Could not find phone number input field")

        # Clear and enter phone number
        await phone_input.click()
        await phone_input.fill("")
        await phone_input.type(phone, delay=100)  # Type with delay to mimic human
        await page.wait_for_timeout(500)

        # Find and click Next/Continue button
        button_selectors = [
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'button[type="submit"]',
            'button.button-primary',
        ]

        clicked = False
        for selector in button_selectors:
            try:
                if await safe_click(page, selector, timeout=3000):
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            # Try pressing Enter
            await phone_input.press("Enter")
            await page.wait_for_timeout(1000)

        logger.info(f"Phone number entered: {phone}")

    async def wait_for_otp_input(self) -> str:
        """
        Wait for OTP input field and get OTP from user.

        Returns:
            OTP code entered by user
        """
        page = self.browser.get_page()

        # Wait for OTP input field to appear
        selectors = [
            'input[type="tel"]',
            'input[placeholder*="code" i]',
            'input[placeholder*="Code" i]',
            'input[name*="code" i]',
            'input[inputmode="numeric"]',
        ]

        otp_input = None
        for selector in selectors:
            try:
                otp_input = await wait_for_selector(page, selector, timeout=30000)
                break
            except ElementNotFoundError:
                continue

        if not otp_input:
            raise LoginError("OTP input field not found")

        logger.info("OTP input field found. Waiting for user to enter OTP...")
        print("\n" + "=" * 50)
        print("Please enter the OTP code you received:")
        print("=" * 50)

        # Wait for user to enter OTP
        # We'll poll the input field value
        max_wait_time = 300  # 5 minutes
        check_interval = 1  # Check every second
        elapsed = 0

        while elapsed < max_wait_time:
            value = await otp_input.input_value()
            if value and len(value) >= 4:  # OTP is usually 5-6 digits
                logger.info(f"OTP entered: {value}")
                return value

            await asyncio.sleep(check_interval)
            elapsed += check_interval

            # Print progress every 30 seconds
            if elapsed % 30 == 0:
                remaining = max_wait_time - elapsed
                print(f"Waiting for OTP... ({remaining} seconds remaining)")

        raise LoginError("Timeout waiting for OTP input")

    async def wait_for_otp_input_field(self) -> None:
        """Wait until the OTP input field is present.

        This is a non-interactive variant used by API flows:
        - `/auth/start` runs until OTP field is ready, then returns `waiting_for_otp`
        - client calls `/auth/submit-otp` to continue
        """
        page = self.browser.get_page()

        selectors = [
            'input[type="tel"]',
            'input[placeholder*="code" i]',
            'input[placeholder*="Code" i]',
            'input[name*="code" i]',
            'input[inputmode="numeric"]',
        ]

        for selector in selectors:
            try:
                await wait_for_selector(page, selector, timeout=30000)
                return
            except ElementNotFoundError:
                continue

        raise LoginError("OTP input field not found")

    async def enter_otp(self, otp: str) -> None:
        """
        Enter OTP code.

        Args:
            otp: OTP code
        """
        page = self.browser.get_page()

        # Find OTP input field
        selectors = [
            'input[type="tel"]',
            'input[placeholder*="code" i]',
            'input[placeholder*="Code" i]',
            'input[name*="code" i]',
            'input[inputmode="numeric"]',
        ]

        otp_input = None
        for selector in selectors:
            try:
                otp_input = await wait_for_selector(page, selector, timeout=5000)
                break
            except ElementNotFoundError:
                continue

        if not otp_input:
            raise LoginError("Could not find OTP input field")

        # Enter OTP
        await otp_input.click()
        await otp_input.fill("")
        await otp_input.type(otp, delay=100)
        await page.wait_for_timeout(500)

        # Try to submit (click button or press Enter)
        button_selectors = [
            'button:has-text("Next")',
            'button:has-text("Sign In")',
            'button:has-text("Continue")',
            'button[type="submit"]',
        ]

        clicked = False
        for selector in button_selectors:
            try:
                if await safe_click(page, selector, timeout=3000):
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            await otp_input.press("Enter")

        logger.info("OTP entered and submitted")

        # Wait for login to process
        await page.wait_for_timeout(3000)

        # Check for 2FA password prompt
        password_selectors = [
            'input[type="password"]',
            'input[placeholder*="password" i]',
            'input[placeholder*="Password" i]',
        ]

        for selector in password_selectors:
            try:
                await wait_for_selector(page, selector, timeout=3000)
                logger.warning("2FA password required. Please handle manually or implement 2FA handler.")
                break
            except ElementNotFoundError:
                continue

    async def check_login_success(self) -> bool:
        """
        Check if login was successful.

        Returns:
            True if logged in successfully
        """
        page = self.browser.get_page()

        # Wait a bit for page to load
        await page.wait_for_timeout(2000)

        # Look for indicators that we're logged in
        # These selectors may need to be updated based on Telegram Web UI
        logged_in_indicators = [
            '[data-testid="chat-list"]',  # Chat list
            '.chat-list',  # Chat list class
            '[aria-label*="Chat" i]',  # Chat elements
            'input[placeholder*="Search" i]',  # Search input
            'button[aria-label*="Menu" i]',  # Menu button
            '.sidebar',  # Sidebar
        ]

        for selector in logged_in_indicators:
            try:
                await wait_for_selector(page, selector, timeout=5000)
                logger.info("Login success confirmed")
                return True
            except ElementNotFoundError:
                continue

        # Also check if we're still on login page
        login_indicators = [
            'input[type="tel"]',
            'input[placeholder*="phone" i]',
            'button:has-text("Log in")',
        ]

        for selector in login_indicators:
            try:
                await wait_for_selector(page, selector, timeout=2000)
                logger.warning("Still on login page - login may have failed")
                return False
            except ElementNotFoundError:
                continue

        # If we can't determine, assume success (page loaded)
        logger.warning("Could not definitively determine login status, assuming success")
        return True

    async def _check_2fa_required(self) -> bool:
        """
        Check if 2FA password is required.

        Returns:
            True if 2FA password field is present
        """
        page = self.browser.get_page()
        
        # Wait a bit for page to update after OTP submission
        await page.wait_for_timeout(2000)
        
        password_selectors = [
            'input[type="password"]',
            'input[placeholder*="password" i]',
            'input[placeholder*="Password" i]',
        ]

        for selector in password_selectors:
            try:
                await wait_for_selector(page, selector, timeout=3000)
                return True
            except ElementNotFoundError:
                continue
        
        return False

    async def wait_for_2fa_password(self) -> str:
        """
        Wait for user to enter 2FA password.

        Returns:
            2FA password entered by user
        """
        page = self.browser.get_page()

        # Find password input field
        password_selectors = [
            'input[type="password"]',
            'input[placeholder*="password" i]',
            'input[placeholder*="Password" i]',
        ]

        password_input = None
        for selector in password_selectors:
            try:
                password_input = await wait_for_selector(page, selector, timeout=10000)
                break
            except ElementNotFoundError:
                continue

        if not password_input:
            raise LoginError("2FA password input field not found")

        logger.info("2FA password input field found. Waiting for user to enter password...")
        print("\n" + "=" * 50)
        print("Please enter your 2FA password:")
        print("=" * 50)

        # Wait for user to enter password
        max_wait_time = 300  # 5 minutes
        check_interval = 1  # Check every second
        elapsed = 0

        while elapsed < max_wait_time:
            value = await password_input.input_value()
            if value and len(value) >= 1:  # Password entered
                logger.info("2FA password entered")
                return value

            await asyncio.sleep(check_interval)
            elapsed += check_interval

            # Print progress every 30 seconds
            if elapsed % 30 == 0:
                remaining = max_wait_time - elapsed
                print(f"Waiting for 2FA password... ({remaining} seconds remaining)")

        raise LoginError("Timeout waiting for 2FA password input")

    async def handle_2fa(self, password: str) -> bool:
        """
        Handle 2FA password if required.

        Args:
            password: 2FA password

        Returns:
            True if 2FA successful
        """
        page = self.browser.get_page()

        # Find password input
        password_selectors = [
            'input[type="password"]',
            'input[placeholder*="password" i]',
            'input[placeholder*="Password" i]',
        ]

        password_input = None
        for selector in password_selectors:
            try:
                password_input = await wait_for_selector(page, selector, timeout=5000)
                break
            except ElementNotFoundError:
                continue

        if not password_input:
            logger.info("No 2FA password field found")
            return True  # No 2FA required

        # Enter password
        await password_input.click()
        await password_input.fill("")
        await password_input.type(password, delay=100)
        await page.wait_for_timeout(500)

        # Submit
        button_selectors = [
            'button:has-text("Next")',
            'button:has-text("Sign In")',
            'button[type="submit"]',
        ]

        for selector in button_selectors:
            try:
                if await safe_click(page, selector, timeout=3000):
                    break
            except Exception:
                continue

        await page.wait_for_timeout(2000)
        return await self.check_login_success()

