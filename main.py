#!/usr/bin/env python3
"""
Gmail Unsubscriber - Automatically unsubscribe from unwanted emails with your approval.
"""

import asyncio
import sys
import argparse
from datetime import datetime
from email.utils import parseaddr

from src.gmail_client import GmailClient
from src.cli_interface import CLIInterface
from src.unsubscribe_agent import unsubscribe_from_emails
from src.database import UnsubscribeDatabase
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


class GmailUnsubscriber:
    """Main application orchestrator."""

    def __init__(self, headless: bool = False, max_emails: int = 50):
        self.gmail = GmailClient()
        self.cli = CLIInterface()
        self.db = UnsubscribeDatabase()
        self.headless = headless
        self.max_emails = max_emails

    def run(self):
        """Run the main application."""
        self.cli.display_welcome()

        # Authenticate with Gmail
        self.cli.display_info("Authenticating with Gmail...")
        if not self.gmail.authenticate():
            self.cli.display_error("Failed to authenticate with Gmail.")
            return

        self.cli.display_info("Successfully authenticated!\n")

        # Main loop
        while True:
            # Scan for emails
            self.cli.display_info(f"Scanning for emails with unsubscribe links (max {self.max_emails})...")
            emails = self.gmail.find_emails_with_unsubscribe(max_results=self.max_emails)

            # Filter out already processed emails
            emails = [email for email in emails if not self.db.is_already_processed(email['id'])]

            if not emails:
                self.cli.display_info("No new emails with unsubscribe links found.")
                if not self.cli.ask_continue():
                    break
                continue

            self.cli.display_scan_progress(len(emails))

            # Get user approval
            approved_emails = self.cli.display_emails(emails)

            if not approved_emails:
                self.cli.display_info("No emails selected for unsubscribing.")
                if not self.cli.ask_continue():
                    break
                continue

            # Process unsubscribes
            asyncio.run(self._process_unsubscribes(approved_emails))

            # Ask if user wants to continue
            if not self.cli.ask_continue():
                break

        # Show final statistics
        self._show_statistics()

    def run_suggest_mode(self, days_back: int = 90):
        """
        Run in suggestion mode - analyze reading patterns and suggest unsubscribes.

        Args:
            days_back: Number of days to look back
        """
        self.cli.display_welcome()
        self.cli.display_info("Successfully authenticated!\n")

        # Analyze reading patterns with progress bar
        self.cli.display_info(f"Analyzing your email reading patterns over the last {days_back} days...\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.cli.console
        ) as progress:
            fetch_task = progress.add_task("[cyan]Fetching emails...", total=None)
            ai_task = progress.add_task("[green]Generating AI hot takes...", total=None, visible=False)

            def update_progress(stage, current, total):
                if stage == 'fetch':
                    if progress.tasks[fetch_task].total is None:
                        progress.update(fetch_task, total=total)
                    progress.update(fetch_task, completed=current)
                elif stage == 'ai':
                    if not progress.tasks[ai_task].visible:
                        progress.update(ai_task, visible=True, total=total)
                    progress.update(ai_task, completed=current)

            worst_offenders = self.gmail.analyze_reading_patterns(
                days_back=days_back,
                max_emails=self.max_emails * 10,  # Analyze more emails for better patterns
                update_db=True,  # Keep reading patterns fresh each time
                progress_callback=update_progress
            )

        self.cli.console.print()

        if not worst_offenders:
            self.cli.display_info("No subscriptions found that match the criteria.")
            return

        # Display worst offenders and get approval
        approved_senders = self.cli.display_worst_offenders(worst_offenders)

        if not approved_senders:
            self.cli.display_info("No senders selected for unsubscribing.")
            return

        # For each approved sender, get a recent email and process unsubscribe
        emails_to_unsubscribe = []
        self.cli.display_info("\nFetching recent emails from selected senders...\n")

        for sender_data in approved_senders:
            sender_address = sender_data['sender_address']

            # Try to use cached unsubscribe links first
            if sender_data.get('latest_unsubscribe_links'):
                # Create a mock email object with the unsubscribe links
                email_data = {
                    'id': f"suggested_{sender_address}",
                    'from': f"{sender_data['sender_name']} <{sender_address}>",
                    'subject': sender_data['sample_subjects'][0] if sender_data['sample_subjects'] else '',
                    'snippet': '',
                    'unsubscribe_links': sender_data['latest_unsubscribe_links']
                }
                emails_to_unsubscribe.append(email_data)
            else:
                # Fetch a recent email from this sender
                emails = self.gmail.get_emails_from_sender(sender_address, max_results=1)
                if emails and emails[0].get('unsubscribe_links'):
                    emails_to_unsubscribe.append(emails[0])

        if not emails_to_unsubscribe:
            self.cli.display_error("Could not find unsubscribe links for selected senders.")
            return

        # In suggest mode, default to headless unless user explicitly wants visible browser
        # Set headless to True if not already set to False by --headless flag
        suggest_headless = True
        if not self.headless:
            # User hasn't specified headless flag, so default to headless in suggest mode
            self.cli.display_info("Running browser in headless mode (invisible)...")
            self.cli.display_info("Tip: Use --headless=false to see the browser if needed\n")
            suggest_headless = True
        else:
            suggest_headless = self.headless

        # Process unsubscribes with headless mode
        asyncio.run(self._process_unsubscribes(emails_to_unsubscribe, override_headless=suggest_headless))

        # Show final statistics
        self._show_statistics()

    async def _process_unsubscribes(self, emails: list, override_headless: bool = None):
        """
        Process unsubscribe requests for approved emails.

        Args:
            emails: List of approved email data dictionaries
            override_headless: Override the instance headless setting
        """
        total = len(emails)
        successful = 0
        failed = 0
        failed_items = []

        self.cli.display_info(f"\nProcessing {total} unsubscribe request(s)...\n")

        # Use override if provided, otherwise use instance setting
        use_headless = override_headless if override_headless is not None else self.headless

        # Unsubscribe from each email
        results = await unsubscribe_from_emails(emails, headless=use_headless)

        for idx, result in enumerate(results, 1):
            email = result['email']
            success = result['success']
            message = result['message']

            # Display progress
            self.cli.display_unsubscribe_progress(idx, total, email)

            # Extract sender info
            sender_name, sender_address = parseaddr(email['from'])

            # Add subscription to database
            subscription_id = self.db.add_subscription(sender_address, sender_name)

            # Get first unsubscribe link for recording
            unsubscribe_link = email['unsubscribe_links'][0] if email['unsubscribe_links'] else ''

            # Record attempt
            self.db.record_unsubscribe_attempt(
                subscription_id,
                email['id'],
                unsubscribe_link,
                success,
                message
            )

            # Display result
            self.cli.display_unsubscribe_result(email, success, message)

            if success:
                successful += 1
            else:
                failed += 1
                # Collect failed items for manual action
                failed_items.append({
                    'sender': sender_name or sender_address,
                    'email': sender_address,
                    'links': email.get('unsubscribe_links', [])
                })

        # Display summary
        self.cli.display_summary(total, successful, failed)

        # Show manual unsubscribe links for failed attempts
        if failed_items:
            self.cli.display_manual_unsubscribe_links(failed_items)

    def _show_statistics(self):
        """Show overall statistics from database."""
        stats = self.db.get_statistics()

        self.cli.display_info("\n" + "=" * 60)
        self.cli.display_info("Overall Statistics")
        self.cli.display_info("=" * 60)
        self.cli.console.print(f"Total subscriptions tracked: {stats['total_subscriptions']}")
        self.cli.console.print(f"Successfully unsubscribed: {stats['unsubscribed_count']}")
        self.cli.console.print(f"Effective unsubscribes: {stats['effective_unsubscribes']}")
        self.cli.console.print(f"Still receiving emails from: {stats['failed_unsubscribes']}")
        self.cli.console.print(f"Total attempts: {stats['total_attempts']}")
        self.cli.console.print(f"Successful attempts: {stats['successful_attempts']}")

    def check_effectiveness(self):
        """Check effectiveness of previous unsubscribes."""
        self.cli.display_info("Checking unsubscribe effectiveness...\n")

        # Get all unsubscribed senders
        report = self.db.get_unsubscribe_effectiveness_report()

        if not report:
            self.cli.display_info("No unsubscribes to check yet.")
            return

        # Scan recent emails to see if we're still getting emails from unsubscribed senders
        self.cli.display_info("Scanning recent emails...")
        recent_emails = self.gmail.find_emails_with_unsubscribe(max_results=200)

        # Check each email against unsubscribed senders
        for email in recent_emails:
            _, sender_address = parseaddr(email['from'])
            subscription = self.db.get_subscription_by_sender(sender_address)

            if subscription and subscription['unsubscribe_status'] == 'unsubscribed':
                # Found an email from an unsubscribed sender
                self.db.record_post_unsubscribe_email(
                    subscription['id'],
                    email['id'],
                    datetime.now().isoformat(),
                    email['subject']
                )
                self.cli.display_info(f"Still receiving from: {sender_address}")

        # Display effectiveness report
        self.cli.display_info("\nUnsubscribe Effectiveness Report\n")

        from rich.table import Table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Sender", style="cyan", width=40)
        table.add_column("Unsubscribed", style="white", width=12)
        table.add_column("Emails After", style="yellow", width=12)
        table.add_column("Status", style="green", width=15)

        for entry in report:
            unsub_date = entry['unsubscribed_date'][:10] if entry['unsubscribed_date'] else 'N/A'
            table.add_row(
                entry['sender_address'],
                unsub_date,
                str(entry['email_count_after_unsub']),
                entry['effectiveness']
            )

        self.cli.console.print(table)

    def run_daily_mode(self):
        """
        Run in daily mode - show one suggestion for the day.
        """
        self.cli.display_welcome()
        self.cli.display_info("Successfully authenticated!\n")

        # First, update reading patterns from recent emails
        self.cli.display_info("Analyzing your recent email reading patterns...")
        self.gmail.analyze_reading_patterns(
            days_back=30,  # Look at last month
            max_emails=200,
            update_db=True  # Update the database with patterns
        )

        # Get daily suggestion
        daily_suggestion = self.db.get_daily_suggestion()

        if not daily_suggestion:
            self.cli.display_info("\nNo suggestions for today! Your inbox looks clean.")
            return

        # Display the suggestion
        sender_address = daily_suggestion['sender_address']
        engagement = daily_suggestion['engagement_score']
        total = daily_suggestion['total_received']
        unread = daily_suggestion['total_unread']

        self.cli.console.print()
        self.cli.console.print(Panel(
            f"[bold cyan]Today's Unsubscribe Suggestion[/bold cyan]\n\n"
            f"[yellow]Sender:[/yellow] {sender_address}\n"
            f"[yellow]Total emails:[/yellow] {total}\n"
            f"[yellow]Unread:[/yellow] {unread}\n"
            f"[yellow]Engagement:[/yellow] {engagement:.0f}% (you read {engagement:.0f}% of their emails)\n\n"
            f"[dim]This sender ranks as one of your least engaged subscriptions.[/dim]",
            border_style="cyan"
        ))

        # Ask if user wants to unsubscribe
        if not self.cli.console.input("\n[cyan]Unsubscribe from this sender? (y/n):[/cyan] ").lower().startswith('y'):
            self.cli.display_info("Skipped. Maybe tomorrow!")
            return

        # Get email from sender and unsubscribe
        self.cli.display_info(f"\nFetching recent email from {sender_address}...")
        emails = self.gmail.get_emails_from_sender(sender_address, max_results=1)

        if not emails or not emails[0].get('unsubscribe_links'):
            self.cli.display_error("Could not find unsubscribe link for this sender.")
            return

        # Process unsubscribe in headless mode
        self.cli.display_info("Unsubscribing (headless mode)...\n")
        asyncio.run(self._process_unsubscribes([emails[0]], override_headless=True))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Gmail Unsubscriber - Automatically unsubscribe from unwanted emails'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (no visible window)'
    )
    parser.add_argument(
        '--max-emails',
        type=int,
        default=50,
        help='Maximum number of emails to scan per batch (default: 50)'
    )
    parser.add_argument(
        '--check-effectiveness',
        action='store_true',
        help='Check effectiveness of previous unsubscribes'
    )
    parser.add_argument(
        '--suggest',
        action='store_true',
        help='Analyze reading patterns and suggest subscriptions to unsubscribe from'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Number of days to look back for analysis (default: 90, used with --suggest)'
    )
    parser.add_argument(
        '--daily',
        action='store_true',
        help='Show one subscription suggestion for the day (perfect for daily cron jobs)'
    )

    args = parser.parse_args()

    app = GmailUnsubscriber(headless=args.headless, max_emails=args.max_emails)

    try:
        if args.check_effectiveness:
            # Authenticate first
            if not app.gmail.authenticate():
                print("Failed to authenticate with Gmail.")
                return
            app.check_effectiveness()
        elif args.daily:
            # Authenticate first
            if not app.gmail.authenticate():
                print("Failed to authenticate with Gmail.")
                return
            app.run_daily_mode()
        elif args.suggest:
            # Authenticate first
            if not app.gmail.authenticate():
                print("Failed to authenticate with Gmail.")
                return
            app.run_suggest_mode(days_back=args.days)
        else:
            app.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
