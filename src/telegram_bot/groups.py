"""Group management for Telegram automation."""

import asyncio
import logging
from typing import List, Optional, Union

from playwright.async_api import Page

from .browser import TelegramBrowser
from .browser.browser_adapter import EnhancedBrowserAdapter
from .telemetry import get_global_tracer
from .utils import ElementNotFoundError, safe_click, wait_for_selector

logger = logging.getLogger(__name__)


class GroupManager:
    """Manages Telegram groups."""

    def __init__(self, browser: Union[TelegramBrowser, EnhancedBrowserAdapter]):
        """
        Initialize group manager.

        Args:
            browser: TelegramBrowser instance
        """
        self.browser = browser
        self.tracer = get_global_tracer()

    async def create_group(self, name: str, members: Optional[List[str]] = None) -> bool:
        """
        Create a new group.

        Args:
            name: Group name
            members: List of phone numbers to add as members (optional)

        Returns:
            True if group created successfully
        """
        if self.tracer:
            self.tracer.log_operation("group", "create_group", status="started", details={"name": name, "members": members or []})

        page = self.browser.get_page()

        try:
            # Find "New Group" button
            # Common locations: sidebar, menu, or floating action button
            new_group_selectors = [
                'button:has-text("New Group")',
                'button[aria-label*="New Group" i]',
                'button[aria-label*="Create Group" i]',
                '.new-group-button',
                '[data-testid="new-group"]',
            ]

            group_clicked = False
            for selector in new_group_selectors:
                try:
                    if await safe_click(page, selector, timeout=5000):
                        group_clicked = True
                        await page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue

            if not group_clicked:
                logger.error("Could not find New Group button")
                return False

            # If members provided, select them
            if members:
                for phone in members:
                    # Search for contact by phone
                    search_selectors = [
                        'input[placeholder*="Search" i]',
                        'input[type="search"]',
                    ]

                    search_input = None
                    for selector in search_selectors:
                        try:
                            search_input = await wait_for_selector(page, selector, timeout=3000)
                            break
                        except ElementNotFoundError:
                            continue

                    if search_input:
                        await search_input.click()
                        await search_input.fill("")
                        await search_input.type(phone, delay=100)
                        await page.wait_for_timeout(1500)

                        # Click on the contact in results
                        result_selectors = [
                            '.contact',
                            '.user-item',
                            '.search-result',
                        ]

                        for result_selector in result_selectors:
                            try:
                                results = await page.query_selector_all(result_selector)
                                if results:
                                    await results[0].click()
                                    await page.wait_for_timeout(500)
                                    break
                            except Exception:
                                continue

            # Click Next/Continue button
            next_selectors = [
                'button:has-text("Next")',
                'button:has-text("Continue")',
                'button[aria-label*="Next" i]',
            ]

            for selector in next_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # Enter group name
            name_selectors = [
                'input[placeholder*="Group name" i]',
                'input[placeholder*="Name" i]',
                'input[type="text"]',
            ]

            name_input = None
            for selector in name_selectors:
                try:
                    name_input = await wait_for_selector(page, selector, timeout=5000)
                    break
                except ElementNotFoundError:
                    continue

            if not name_input:
                logger.error("Could not find group name input")
                return False

            await name_input.click()
            await name_input.fill("")
            await name_input.type(name, delay=100)
            await page.wait_for_timeout(500)

            # Click Create button
            create_selectors = [
                'button:has-text("Create")',
                'button:has-text("Create Group")',
                'button[type="submit"]',
            ]

            for selector in create_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(3000)
                        logger.info(f"Group created: {name}")
                        if self.tracer:
                            self.tracer.log_operation("group", "create_group", status="completed", details={"name": name, "members": members or []})
                        return True
                except Exception:
                    continue

            logger.warning("Could not find create button")
            if self.tracer:
                self.tracer.log_error("group", "create_group", "Could not find create button")
            return False

        except Exception as e:
            logger.error(f"Error creating group: {e}")
            if self.tracer:
                self.tracer.log_error("group", "create_group", str(e))
            return False

    async def add_members_to_group(self, group_name: str, phone_numbers: List[str]) -> bool:
        """
        Add members to an existing group.

        Args:
            group_name: Name of the group
            phone_numbers: List of phone numbers to add

        Returns:
            True if members added successfully
        """
        page = self.browser.get_page()

        try:
            # Find and open the group
            if not await self._open_group(group_name):
                logger.error(f"Could not open group: {group_name}")
                return False

            # Find group info/settings button
            info_selectors = [
                'button[aria-label*="Group Info" i]',
                'button[aria-label*="Info" i]',
                '.group-info-button',
            ]

            for selector in info_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # Find "Add Members" button
            add_member_selectors = [
                'button:has-text("Add Members")',
                'button:has-text("Add")',
                'button[aria-label*="Add Member" i]',
            ]

            for selector in add_member_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # Add each member
            for phone in phone_numbers:
                # Search for contact
                search_selectors = [
                    'input[placeholder*="Search" i]',
                    'input[type="search"]',
                ]

                search_input = None
                for selector in search_selectors:
                    try:
                        search_input = await wait_for_selector(page, selector, timeout=3000)
                        break
                    except ElementNotFoundError:
                        continue

                if search_input:
                    await search_input.click()
                    await search_input.fill("")
                    await search_input.type(phone, delay=100)
                    await page.wait_for_timeout(1500)

                    # Click on contact
                    result_selectors = [
                        '.contact',
                        '.user-item',
                        '.search-result',
                    ]

                    for result_selector in result_selectors:
                        try:
                            results = await page.query_selector_all(result_selector)
                            if results:
                                await results[0].click()
                                await page.wait_for_timeout(500)
                                break
                        except Exception:
                            continue

            # Click Done/Add button
            done_selectors = [
                'button:has-text("Done")',
                'button:has-text("Add")',
                'button:has-text("Add Members")',
            ]

            for selector in done_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(2000)
                        logger.info(f"Members added to group: {group_name}")
                        return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.error(f"Error adding members to group: {e}")
            return False

    async def remove_member_from_group(self, group_name: str, phone_number: str) -> bool:
        """
        Remove a member from a group.

        Args:
            group_name: Name of the group
            phone_number: Phone number of member to remove

        Returns:
            True if member removed successfully
        """
        if self.tracer:
            self.tracer.log_operation("group", "remove_member_from_group", status="started", details={"group_name": group_name, "phone_number": phone_number})

        page = self.browser.get_page()

        try:
            # Open group
            if not await self._open_group(group_name):
                if self.tracer:
                    self.tracer.log_error("group", "remove_member_from_group", f"Could not open group: {group_name}")
                return False

            # Open group info
            info_selectors = [
                'button[aria-label*="Group Info" i]',
                'button[aria-label*="Info" i]',
                '.group-info-button',
            ]

            info_opened = False
            for selector in info_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(1500)
                        info_opened = True
                        break
                except Exception:
                    continue

            if not info_opened:
                logger.error("Could not open group info")
                if self.tracer:
                    self.tracer.log_error("group", "remove_member_from_group", "Could not open group info")
                return False

            # Look for "Members" section or member list
            # Scroll to find members section if needed
            member_section_selectors = [
                'button:has-text("Members")',
                'div:has-text("Members")',
                '[aria-label*="Members" i]',
            ]

            for selector in member_section_selectors:
                try:
                    member_section = await wait_for_selector(page, selector, timeout=3000)
                    if member_section:
                        await member_section.click()
                        await page.wait_for_timeout(1000)
                        break
                except ElementNotFoundError:
                    continue

            # Wait for member list to load
            await page.wait_for_timeout(1000)

            # Search for member by phone number in the member list
            # Try to find member item that contains the phone number
            member_item_selectors = [
                '.member-item',
                '.user-item',
                '.contact-item',
                '[data-testid="member-item"]',
            ]

            member_found = False
            for selector in member_item_selectors:
                try:
                    member_items = await page.query_selector_all(selector)
                    for item in member_items:
                        try:
                            text = await item.inner_text()
                            # Check if phone number appears in the member item text
                            if phone_number in text or phone_number.replace("+", "") in text:
                                # Right-click or click menu button on member item
                                # Try to find menu button within the member item
                                menu_button = await item.query_selector('button[aria-label*="Menu" i], button[aria-label*="More" i], .menu-button')
                                if menu_button:
                                    await menu_button.click()
                                    await page.wait_for_timeout(500)
                                else:
                                    # Right-click on the item
                                    await item.click(button="right")
                                    await page.wait_for_timeout(500)
                                
                                member_found = True
                                break
                        except Exception:
                            continue
                    
                    if member_found:
                        break
                except Exception:
                    continue

            # Alternative: Search for member using search input in members list
            if not member_found:
                search_selectors = [
                    'input[placeholder*="Search" i]',
                    'input[type="search"]',
                ]

                for selector in search_selectors:
                    try:
                        search_input = await wait_for_selector(page, selector, timeout=3000)
                        if search_input:
                            await search_input.click()
                            await search_input.fill("")
                            await search_input.type(phone_number, delay=100)
                            await page.wait_for_timeout(1500)
                            
                            # Find the member in search results
                            result_items = await page.query_selector_all('.member-item, .user-item, .contact-item')
                            for item in result_items:
                                try:
                                    text = await item.inner_text()
                                    if phone_number in text or phone_number.replace("+", "") in text:
                                        # Click menu button
                                        menu_button = await item.query_selector('button[aria-label*="Menu" i], button[aria-label*="More" i]')
                                        if menu_button:
                                            await menu_button.click()
                                            await page.wait_for_timeout(500)
                                        else:
                                            await item.click(button="right")
                                            await page.wait_for_timeout(500)
                                        member_found = True
                                        break
                                except Exception:
                                    continue
                            break
                    except ElementNotFoundError:
                        continue

            if not member_found:
                logger.error(f"Could not find member with phone number: {phone_number}")
                if self.tracer:
                    self.tracer.log_error("group", "remove_member_from_group", f"Member not found: {phone_number}")
                return False

            # Look for remove/delete option in context menu
            remove_selectors = [
                'button:has-text("Remove")',
                'button:has-text("Remove from Group")',
                'button:has-text("Delete")',
                'button[aria-label*="Remove" i]',
                'button[aria-label*="Delete" i]',
                '.remove-member',
            ]

            remove_clicked = False
            for selector in remove_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(1000)
                        remove_clicked = True
                        break
                except Exception:
                    continue

            if not remove_clicked:
                logger.error("Could not find remove button")
                if self.tracer:
                    self.tracer.log_error("group", "remove_member_from_group", "Could not find remove button")
                return False

            # Check for confirmation dialog
            confirm_selectors = [
                'button:has-text("Remove")',
                'button:has-text("Delete")',
                'button:has-text("Confirm")',
                'button:has-text("Yes")',
                'button[type="submit"]',
            ]

            for selector in confirm_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue

            logger.info(f"Member {phone_number} removed from group: {group_name}")
            if self.tracer:
                self.tracer.log_operation("group", "remove_member_from_group", status="completed", details={"group_name": group_name, "phone_number": phone_number})
            return True

        except Exception as e:
            logger.error(f"Error removing member from group: {e}")
            if self.tracer:
                self.tracer.log_error("group", "remove_member_from_group", str(e))
            return False

    async def get_group_info(self, group_name: str) -> Optional[dict]:
        """
        Get information about a group.

        Args:
            group_name: Name of the group

        Returns:
            Group information dictionary or None if not found
        """
        page = self.browser.get_page()

        try:
            if not await self._open_group(group_name):
                return None

            # Open group info
            info_selectors = [
                'button[aria-label*="Group Info" i]',
                'button[aria-label*="Info" i]',
                '.group-info-button',
            ]

            info_opened = False
            for selector in info_selectors:
                try:
                    if await safe_click(page, selector, timeout=3000):
                        await page.wait_for_timeout(1500)
                        info_opened = True
                        break
                except Exception:
                    continue

            if not info_opened:
                logger.warning("Could not open group info, returning basic info")
                return {"name": group_name}

            # Initialize info dictionary
            info = {"name": group_name}

            # Extract member count
            member_count_selectors = [
                'text=/\\d+\\s+members?/i',
                'text=/\\d+\\s+participants?/i',
                '[aria-label*="members" i]',
                '.member-count',
            ]

            for selector in member_count_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        # Extract number from text like "123 members" or "123 participants"
                        import re
                        match = re.search(r'(\d+)', text)
                        if match:
                            info["member_count"] = int(match.group(1))
                            break
                except Exception:
                    continue

            # Try to get member count from Members button/link
            if "member_count" not in info:
                members_button_selectors = [
                    'button:has-text("Members")',
                    'a:has-text("Members")',
                    '[aria-label*="Members" i]',
                ]

                for selector in members_button_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.inner_text()
                            import re
                            match = re.search(r'(\d+)', text)
                            if match:
                                info["member_count"] = int(match.group(1))
                                break
                    except Exception:
                        continue

            # Extract description
            description_selectors = [
                '.group-description',
                '.description',
                '[aria-label*="Description" i]',
                'div:has-text("Description")',
            ]

            for selector in description_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        description = await element.inner_text()
                        if description and description.strip():
                            info["description"] = description.strip()
                            break
                except Exception:
                    continue

            # Extract group type (group, supergroup, channel)
            # Check for indicators in the UI
            page_content = await page.content()
            if "supergroup" in page_content.lower() or "super group" in page_content.lower():
                info["type"] = "supergroup"
            elif "channel" in page_content.lower():
                info["type"] = "channel"
            else:
                info["type"] = "group"

            # Try to extract admin count or admin list
            admin_selectors = [
                'text=/\\d+\\s+admins?/i',
                '[aria-label*="admin" i]',
                '.admin-count',
            ]

            for selector in admin_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        import re
                        match = re.search(r'(\d+)', text)
                        if match:
                            info["admin_count"] = int(match.group(1))
                            break
                except Exception:
                    continue

            # Try to get group photo/avatar indicator
            photo_selectors = [
                '.group-photo',
                '.avatar',
                '[aria-label*="group photo" i]',
            ]

            for selector in photo_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        info["has_photo"] = True
                        break
                except Exception:
                    continue

            if "has_photo" not in info:
                info["has_photo"] = False

            # Extract username if it's a public group/channel
            username_selectors = [
                'input[value*="@"]',
                '.username',
                '[aria-label*="username" i]',
            ]

            for selector in username_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        value = await element.get_attribute("value") or await element.inner_text()
                        if value and "@" in value:
                            info["username"] = value.strip()
                            break
                except Exception:
                    continue

            # Get current URL which might contain group ID
            current_url = page.url
            if current_url:
                info["url"] = current_url
                # Try to extract group ID from URL
                import re
                match = re.search(r'/(\d+)/?$', current_url)
                if match:
                    info["group_id"] = match.group(1)

            logger.info(f"Group info extracted for: {group_name}")
            return info

        except Exception as e:
            logger.error(f"Error getting group info: {e}")
            return {"name": group_name}  # Return at least basic info

    async def list_groups(self) -> List[str]:
        """
        List all groups.

        Returns:
            List of group names
        """
        page = self.browser.get_page()

        try:
            # Find chat list or group list
            chat_list_selectors = [
                '.chat-list',
                '[data-testid="chat-list"]',
                '.sidebar',
            ]

            groups = []
            for selector in chat_list_selectors:
                try:
                    chat_list = await wait_for_selector(page, selector, timeout=5000)
                    if chat_list:
                        # Extract group names from chat list
                        # This depends on Telegram Web UI structure
                        items = await chat_list.query_selector_all('.chat-item, .group-item')
                        for item in items:
                            text = await item.inner_text()
                            if text:
                                groups.append(text.strip())
                        break
                except ElementNotFoundError:
                    continue

            return groups

        except Exception as e:
            logger.error(f"Error listing groups: {e}")
            return []

    async def _open_group(self, group_name: str) -> bool:
        """
        Open a group by name.

        Args:
            group_name: Name of the group

        Returns:
            True if group opened successfully
        """
        page = self.browser.get_page()

        try:
            # Search for group
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
                return False

            await search_input.click()
            await search_input.fill("")
            await search_input.type(group_name, delay=100)
            await page.wait_for_timeout(2000)

            # Click on group in results
            result_selectors = [
                '.chat-item',
                '.group-item',
                '.search-result',
            ]

            for result_selector in result_selectors:
                try:
                    results = await page.query_selector_all(result_selector)
                    for result in results:
                        text = await result.inner_text()
                        if group_name.lower() in text.lower():
                            await result.click()
                            await page.wait_for_timeout(2000)
                            return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.error(f"Error opening group: {e}")
            return False

