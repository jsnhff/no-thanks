"""Terminal CLI interface for reviewing and approving unsubscribe actions."""

from typing import List, Dict
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text


class CLIInterface:
    """Interactive CLI for email unsubscribe approval."""

    def __init__(self):
        self.console = Console()

    def display_welcome(self):
        """Display welcome message."""
        welcome_text = Text()
        welcome_text.append("Gmail Unsubscriber\n", style="bold cyan")
        welcome_text.append("Automatically unsubscribe from unwanted emails with your approval", style="dim")

        self.console.print(Panel(welcome_text, border_style="cyan"))
        self.console.print()

    def display_scan_progress(self, count: int):
        """Display scanning progress."""
        self.console.print(f"[cyan]Scanning emails... Found {count} with unsubscribe links[/cyan]")

    def display_emails(self, emails: List[Dict]) -> List[Dict]:
        """
        Display emails and get user approval for which to unsubscribe.

        Args:
            emails: List of email data dictionaries

        Returns:
            List of approved emails to unsubscribe from
        """
        if not emails:
            self.console.print("[yellow]No emails with unsubscribe links found.[/yellow]")
            return []

        self.console.print(f"\n[bold]Found {len(emails)} emails with unsubscribe links:[/bold]\n")

        # Display emails in a table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("From", style="cyan", width=30)
        table.add_column("Subject", style="white", width=50)
        table.add_column("Links", style="green", width=6)

        for idx, email in enumerate(emails, 1):
            from_addr = self._truncate(email['from'], 30)
            subject = self._truncate(email['subject'], 50)
            num_links = str(len(email['unsubscribe_links']))

            table.add_row(str(idx), from_addr, subject, num_links)

        self.console.print(table)
        self.console.print()

        # Get user selection
        approved = self._get_user_selection(emails)
        return approved

    def _get_user_selection(self, emails: List[Dict]) -> List[Dict]:
        """Get user selection of which emails to unsubscribe from."""
        self.console.print("[bold]Select emails to unsubscribe from:[/bold]")
        self.console.print("  - Enter numbers separated by commas (e.g., 1,3,5)")
        self.console.print("  - Enter a range (e.g., 1-5)")
        self.console.print("  - Enter 'all' to unsubscribe from all")
        self.console.print("  - Enter 'none' or leave blank to skip")
        self.console.print()

        selection = Prompt.ask("[cyan]Your selection[/cyan]", default="none")

        if selection.lower() in ['none', '']:
            return []

        if selection.lower() == 'all':
            if Confirm.ask(f"[yellow]Unsubscribe from all {len(emails)} emails?[/yellow]"):
                return emails
            return []

        # Parse selection
        selected_indices = self._parse_selection(selection, len(emails))

        if not selected_indices:
            self.console.print("[red]Invalid selection. No emails selected.[/red]")
            return []

        approved = [emails[i] for i in selected_indices]

        # Confirm selection
        self.console.print(f"\n[yellow]You selected {len(approved)} email(s) to unsubscribe from.[/yellow]")
        if Confirm.ask("Proceed with unsubscribing?", default=True):
            return approved

        return []

    def _parse_selection(self, selection: str, max_index: int) -> List[int]:
        """
        Parse user selection string into list of indices.

        Args:
            selection: User input string (e.g., "1,3,5" or "1-5")
            max_index: Maximum valid index

        Returns:
            List of zero-based indices
        """
        indices = set()

        parts = selection.split(',')
        for part in parts:
            part = part.strip()

            # Handle ranges (e.g., "1-5")
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start_idx = int(start.strip()) - 1
                    end_idx = int(end.strip()) - 1

                    if 0 <= start_idx < max_index and 0 <= end_idx < max_index:
                        indices.update(range(start_idx, end_idx + 1))
                except ValueError:
                    continue

            # Handle single numbers
            else:
                try:
                    idx = int(part) - 1
                    if 0 <= idx < max_index:
                        indices.add(idx)
                except ValueError:
                    continue

        return sorted(list(indices))

    def display_email_details(self, email: Dict):
        """Display detailed information about an email."""
        self.console.print()
        self.console.print(Panel(
            f"[bold]From:[/bold] {email['from']}\n"
            f"[bold]Subject:[/bold] {email['subject']}\n"
            f"[bold]Preview:[/bold] {email['snippet']}\n"
            f"[bold]Unsubscribe links found:[/bold] {len(email['unsubscribe_links'])}",
            title=f"Email Details",
            border_style="cyan"
        ))

        for idx, link in enumerate(email['unsubscribe_links'], 1):
            self.console.print(f"  {idx}. {self._truncate(link, 80)}")

        self.console.print()

    def display_unsubscribe_progress(self, current: int, total: int, email: Dict):
        """Display progress while unsubscribing."""
        self.console.print(
            f"[cyan]Unsubscribing {current}/{total}:[/cyan] {self._truncate(email['from'], 40)}"
        )

    def display_unsubscribe_result(self, email: Dict, success: bool, message: str = ""):
        """Display result of unsubscribe attempt."""
        if success:
            self.console.print(f"  [green]✓[/green] Successfully unsubscribed from: {email['from']}")
        else:
            self.console.print(f"  [red]✗[/red] Failed to unsubscribe from: {email['from']}")
            if message:
                self.console.print(f"    [dim]{message}[/dim]")

    def display_summary(self, total: int, successful: int, failed: int):
        """Display summary of unsubscribe operations."""
        self.console.print()
        summary = Text()
        summary.append("\nUnsubscribe Summary\n", style="bold")
        summary.append(f"Total processed: {total}\n", style="white")
        summary.append(f"Successful: {successful}\n", style="green")
        summary.append(f"Failed: {failed}\n", style="red")

        self.console.print(Panel(summary, border_style="cyan"))

    def display_manual_unsubscribe_links(self, failed_items: List[Dict]):
        """Display links for manual unsubscribe of failed attempts."""
        if not failed_items:
            return

        self.console.print()
        self.console.print(Panel(
            "[bold yellow]⚠️  Manual Action Required[/bold yellow]\n\n"
            f"The following {len(failed_items)} subscription(s) couldn't be unsubscribed automatically.\n"
            "They may require CAPTCHA, login, or have complex unsubscribe flows.\n\n"
            "[dim]Click the links below to unsubscribe manually:[/dim]",
            border_style="yellow",
            padding=(1, 2)
        ))

        for item in failed_items:
            sender = item.get('sender', 'Unknown')
            email = item.get('email', '')
            links = item.get('links', [])

            self.console.print(f"\n[bold cyan]• {sender}[/bold cyan]")
            if email:
                self.console.print(f"  [dim]{email}[/dim]")

            if links:
                for idx, link in enumerate(links, 1):
                    # Make links clickable in terminal
                    self.console.print(f"  [link={link}]Link {idx}: {self._truncate(link, 80)}[/link]")
            else:
                self.console.print("  [red]No unsubscribe link found - may need to contact sender[/red]")

        self.console.print()

    def display_error(self, message: str):
        """Display an error message."""
        self.console.print(f"[red bold]Error:[/red bold] {message}")

    def display_info(self, message: str):
        """Display an info message."""
        self.console.print(f"[cyan]{message}[/cyan]")

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def ask_continue(self) -> bool:
        """Ask user if they want to continue scanning for more emails."""
        return Confirm.ask("\n[cyan]Scan for more emails?[/cyan]", default=False)

    def display_worst_offenders(self, offenders: List[Dict]) -> List[Dict]:
        """
        Display worst offender senders and get user approval.

        Args:
            offenders: List of sender statistics

        Returns:
            List of approved senders to unsubscribe from
        """
        if not offenders:
            self.console.print("[yellow]No senders found that match the criteria.[/yellow]")
            return []

        self.console.print(f"\n[bold]Found {len(offenders)} subscription(s) you rarely/never read:[/bold]\n")
        self.console.print("[dim]Ranked by staleness & relevance (never/rarely read + time since last read)[/dim]\n")
        self.console.print("[dim]Review one at a time - Keep or Cut with a knife! 🔪[/dim]\n")

        # Track which to cut
        to_cut = []

        # Show one card at a time with keep/cut decision
        for idx, offender in enumerate(offenders, 1):
            sender_name = offender['sender_name']
            sender_address = offender['sender_address']

            # Use AI hot take if available, otherwise use sample subject
            hot_take = offender.get('summary', '')
            if not hot_take and offender['sample_subjects']:
                hot_take = offender['sample_subjects'][0]
            hot_take = hot_take if hot_take else "[dim]No description[/dim]"

            # Get email content summary (AI-generated) or fallback to subject
            email_preview = offender.get('email_content_summary', '')
            if not email_preview and offender['sample_subjects']:
                email_preview = offender['sample_subjects'][0]
            email_preview = email_preview if email_preview else "[dim]No preview[/dim]"

            # Format last read
            days_since_read = offender.get('days_since_last_read', 999)
            if days_since_read >= 999:
                last_read_str = "Never"
            elif days_since_read == 0:
                last_read_str = "Today"
            elif days_since_read == 1:
                last_read_str = "1 day ago"
            elif days_since_read < 7:
                last_read_str = f"{days_since_read} days ago"
            elif days_since_read < 30:
                weeks = days_since_read // 7
                last_read_str = f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = days_since_read // 30
                last_read_str = f"{months} month{'s' if months > 1 else ''} ago"

            # Create detailed card for this subscription
            card_content = (
                f"[bold cyan]{sender_name}[/bold cyan]\n"
                f"[dim]{sender_address}[/dim]\n\n"
                f"[green]🤖 What's their deal?[/green]\n{hot_take}\n\n"
                f"[blue]📧 Latest email:[/blue]\n{email_preview}\n\n"
                f"[yellow]📊 Your stats:[/yellow]\n"
                f"  • Total: {offender['total_emails']} emails\n"
                f"  • Unread: {offender['unread_emails']} ({offender['unread_percentage']:.0f}%)\n"
                f"  • Last read: {last_read_str}"
            )

            self.console.print(Panel(
                card_content,
                title=f"[bold white]Subscription {idx} of {len(offenders)}[/bold white]",
                border_style="cyan",
                padding=(1, 2)
            ))

            # Quick Keep or Cut decision
            self.console.print()
            self.console.print("[dim]k[/dim] = keep  |  [dim]c[/dim] = cut 🔪  |  [dim]q[/dim] = quit")
            choice = Prompt.ask(
                "[bold cyan]Your choice[/bold cyan]",
                choices=["keep", "k", "cut", "c", "quit", "q"],
                default="keep",
                show_choices=False
            )
            self.console.print()

            if choice in ["cut", "c"]:
                to_cut.append(offender)
                self.console.print(f"[red]🔪 Marked for cutting[/red] ({len(to_cut)} total)\n")
            elif choice in ["keep", "k"]:
                self.console.print(f"[green]✓ Keeping[/green]\n")
            elif choice in ["quit", "q"]:
                self.console.print("[yellow]Stopped reviewing. Processing cuts so far...[/yellow]\n")
                break

        # Show summary if anything was cut
        if not to_cut:
            self.console.print("[yellow]No subscriptions marked for cutting.[/yellow]")
            return []

        # Show summary
        self.console.print(f"[bold red]🔪 Ready to cut {len(to_cut)} subscription(s):[/bold red]")
        for offender in to_cut:
            self.console.print(f"  • {offender['sender_name']}")

        self.console.print()
        if Confirm.ask("[bold]Proceed with unsubscribing?[/bold]", default=True):
            return to_cut

        return []

    def display_chief_of_staff_report(self, analysis: Dict, trends: List[Dict] = None):
        """Display the Chief of Staff inbox intelligence report."""
        if not analysis:
            self.console.print("[red]No analysis data available[/red]")
            return

        period = analysis.get('period_days', 30)
        total_emails = analysis.get('total_emails', 0)

        # Header with trends indicator
        trend_indicator = ""
        if trends and len(trends) >= 2:
            current_signal = analysis.get('goal_alignment', {}).get('inbox_composition_signal_pct', 0)
            prev_signal = trends[1]['signal_percentage'] if len(trends) > 1 else current_signal
            diff = current_signal - prev_signal

            if diff > 0:
                trend_indicator = f"  [green]↑ +{diff:.1f}% signal vs last time[/green]"
            elif diff < 0:
                trend_indicator = f"  [red]↓ {diff:.1f}% signal vs last time[/red]"
            else:
                trend_indicator = f"  [yellow]→ No change vs last time[/yellow]"

        self.console.print()
        self.console.print(Panel(
            f"[bold cyan]Chief of Staff Inbox Report[/bold cyan]\n\n"
            f"[dim]Analysis Period: Last {period} days | Total Emails: {total_emails}[/dim]"
            f"{trend_indicator}",
            border_style="cyan",
            padding=(1, 2)
        ))

        # VIP Relationship Insights
        vip_insights = analysis.get('vip_insights', {})
        if vip_insights:
            self.console.print()
            self.console.print("[bold yellow]👥 VIP RELATIONSHIP TRACKER[/bold yellow]")
            self.console.print(f"[dim]Tracking your most important relationships[/dim]\n")

            vips = vip_insights.get('vips', [])
            if vips:
                table = Table(show_header=True, header_style="bold magenta", box=None)
                table.add_column("Person", style="cyan", width=30)
                table.add_column("Tier", style="yellow", width=12)
                table.add_column("Emails", style="white", width=8)
                table.add_column("Unread", style="red", width=8)
                table.add_column("Status", style="green", width=30)

                for vip in vips[:10]:  # Top 10
                    name = vip['sender_name'] or vip['sender_address']
                    tier = vip['relationship_tier'].title()
                    total = vip['total_emails']
                    unread = vip['unread_count']

                    # Status message
                    days_since = vip.get('days_since_last_email', 0)
                    if unread > 3:
                        status = f"⚠️  {unread} emails need attention"
                    elif days_since > 14:
                        status = f"💤 Last email {days_since}d ago"
                    else:
                        status = "✓ Engaged"

                    table.add_row(
                        self._truncate(name, 30),
                        tier,
                        str(total),
                        str(unread) if unread > 0 else "-",
                        status
                    )

                self.console.print(table)

                # Show clickable links for VIPs with unread emails
                vips_with_unread = [v for v in vips[:10] if v['unread_count'] > 0 and v.get('unread_email_ids')]
                if vips_with_unread:
                    self.console.print("\n[dim]Quick Links (click to open in Gmail):[/dim]")
                    for vip in vips_with_unread[:5]:  # Top 5 with unread
                        name = self._truncate(vip['sender_name'] or vip['sender_address'], 30)
                        email_ids = vip.get('unread_email_ids', [])
                        if email_ids:
                            link = f"https://mail.google.com/mail/u/0/#inbox/{email_ids[0]}"
                            self.console.print(f"  • {name}: [link={link}]Open unread email[/link]")
            else:
                self.console.print("[dim]No VIPs identified yet[/dim]")

        # Signal vs Noise Analysis
        self.console.print()
        noise_analysis = analysis.get('noise_analysis', {})
        if noise_analysis:
            self.console.print("[bold yellow]🧹 SIGNAL vs NOISE ANALYSIS[/bold yellow]")
            self.console.print(f"[dim]Quantifying the clutter in your inbox[/dim]\n")

            signal = noise_analysis.get('signal_count', 0)
            noise = noise_analysis.get('noise_count', 0)
            noise_pct = noise_analysis.get('noise_percentage', 0)
            time_wasted = noise_analysis.get('estimated_time_wasted_hours', 0)

            self.console.print(f"  📊 Inbox Composition: [green]{signal} signal[/green] | [red]{noise} noise[/red] ([red]{noise_pct}%[/red])")
            self.console.print(f"  ⏱️  Estimated Time Wasted: [yellow]{time_wasted} hours[/yellow] this period")
            self.console.print(f"  💡 Potential Monthly Savings: [cyan]{round(time_wasted * (30/analysis['period_days']), 1)} hours/month[/cyan]\n")

            worst = noise_analysis.get('worst_offenders', [])
            if worst:
                self.console.print("[dim]Top Noise Offenders:[/dim]")
                for idx, offender in enumerate(worst[:5], 1):
                    self.console.print(f"  {idx}. {offender['sender']} ([red]{offender['count']} emails[/red])")

        # Goal Alignment
        self.console.print()
        goal_alignment = analysis.get('goal_alignment', {})
        if goal_alignment:
            self.console.print("[bold yellow]🎯 GOAL ALIGNMENT CHECK[/bold yellow]")
            self.console.print(f"[dim]How your inbox is helping/hurting your Q4 2025 goals[/dim]\n")

            email_debt = goal_alignment.get('email_debt_score', 0)
            vips_pending = goal_alignment.get('vips_needing_response', 0)
            signal_pct = goal_alignment.get('inbox_composition_signal_pct', 0)

            self.console.print(f"  📬 Email Debt Score: [{'red' if email_debt > 15 else 'yellow' if email_debt > 5 else 'green'}]{email_debt} VIP emails unread[/{'red' if email_debt > 15 else 'yellow' if email_debt > 5 else 'green'}]")
            self.console.print(f"  ✉️  VIPs Needing Response: [yellow]{vips_pending}[/yellow]")
            self.console.print(f"  📈 Signal Quality: [{'green' if signal_pct > 40 else 'yellow' if signal_pct > 25 else 'red'}]{signal_pct}% high-value[/{'green' if signal_pct > 40 else 'yellow' if signal_pct > 25 else 'red'}]\n")

            goal_insights = goal_alignment.get('goal_insights', [])
            if goal_insights:
                self.console.print("[dim]Goal-Specific Insights:[/dim]\n")

                for insight in goal_insights:
                    status_emoji = "✅" if insight['status'] == 'on_track' else "⚠️ "
                    status_color = "green" if insight['status'] == 'on_track' else "yellow"

                    self.console.print(f"  {status_emoji} [{status_color}]{insight['goal']}[/{status_color}]")
                    self.console.print(f"     {insight['insight']}")
                    self.console.print(f"     [dim]→ {insight['action']}[/dim]\n")

        # Summary with historical context
        self.console.print()

        summary_text = "[bold cyan]✨ CHIEF OF STAFF RECOMMENDATION[/bold cyan]\n\n"
        summary_text += f"Your inbox is [{'green' if goal_alignment.get('inbox_composition_signal_pct', 0) > 40 else 'yellow'}]{goal_alignment.get('inbox_composition_signal_pct', 0)}% signal[/{'green' if goal_alignment.get('inbox_composition_signal_pct', 0) > 40 else 'yellow'}]. "
        summary_text += f"You have [{('red' if email_debt > 15 else 'yellow' if email_debt > 5 else 'green')}]{email_debt} VIP emails[/{('red' if email_debt > 15 else 'yellow' if email_debt > 5 else 'green')}] waiting.\n\n"

        # Add trend context if available
        if trends and len(trends) >= 2:
            noise_prev = trends[1]['noise_percentage']
            noise_curr = noise_analysis.get('noise_percentage', 0)
            noise_diff = noise_curr - noise_prev

            if noise_diff < -5:
                summary_text += f"[green]🎉 Great progress! Noise down {abs(noise_diff):.1f}% since last check.[/green]\n"
            elif noise_diff > 5:
                summary_text += f"[red]📈 Noise increased {noise_diff:.1f}% - time to clean up![/red]\n"

        summary_text += f"\n[dim]Top Priority: {goal_insights[0]['action'] if goal_insights else 'Keep up your inbox hygiene'}[/dim]"

        self.console.print(Panel(
            summary_text,
            border_style="cyan",
            padding=(1, 2)
        ))
        self.console.print()

    def _parse_selection_input(self, selection: str, max_index: int) -> set:
        """Parse user selection input like '1,3,5' or '1-3'."""
        indices = set()
        parts = selection.split(',')

        for part in parts:
            part = part.strip()
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start_idx = int(start.strip())
                    end_idx = int(end.strip())
                    if 1 <= start_idx <= max_index and 1 <= end_idx <= max_index:
                        indices.update(range(start_idx, end_idx + 1))
                except ValueError:
                    continue
            else:
                try:
                    idx = int(part)
                    if 1 <= idx <= max_index:
                        indices.add(idx)
                except ValueError:
                    continue

        return indices

    def _get_user_selection_offenders(self, offenders: List[Dict]) -> List[Dict]:
        """Get user selection of which offenders to unsubscribe from."""
        self.console.print("[bold]Select senders to unsubscribe from:[/bold]")
        self.console.print("  - Enter numbers separated by commas (e.g., 1,3,5)")
        self.console.print("  - Enter a range (e.g., 1-5)")
        self.console.print("  - Enter 'all' to unsubscribe from all")
        self.console.print("  - Enter 'top N' to select top N worst offenders (e.g., 'top 5')")
        self.console.print("  - Enter 'none' or leave blank to skip")
        self.console.print()

        selection = Prompt.ask("[cyan]Your selection[/cyan]", default="none")

        if selection.lower() in ['none', '']:
            return []

        if selection.lower() == 'all':
            if Confirm.ask(f"[yellow]Unsubscribe from all {len(offenders)} senders?[/yellow]"):
                return offenders
            return []

        # Handle "top N" selection
        if selection.lower().startswith('top '):
            try:
                n = int(selection.split()[1])
                top_n = offenders[:min(n, len(offenders))]
                self.console.print(f"\n[yellow]You selected the top {len(top_n)} worst offender(s).[/yellow]")
                if Confirm.ask("Proceed with unsubscribing?", default=True):
                    return top_n
                return []
            except (ValueError, IndexError):
                self.console.print("[red]Invalid 'top N' format. No senders selected.[/red]")
                return []

        # Parse selection
        selected_indices = self._parse_selection(selection, len(offenders))

        if not selected_indices:
            self.console.print("[red]Invalid selection. No senders selected.[/red]")
            return []

        approved = [offenders[i] for i in selected_indices]

        # Confirm selection
        self.console.print(f"\n[yellow]You selected {len(approved)} sender(s) to unsubscribe from.[/yellow]")
        if Confirm.ask("Proceed with unsubscribing?", default=True):
            return approved

        return []
