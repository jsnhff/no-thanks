#!/usr/bin/env python3
"""
Gmail Unsubscriber - Automatically unsubscribe from unwanted emails with your approval.
"""

import asyncio
import sys
import argparse
from datetime import datetime
from email.utils import parseaddr
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables from .env file
load_dotenv()

from src.gmail_client import GmailClient
from src.cli_interface import CLIInterface
from src.unsubscribe_agent import unsubscribe_from_emails
from src.database import UnsubscribeDatabase
from src.chief_of_staff import ChiefOfStaff
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel


class GmailUnsubscriber:
    """Main application orchestrator."""

    def __init__(self, headless: bool = False, max_emails: int = 50, skip_ai: bool = False):
        self.gmail = GmailClient()
        self.cli = CLIInterface()
        self.db = UnsubscribeDatabase()
        self.headless = headless
        self.max_emails = max_emails
        self.skip_ai = skip_ai

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
            # Scan for emails with progress indicator
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.cli.console
            ) as progress:
                scan_task = progress.add_task(
                    f"[cyan]Scanning for emails with unsubscribe links (max {self.max_emails})...",
                    total=None
                )
                emails = self.gmail.find_emails_with_unsubscribe(max_results=self.max_emails)
                progress.update(scan_task, completed=True)

            # Filter out already processed emails
            emails = [email for email in emails if not self.db.is_already_processed(email['id'])]

            if not emails:
                self.cli.display_info("No new emails with unsubscribe links found.")
                if not self.cli.ask_continue():
                    break
                continue

            self.cli.display_info(f"✓ Found {len(emails)} email(s) with unsubscribe links\n")

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
                progress_callback=update_progress,
                skip_ai=self.skip_ai  # Skip AI summaries if flag is set
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

        # Use override if provided, otherwise use instance setting
        use_headless = override_headless if override_headless is not None else self.headless

        # Unsubscribe from each email with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.cli.console
        ) as progress:
            unsub_task = progress.add_task(
                f"[cyan]Processing {total} unsubscribe request(s)...",
                total=total
            )

            # Unsubscribe from each email (pass database for learning)
            results = await unsubscribe_from_emails(emails, headless=use_headless, db=self.db)

            for idx, result in enumerate(results, 1):
                email = result['email']
                success = result['success']
                message = result['message']

                # Update progress bar
                progress.update(unsub_task, completed=idx)

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

                # Record link pattern result for learning
                self.db.record_link_pattern_result(unsubscribe_link, success)

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
        learning_stats = self.db.get_link_learning_stats()

        self.cli.display_info("\n" + "=" * 60)
        self.cli.display_info("Overall Statistics")
        self.cli.display_info("=" * 60)
        self.cli.console.print(f"Total subscriptions tracked: {stats['total_subscriptions']}")
        self.cli.console.print(f"Successfully unsubscribed: {stats['unsubscribed_count']}")
        self.cli.console.print(f"Effective unsubscribes: {stats['effective_unsubscribes']}")
        self.cli.console.print(f"Still receiving emails from: {stats['failed_unsubscribes']}")
        self.cli.console.print(f"Total attempts: {stats['total_attempts']}")
        self.cli.console.print(f"Successful attempts: {stats['successful_attempts']}")

        # Show learning stats if available
        if learning_stats['domains_learned'] > 0:
            self.cli.console.print()
            self.cli.display_info("Learning & Improvement")
            self.cli.display_info("=" * 60)
            self.cli.console.print(f"Domains learned: {learning_stats['domains_learned']}")
            self.cli.console.print(f"Link patterns tracked: {learning_stats['total_patterns']}")
            if learning_stats['best_pattern']:
                success_rate = 0
                if learning_stats['best_pattern_success'] + learning_stats['best_pattern_failure'] > 0:
                    success_rate = (learning_stats['best_pattern_success'] /
                                  (learning_stats['best_pattern_success'] + learning_stats['best_pattern_failure'])) * 100
                self.cli.console.print(
                    f"Most successful pattern: '{learning_stats['best_pattern']}' "
                    f"({learning_stats['best_pattern_success']} successes, {success_rate:.0f}% success rate)"
                )

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

    def run_chief_of_staff_mode(self, days_back: int = 30):
        """
        Run Chief of Staff mode - goal-aligned inbox intelligence report.

        Args:
            days_back: Number of days to analyze (default: 30)
        """
        self.cli.display_welcome()
        self.cli.display_info(f"Analyzing your inbox from the last {days_back} days...\n")

        # Create Chief of Staff instance
        cos = ChiefOfStaff(self.gmail, self.db)

        # Run analysis with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.cli.console
        ) as progress:
            fetch_task = progress.add_task("[cyan]Fetching emails...", total=None)
            analyze_task = progress.add_task("[green]Analyzing relationships...", total=None, visible=False)
            goals_task = progress.add_task("[yellow]Checking goal alignment...", total=None, visible=False)

            def update_progress(stage, current=None, total=None):
                if stage == 'fetch':
                    if current and total:
                        if progress.tasks[fetch_task].total is None:
                            progress.update(fetch_task, total=total)
                        progress.update(fetch_task, completed=current)
                elif stage == 'analyze':
                    progress.update(fetch_task, completed=progress.tasks[fetch_task].total or 100)
                    if not progress.tasks[analyze_task].visible:
                        progress.update(analyze_task, visible=True, total=100)
                    progress.update(analyze_task, completed=current or 50)
                elif stage == 'goals':
                    progress.update(analyze_task, completed=100)
                    if not progress.tasks[goals_task].visible:
                        progress.update(goals_task, visible=True, total=100)
                    progress.update(goals_task, completed=current or 50)
                elif stage == 'done':
                    progress.update(goals_task, completed=100)

            analysis = cos.analyze_inbox_health(days_back=days_back, progress_callback=update_progress)

        self.cli.console.print()

        if not analysis:
            self.cli.display_error("Failed to generate Chief of Staff report")
            return

        # Save analysis to database for historical tracking
        self.db.save_chief_of_staff_analysis(analysis)

        # Get trends if available
        trends = self.db.get_chief_of_staff_trends(limit=5)

        # Display the report
        self.cli.display_chief_of_staff_report(analysis, trends)

        # Ask if user wants to unsubscribe from noise offenders
        noise_analysis = analysis.get('noise_analysis', {})
        worst_offenders = noise_analysis.get('worst_offenders', [])

        if worst_offenders:
            self.cli.console.print()
            if self.cli.console.input("\n[cyan]Would you like to unsubscribe from top noise offenders? (y/n):[/cyan] ").lower().startswith('y'):
                # Get number to unsubscribe from
                count_str = self.cli.console.input("[cyan]How many? (1-10):[/cyan] ") or "5"
                try:
                    count = min(int(count_str), 10)
                    self._unsubscribe_from_noise_offenders(worst_offenders[:count])
                except ValueError:
                    self.cli.display_error("Invalid number")

    def _unsubscribe_from_noise_offenders(self, offenders: List[Dict]):
        """Unsubscribe from noise offender senders."""
        self.cli.display_info(f"\nFetching recent emails from {len(offenders)} noise offender(s)...\n")

        emails_to_unsubscribe = []
        for offender in offenders:
            sender_address = offender['sender']
            emails = self.gmail.get_emails_from_sender(sender_address, max_results=1)
            if emails and emails[0].get('unsubscribe_links'):
                emails_to_unsubscribe.append(emails[0])

        if not emails_to_unsubscribe:
            self.cli.display_error("Could not find unsubscribe links for these senders.")
            return

        # Process unsubscribes
        asyncio.run(self._process_unsubscribes(emails_to_unsubscribe, override_headless=True))

    def run_aggressive_mode(self, days_back: int = 90, engagement_threshold: int = 10):
        """
        Run aggressive bulk unsubscribe mode.

        Args:
            days_back: Number of days to analyze
            engagement_threshold: Only target senders with engagement below this % (default: 10)
        """
        self.cli.display_welcome()
        self.cli.display_info("Successfully authenticated!\n")

        # Analyze reading patterns with larger batch
        self.cli.display_info(f"Analyzing your email reading patterns over the last {days_back} days...")
        self.cli.display_info(f"Looking for senders with <{engagement_threshold}% engagement (emails you don't read)\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.cli.console
        ) as progress:
            fetch_task = progress.add_task("[cyan]Fetching emails...", total=None)
            ai_task = progress.add_task("[green]Analyzing patterns...", total=None, visible=False)

            def update_progress(stage, current, total):
                if stage == 'fetch':
                    if progress.tasks[fetch_task].total is None:
                        progress.update(fetch_task, total=total)
                    progress.update(fetch_task, completed=current)
                elif stage == 'ai':
                    if not progress.tasks[ai_task].visible:
                        progress.update(ai_task, visible=True, total=total)
                    progress.update(ai_task, completed=current)

            # Analyze with larger batch for aggressive mode
            worst_offenders = self.gmail.analyze_reading_patterns(
                days_back=days_back,
                max_emails=self.max_emails * 10,  # Analyze 10x more emails
                update_db=True,
                progress_callback=update_progress
            )

        self.cli.console.print()

        # Filter for low engagement senders only
        low_engagement_senders = [
            sender for sender in worst_offenders
            if sender.get('engagement_score', 100) < engagement_threshold
        ]

        if not low_engagement_senders:
            self.cli.display_info("No low-engagement senders found. Your inbox looks clean!")
            return

        # Show preview of what will be cut
        self.cli.console.print(Panel(
            f"[bold yellow]⚠️  AGGRESSIVE MODE - PREVIEW[/bold yellow]\n\n"
            f"Found [bold cyan]{len(low_engagement_senders)}[/bold cyan] senders with <{engagement_threshold}% engagement\n"
            f"These are subscriptions you rarely or never read.",
            border_style="yellow"
        ))

        # Display detailed preview table
        from rich.table import Table
        table = Table(show_header=True, header_style="bold magenta", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Sender", style="cyan", width=35)
        table.add_column("Emails", style="yellow", justify="right", width=8)
        table.add_column("Read", style="green", justify="right", width=8)
        table.add_column("Engagement", style="red", justify="right", width=12)

        for idx, sender in enumerate(low_engagement_senders[:50], 1):  # Show first 50
            sender_name = sender.get('sender_name', sender['sender_address'])
            if len(sender_name) > 35:
                sender_name = sender_name[:32] + "..."

            total = sender.get('total_received', 0)
            unread = sender.get('total_unread', 0)
            read = total - unread
            engagement = sender.get('engagement_score', 0)

            table.add_row(
                str(idx),
                sender_name,
                str(total),
                str(read),
                f"{engagement:.0f}%"
            )

        if len(low_engagement_senders) > 50:
            table.add_row(
                "...",
                f"[dim]+ {len(low_engagement_senders) - 50} more...[/dim]",
                "",
                "",
                ""
            )

        self.cli.console.print(table)
        self.cli.console.print()

        # Get confirmation
        self.cli.console.print(
            f"[yellow]This will unsubscribe from [bold]{len(low_engagement_senders)}[/bold] senders.[/yellow]\n"
            f"[dim]You'll get a report with resubscribe links in case you want to undo any.[/dim]\n"
        )

        response = self.cli.console.input("[cyan]Proceed with bulk unsubscribe? (yes/no):[/cyan] ")
        if response.lower() not in ['yes', 'y']:
            self.cli.display_info("Cancelled. No changes made.")
            return

        # Collect emails to unsubscribe
        emails_to_unsubscribe = []
        resubscribe_data = []  # Track for report

        self.cli.display_info(f"\nFetching unsubscribe links from {len(low_engagement_senders)} senders...\n")

        for sender_data in low_engagement_senders:
            sender_address = sender_data['sender_address']
            sender_name = sender_data.get('sender_name', sender_address)

            # Try cached unsubscribe links first
            if sender_data.get('latest_unsubscribe_links'):
                email_data = {
                    'id': f"aggressive_{sender_address}",
                    'from': f"{sender_name} <{sender_address}>",
                    'subject': sender_data['sample_subjects'][0] if sender_data['sample_subjects'] else '',
                    'snippet': '',
                    'unsubscribe_links': sender_data['latest_unsubscribe_links']
                }
                emails_to_unsubscribe.append(email_data)
                resubscribe_data.append({
                    'sender_name': sender_name,
                    'sender_address': sender_address,
                    'emails_sent': sender_data.get('total_received', 0),
                    'engagement': sender_data.get('engagement_score', 0),
                    'unsubscribe_link': sender_data['latest_unsubscribe_links'][0]
                })
            else:
                # Fetch recent email
                emails = self.gmail.get_emails_from_sender(sender_address, max_results=1)
                if emails and emails[0].get('unsubscribe_links'):
                    emails_to_unsubscribe.append(emails[0])
                    resubscribe_data.append({
                        'sender_name': sender_name,
                        'sender_address': sender_address,
                        'emails_sent': sender_data.get('total_received', 0),
                        'engagement': sender_data.get('engagement_score', 0),
                        'unsubscribe_link': emails[0]['unsubscribe_links'][0]
                    })

        if not emails_to_unsubscribe:
            self.cli.display_error("Could not find unsubscribe links for selected senders.")
            return

        # Process unsubscribes in headless mode
        self.cli.display_info(f"\nProcessing {len(emails_to_unsubscribe)} unsubscribes in headless mode...\n")
        asyncio.run(self._process_unsubscribes(emails_to_unsubscribe, override_headless=True))

        # Generate resubscribe report
        self._generate_resubscribe_report(resubscribe_data)

    def _generate_resubscribe_report(self, resubscribe_data: List[Dict]):
        """Generate a report with resubscribe links."""
        self.cli.console.print("\n" + "=" * 80)
        self.cli.console.print(Panel(
            "[bold green]✓ Bulk Unsubscribe Complete![/bold green]\n\n"
            f"Unsubscribed from [cyan]{len(resubscribe_data)}[/cyan] senders.\n"
            "Here are the unsubscribe links in case you want to resubscribe to any:",
            border_style="green"
        ))

        from rich.table import Table
        table = Table(show_header=True, header_style="bold cyan", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Sender", style="cyan", width=35)
        table.add_column("Stats", style="yellow", width=25)
        table.add_column("Resubscribe Link", style="blue", width=50)

        for idx, data in enumerate(resubscribe_data, 1):
            sender_name = data['sender_name']
            if len(sender_name) > 35:
                sender_name = sender_name[:32] + "..."

            stats = f"{data['emails_sent']} emails, {data['engagement']:.0f}% read"
            link = data['unsubscribe_link']

            # Truncate link if too long
            if len(link) > 50:
                link = link[:47] + "..."

            table.add_row(str(idx), sender_name, stats, link)

        self.cli.console.print(table)

        # Save to file
        report_file = f"resubscribe_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write("RESUBSCRIBE REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total unsubscribes: {len(resubscribe_data)}\n\n")

            for idx, data in enumerate(resubscribe_data, 1):
                f.write(f"\n{idx}. {data['sender_name']} ({data['sender_address']})\n")
                f.write(f"   Sent you: {data['emails_sent']} emails\n")
                f.write(f"   Your engagement: {data['engagement']:.0f}%\n")
                f.write(f"   Unsubscribe link: {data['unsubscribe_link']}\n")

        self.cli.console.print(f"\n[green]✓ Full report saved to:[/green] [cyan]{report_file}[/cyan]")
        self.cli.console.print("[dim]You can use the unsubscribe links above to resubscribe if needed.[/dim]\n")


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
    parser.add_argument(
        '--chief-of-staff',
        action='store_true',
        help='Run Chief of Staff mode - goal-aligned inbox intelligence report'
    )
    parser.add_argument(
        '--aggressive',
        action='store_true',
        help='Aggressive bulk unsubscribe mode - preview and bulk unsubscribe from low-engagement senders'
    )
    parser.add_argument(
        '--engagement-threshold',
        type=int,
        default=10,
        help='Engagement threshold percentage for aggressive mode (default: 10, used with --aggressive)'
    )
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Skip AI summaries for faster performance'
    )

    args = parser.parse_args()

    app = GmailUnsubscriber(headless=args.headless, max_emails=args.max_emails, skip_ai=args.no_ai)

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
        elif args.chief_of_staff:
            # Authenticate first
            if not app.gmail.authenticate():
                print("Failed to authenticate with Gmail.")
                return
            app.run_chief_of_staff_mode(days_back=args.days)
        elif args.aggressive:
            # Authenticate first
            if not app.gmail.authenticate():
                print("Failed to authenticate with Gmail.")
                return
            app.run_aggressive_mode(
                days_back=args.days,
                engagement_threshold=args.engagement_threshold
            )
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
