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

    async def unsubscribe_from_email(self, email_data: Dict, db=None) -> Tuple[bool, str]:
        """
        Attempt to unsubscribe from an email using its unsubscribe links.
        Uses learned patterns to prioritize which links to try first.

        Args:
            email_data: Dictionary containing email data with 'unsubscribe_links'
            db: Optional database instance for learning link patterns

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not email_data.get('unsubscribe_links'):
            return False, "No unsubscribe links found"

        links = email_data['unsubscribe_links']
        attempt_errors = []  # Track all failure reasons

        # Prioritize mailto: links (one-click unsubscribes)
        mailto_links = [link for link in links if link.startswith('mailto:')]
        web_links = [link for link in links if not link.startswith('mailto:')]

        # Try mailto: links first
        for mailto_link in mailto_links:
            try:
                success, message = await self._process_mailto_link(mailto_link)
                if success:
                    return True, message
                attempt_errors.append(f"mailto: {message}")
            except Exception as e:
                attempt_errors.append(f"mailto exception: {str(e)}")
                continue

        # Sort web links by priority using learned patterns
        if db and web_links:
            try:
                from urllib.parse import urlparse

                link_priorities = []
                for link in web_links:
                    try:
                        parsed = urlparse(link)
                        domain = parsed.netloc
                        best_patterns = db.get_best_link_patterns_for_domain(domain)

                        # Calculate priority based on learned patterns
                        path_lower = parsed.path.lower()
                        priority = 0

                        # Check if this link matches any successful pattern
                        for idx, pattern in enumerate(best_patterns):
                            if pattern in path_lower or pattern == 'other':
                                priority = len(best_patterns) - idx + 10
                                break

                        # Default priority for links with no learned pattern
                        if priority == 0:
                            if 'unsubscribe' in path_lower:
                                priority = 5
                            elif 'opt-out' in path_lower or 'optout' in path_lower:
                                priority = 4
                            elif 'preferences' in path_lower:
                                priority = 3
                            else:
                                priority = 2

                        link_priorities.append((link, priority))
                    except Exception as e:
                        link_priorities.append((link, 1))

                # Sort by priority (highest first)
                link_priorities.sort(key=lambda x: x[1], reverse=True)
                web_links = [link for link, _ in link_priorities]

            except Exception as e:
                attempt_errors.append(f"Link prioritization error: {str(e)}")

        # Try each web unsubscribe link until one succeeds
        for idx, link in enumerate(web_links, 1):
            try:
                success, message = await self._process_unsubscribe_link(link)
                if success:
                    return True, message
                attempt_errors.append(f"Link {idx}/{len(web_links)}: {message}")
            except Exception as e:
                attempt_errors.append(f"Link {idx}/{len(web_links)} exception: {str(e)}")
                continue

        # Return detailed failure message
        error_summary = "; ".join(attempt_errors[:5])  # Show first 5 errors
        return False, f"All {len(mailto_links) + len(web_links)} attempts failed: {error_summary}"

    async def _process_mailto_link(self, mailto_url: str) -> Tuple[bool, str]:
        """
        Process a mailto: unsubscribe link.

        Note: mailto: links require sending an email, which we can't easily automate.
        We'll return False but with a helpful message for manual action.

        Args:
            mailto_url: mailto: URL

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Extract email address from mailto: link
        email_address = mailto_url.replace('mailto:', '').split('?')[0]
        return False, f"mailto link (requires manual email to {email_address})"

    async def _process_unsubscribe_link(self, url: str) -> Tuple[bool, str]:
        """
        Process a single unsubscribe link.

        Args:
            url: Unsubscribe URL to visit

        Returns:
            Tuple of (success: bool, message: str)
        """
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        try:
            # Navigate to unsubscribe page with better wait strategy
            try:
                # Try networkidle first (best for dynamic sites)
                await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            except:
                # Fall back to load event
                try:
                    await page.goto(url, wait_until='load', timeout=self.timeout)
                except:
                    # Last resort: domcontentloaded
                    await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)

            # Wait for any client-side rendering or redirects
            await asyncio.sleep(3)

            # Try to detect if already unsubscribed
            page_content = await page.content()
            if self._is_already_unsubscribed(page_content):
                return True, "Already unsubscribed"

            # Try to find and click unsubscribe button/link
            success = await self._find_and_click_unsubscribe(page)

            if success:
                # Wait for confirmation to appear
                await asyncio.sleep(2.5)

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
            return False, f"Error: {str(e)[:100]}"  # Truncate long error messages
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
        # Comprehensive list of unsubscribe button selectors
        # Prioritized by likelihood of success
        selectors = [
            # Most common text-based selectors
            'button:has-text("Unsubscribe")',
            'a:has-text("Unsubscribe")',
            'button:has-text("unsubscribe")',
            'a:has-text("unsubscribe")',

            # Case variations
            'button:has-text("UNSUBSCRIBE")',
            'a:has-text("UNSUBSCRIBE")',

            # With exact match
            'button:text-is("Unsubscribe")',
            'a:text-is("Unsubscribe")',

            # Opt-out variations
            'button:has-text("Opt Out")',
            'a:has-text("Opt Out")',
            'button:has-text("opt out")',
            'a:has-text("opt out")',
            'button:has-text("Opt-Out")',
            'a:has-text("Opt-Out")',

            # Remove variations
            'button:has-text("Remove")',
            'a:has-text("Remove")',
            'button:has-text("Remove me")',
            'a:has-text("Remove me")',

            # Input submit buttons
            'input[type="submit"][value*="unsubscribe" i]',
            'input[type="submit"][value*="opt" i]',
            'input[type="button"][value*="unsubscribe" i]',

            # By ID or class
            '#unsubscribe',
            '.unsubscribe',
            'button[id*="unsubscribe" i]',
            'a[id*="unsubscribe" i]',
            'button[class*="unsubscribe" i]',
            'a[class*="unsubscribe" i]',
            'button[id*="opt-out" i]',
            'a[id*="opt-out" i]',

            # By name attribute
            'button[name*="unsubscribe" i]',
            'input[name*="unsubscribe" i]',

            # By data attributes (common in modern web apps)
            'button[data-action*="unsubscribe" i]',
            'a[data-action*="unsubscribe" i]',
            '[data-testid*="unsubscribe" i]',

            # By aria-label
            'button[aria-label*="unsubscribe" i]',
            'a[aria-label*="unsubscribe" i]',
        ]

        # Try each selector
        for selector in selectors:
            try:
                element = page.locator(selector).first

                # Wait a bit longer and check if visible
                if await element.is_visible(timeout=3000):
                    # Scroll element into view before clicking
                    await element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)

                    await element.click(timeout=5000)
                    await asyncio.sleep(1.5)  # Wait for any modals/confirmations to appear

                    # After clicking, check if there's a confirmation button
                    confirmation_selectors = [
                        'button:has-text("Confirm")',
                        'button:has-text("confirm")',
                        'button:has-text("Yes")',
                        'button:has-text("yes")',
                        'button:has-text("YES")',
                        'button:has-text("Submit")',
                        'button:has-text("submit")',
                        'button:has-text("Continue")',
                        'button:has-text("Proceed")',
                        'input[type="submit"]',
                        'button[type="submit"]',
                        'button:has-text("OK")',
                        'button:has-text("Ok")',
                        '[data-action*="confirm" i]',
                    ]

                    for conf_selector in confirmation_selectors:
                        try:
                            conf_element = page.locator(conf_selector).first
                            if await conf_element.is_visible(timeout=2000):
                                await conf_element.scroll_into_view_if_needed()
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
            # Direct unsubscribe success messages
            r'successfully\s+unsubscribed',
            r'you\s+have\s+been\s+unsubscribed',
            r'unsubscribe\s+successful',
            r'unsubscribe\s+complete',
            r'you\'?re\s+unsubscribed',
            r'you\s+are\s+unsubscribed',

            # Removal from list variations
            r'removed\s+from\s+(?:the\s+|our\s+)?(?:mailing\s+|email\s+)?list',
            r'(?:email\s+)?address\s+(?:has\s+been\s+)?removed',
            r'taken\s+(?:you\s+)?off\s+(?:the\s+|our\s+)?list',

            # No more emails variations
            r'won\'?t\s+(?:receive|get|send)\s+any\s+more',
            r'no\s+longer\s+receive',
            r'will\s+not\s+receive',
            r'stop\s+receiving',
            r'stopped\s+sending',
            r'email\s+subscription\s+(?:has\s+been\s+)?(?:removed|cancelled|ended)',

            # Preferences updated
            r'preferences?\s+(?:have\s+been\s+)?(?:updated|saved|changed)',
            r'settings?\s+(?:have\s+been\s+)?(?:updated|saved|changed)',

            # Thank you messages (common after unsubscribe)
            r'thank\s+you\s+for\s+(?:letting\s+us\s+know|your\s+feedback)',
            r'sorry\s+to\s+see\s+you\s+go',
            r'we\'?re\s+sorry\s+to\s+see\s+you\s+leave',

            # Confirmation messages
            r'request\s+(?:has\s+been\s+)?(?:processed|confirmed|completed)',
            r'subscription\s+(?:has\s+been\s+)?(?:cancelled|removed|ended)',

            # Opted out variations
            r'(?:you\'?ve|you\s+have)\s+opted\s+out',
            r'opt(?:-|\s+)out\s+successful',

            # Done/complete messages
            r'all\s+set',
            r'you\'?re\s+all\s+set',
            r'done',
        ]

        content_lower = content.lower()
        for pattern in patterns:
            if re.search(pattern, content_lower):
                return True

        return False


async def unsubscribe_from_emails(emails: List[Dict], headless: bool = False, db=None) -> List[Dict]:
    """
    Unsubscribe from a list of emails.

    Args:
        emails: List of email data dictionaries
        headless: Run browser in headless mode
        db: Optional database instance for learning patterns

    Returns:
        List of results with success status
    """
    results = []

    async with UnsubscribeAgent(headless=headless) as agent:
        for email in emails:
            success, message = await agent.unsubscribe_from_email(email, db=db)
            results.append({
                'email': email,
                'success': success,
                'message': message
            })

    return results
