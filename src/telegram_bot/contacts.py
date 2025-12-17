"""Contact management for Telegram automation."""

import asyncio
import logging
from typing import Optional, Union

from playwright.async_api import Page

from .browser import TelegramBrowser
from .browser.browser_adapter import EnhancedBrowserAdapter
from .telemetry import get_global_tracer
from .utils import ElementNotFoundError, safe_click, wait_for_selector

logger = logging.getLogger(__name__)


class ContactManager:
    """Manages Telegram contacts."""

    def __init__(self, browser: Union[TelegramBrowser, EnhancedBrowserAdapter]):
        """
        Initialize contact manager.

        Args:
            browser: TelegramBrowser instance
        """
        self.browser = browser
        self.tracer = get_global_tracer()

    async def check_phone_exists(self, phone: str) -> bool:
        """
        Check if a phone number has a Telegram account.

        Args:
            phone: Phone number with country code

        Returns:
            True if phone number has Telegram account, False otherwise
        """
        if self.tracer:
            self.tracer.log_operation("contact", "check_phone_exists", status="started", details={"phone": phone})

        page = self.browser.get_page()

        try:
            # Find and click search/contact icon
            # Common selectors for search in Telegram Web
            search_selectors = [
                'input[placeholder*="Search" i]',
                'input[type="search"]',
                '.search-input',
                '[aria-label*="Search" i]',
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await wait_for_selector(page, selector, timeout=5000)
                    break
                except ElementNotFoundError:
                    continue

            if not search_input:
                logger.error("Could not find search input")
                return False

            # Click search input and enter phone number
            await search_input.click()
            await search_input.fill("")
            await search_input.type(phone, delay=100)
            await page.wait_for_timeout(2000)  # Wait for search results

            # Look for user in search results
            # Common selectors for search results
            result_selectors = [
                '.search-result',
                '.contact',
                '[data-testid="search-result"]',
                '.user-item',
            ]

            # Check if any results appear
            for selector in result_selectors:
                try:
                    results = await page.query_selector_all(selector)
                    if results:
                        logger.info(f"Found Telegram account for {phone}")
                        return True
                except Exception:
                    continue

            # Also check if phone number appears in any text on page
            page_content = await page.content()
            if phone in page_content or phone.replace("+", "") in page_content:
                logger.info(f"Found phone number reference for {phone}")
                if self.tracer:
                    self.tracer.log_operation("contact", "check_phone_exists", status="completed", details={"phone": phone, "exists": True})
                return True

            logger.info(f"No Telegram account found for {phone}")
            if self.tracer:
                self.tracer.log_operation("contact", "check_phone_exists", status="completed", details={"phone": phone, "exists": False})
            return False

        except Exception as e:
            logger.error(f"Error checking phone number: {e}")
            if self.tracer:
                self.tracer.log_error("contact", "check_phone_exists", str(e))
            return False

    async def add_contact(
        self, phone: str, first_name: str, last_name: str = ""
    ) -> bool:
        """
        Add a new contact.

        Args:
            phone: Phone number with country code
            first_name: First name
            last_name: Last name (optional)

        Returns:
            True if contact added successfully
        """
        if self.tracer:
            self.tracer.log_operation("contact", "add_contact", status="started", details={"phone": phone, "first_name": first_name, "last_name": last_name})

        page = self.browser.get_page()

        try:
            # Find menu or settings button to access contacts
            menu_selectors = [
                'button[aria-label*="Menu" i]',
                'button[aria-label*="Settings" i]',
                '.menu-button',
                '[data-testid="menu-button"]',
            ]

            menu_clicked = False
            for selector in menu_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        menu_clicked = True
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # Look for "Contacts" or "Add Contact" option
            contact_selectors = [
                'button:has-text("Contacts")',
                'button:has-text("Add Contact")',
                'a:has-text("Contacts")',
                '[aria-label*="Contact" i]',
            ]

            contact_clicked = False
            for selector in contact_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        contact_clicked = True
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # Find "New Contact" or "Add Contact" button
            new_contact_selectors = [
                'button:has-text("New Contact")',
                'button:has-text("Add Contact")',
                'button:has-text("Add")',
                '[aria-label*="Add Contact" i]',
            ]

            for selector in new_contact_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # Fill in contact form
            # First name
            first_name_selectors = [
                'input[placeholder*="First name" i]',
                'input[name*="first" i]',
                'input[type="text"]:first-of-type',
            ]

            for selector in first_name_selectors:
                try:
                    first_name_input = await wait_for_selector(page, selector, timeout=3000)
                    await first_name_input.click()
                    await first_name_input.fill(first_name)
                    break
                except ElementNotFoundError:
                    continue

            # Last name (if provided)
            if last_name:
                last_name_selectors = [
                    'input[placeholder*="Last name" i]',
                    'input[name*="last" i]',
                ]

                for selector in last_name_selectors:
                    try:
                        last_name_input = await wait_for_selector(page, selector, timeout=3000)
                        await last_name_input.click()
                        await last_name_input.fill(last_name)
                        break
                    except ElementNotFoundError:
                        continue

            # Phone number
            phone_selectors = [
                'input[type="tel"]',
                'input[placeholder*="phone" i]',
                'input[name*="phone" i]',
            ]

            for selector in phone_selectors:
                try:
                    phone_input = await wait_for_selector(page, selector, timeout=3000)
                    await phone_input.click()
                    await phone_input.fill(phone)
                    break
                except ElementNotFoundError:
                    continue

            await page.wait_for_timeout(500)

            # Click Save/Add button
            save_selectors = [
                'button:has-text("Save")',
                'button:has-text("Add")',
                'button:has-text("Create")',
                'button[type="submit"]',
            ]

            for selector in save_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(2000)
                        logger.info(f"Contact added: {first_name} {last_name} ({phone})")
                        if self.tracer:
                            self.tracer.log_operation("contact", "add_contact", status="completed", details={"phone": phone, "first_name": first_name, "last_name": last_name})
                        return True
                except Exception:
                    continue

            logger.warning("Could not find save button, contact may not have been added")
            if self.tracer:
                self.tracer.log_error("contact", "add_contact", "Could not find save button")
            return False

        except Exception as e:
            logger.error(f"Error adding contact: {e}")
            if self.tracer:
                self.tracer.log_error("contact", "add_contact", str(e))
            return False

    async def search_contact(self, phone: str) -> Optional[dict]:
        """
        Search for a contact by phone number.

        Args:
            phone: Phone number with country code

        Returns:
            Contact information dictionary or None if not found
        """
        page = self.browser.get_page()

        try:
            # Use search functionality
            search_selectors = [
                'input[placeholder*="Search" i]',
                'input[type="search"]',
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await wait_for_selector(page, selector, timeout=5000)
                    break
                except ElementNotFoundError:
                    continue

            if not search_input:
                return None

            await search_input.click()
            await search_input.fill("")
            await search_input.type(phone, delay=100)
            await page.wait_for_timeout(2000)

            # Look for contact in results
            result_selectors = [
                '.search-result',
                '.contact',
                '.user-item',
            ]

            for selector in result_selectors:
                try:
                    results = await page.query_selector_all(selector)
                    if results:
                        # Try to extract contact info from first result
                        first_result = results[0]
                        text = await first_result.inner_text()
                        return {"phone": phone, "name": text.strip()}
                except Exception:
                    continue

            return None

        except Exception as e:
            logger.error(f"Error searching contact: {e}")
            return None

