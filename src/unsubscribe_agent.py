"""Playwright-based agent for automatically unsubscribing from emails."""

import asyncio
from typing import List, Dict, Tuple
from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError
import re


class UnsubscribeAgent:
    """Agent that navigates to unsubscribe links and completes the unsubscribe process."""

    def __init__(self, headless: bool = False, timeout: int = 30000):
        """
        Initialize the unsubscribe agent.

        Args:
            headless: Run browser in headless mode
            timeout: Timeout for page operations in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.playwright = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def unsubscribe_from_email(self, email_data: Dict) -> Tuple[bool, str]:
        """
        Attempt to unsubscribe from an email using its unsubscribe links.

        Args:
            email_data: Dictionary containing email data with 'unsubscribe_links'

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not email_data.get('unsubscribe_links'):
            return False, "No unsubscribe links found"

        # Try each unsubscribe link until one succeeds
        for link in email_data['unsubscribe_links']:
            # Skip mailto links
            if link.startswith('mailto:'):
                continue

            try:
                success, message = await self._process_unsubscribe_link(link)
                if success:
                    return True, message
            except Exception as e:
                continue

        return False, "All unsubscribe attempts failed"

    async def _process_unsubscribe_link(self, url: str) -> Tuple[bool, str]:
        """
        Process a single unsubscribe link.

        Args:
            url: Unsubscribe URL to visit

        Returns:
            Tuple of (success: bool, message: str)
        """
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # Navigate to unsubscribe page
            await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
            await asyncio.sleep(2)  # Wait for any redirects or JS to execute

            # Try to detect if already unsubscribed
            page_content = await page.content()
            if self._is_already_unsubscribed(page_content):
                return True, "Already unsubscribed"

            # Try to find and click unsubscribe button/link
            success = await self._find_and_click_unsubscribe(page)

            if success:
                # Wait a bit for confirmation
                await asyncio.sleep(2)

                # Check for success indicators
                page_content = await page.content()
                if self._is_unsubscribe_successful(page_content):
                    return True, "Successfully unsubscribed"
                else:
                    return True, "Clicked unsubscribe (confirmation uncertain)"

            return False, "Could not find unsubscribe button"

        except PlaywrightTimeoutError:
            return False, "Page load timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            await context.close()

    async def _find_and_click_unsubscribe(self, page: Page) -> bool:
        """
        Try to find and click the unsubscribe button on the page.

        Args:
            page: Playwright page object

        Returns:
            True if unsubscribe button was found and clicked
        """
        # Common unsubscribe button selectors
        selectors = [
            # Text-based selectors
            'button:has-text("unsubscribe")',
            'button:has-text("Unsubscribe")',
            'a:has-text("unsubscribe")',
            'a:has-text("Unsubscribe")',
            'input[type="submit"][value*="unsubscribe" i]',
            'button:has-text("opt out")',
            'button:has-text("Opt Out")',
            'a:has-text("opt out")',

            # By ID or class
            '#unsubscribe',
            '.unsubscribe',
            'button[id*="unsubscribe" i]',
            'a[id*="unsubscribe" i]',
            'button[class*="unsubscribe" i]',
            'a[class*="unsubscribe" i]',

            # Confirm/Submit buttons (often appear after clicking unsubscribe)
            'button:has-text("Confirm")',
            'button:has-text("confirm")',
            'button:has-text("Yes")',
            'button:has-text("Submit")',
        ]

        # Try each selector
        for selector in selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=2000):
                    await element.click(timeout=5000)
                    await asyncio.sleep(1)

                    # After clicking, check if there's a confirmation button
                    confirmation_selectors = [
                        'button:has-text("Confirm")',
                        'button:has-text("Yes")',
                        'button:has-text("Submit")',
                        'input[type="submit"]',
                    ]

                    for conf_selector in confirmation_selectors:
                        try:
                            conf_element = page.locator(conf_selector).first
                            if await conf_element.is_visible(timeout=2000):
                                await conf_element.click(timeout=5000)
                                await asyncio.sleep(1)
                                break
                        except:
                            continue

                    return True
            except:
                continue

        return False

    def _is_already_unsubscribed(self, content: str) -> bool:
        """Check if page indicates already unsubscribed."""
        patterns = [
            r'already\s+unsubscribed',
            r'you\s+have\s+been\s+unsubscribed',
            r'successfully\s+unsubscribed',
            r'removed\s+from\s+(?:the\s+)?(?:mailing\s+)?list',
            r'no\s+longer\s+receive',
        ]

        content_lower = content.lower()
        for pattern in patterns:
            if re.search(pattern, content_lower):
                return True

        return False

    def _is_unsubscribe_successful(self, content: str) -> bool:
        """Check if page indicates successful unsubscription."""
        patterns = [
            r'successfully\s+unsubscribed',
            r'you\s+have\s+been\s+unsubscribed',
            r'unsubscribe\s+successful',
            r'removed\s+from\s+(?:the\s+)?(?:mailing\s+)?list',
            r'won\'?t\s+receive\s+any\s+more',
            r'no\s+longer\s+receive',
            r'preferences?\s+(?:have\s+been\s+)?updated',
            r'email\s+address\s+(?:has\s+been\s+)?removed',
        ]

        content_lower = content.lower()
        for pattern in patterns:
            if re.search(pattern, content_lower):
                return True

        return False


async def unsubscribe_from_emails(emails: List[Dict], headless: bool = False) -> List[Dict]:
    """
    Unsubscribe from a list of emails.

    Args:
        emails: List of email data dictionaries
        headless: Run browser in headless mode

    Returns:
        List of results with success status
    """
    results = []

    async with UnsubscribeAgent(headless=headless) as agent:
        for email in emails:
            success, message = await agent.unsubscribe_from_email(email)
            results.append({
                'email': email,
                'success': success,
                'message': message
            })

    return results
