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
        self.console.print("[dim]Review 3 at a time. Mark selections with checkbox syntax: [x] or numbers[/dim]\n")

        # Track selected indices across batches
        selected_indices = set()

        # Display offenders in batches of 3 with detailed cards
        batch_size = 3
        for batch_start in range(0, len(offenders), batch_size):
            batch = offenders[batch_start:batch_start + batch_size]

            for idx, offender in enumerate(batch, start=batch_start + 1):
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
                email_preview = self._truncate(email_preview, 70) if email_preview else "[dim]No preview[/dim]"

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

                # Check if selected
                checkbox = "[x]" if idx in selected_indices else "[ ]"

                # Create detailed card for each subscription
                card_content = (
                    f"{checkbox} [bold cyan]#{idx}. {sender_name}[/bold cyan]\n"
                    f"[dim]{sender_address}[/dim]\n\n"
                    f"[green]🤖 What's their deal?[/green]\n{hot_take}\n\n"
                    f"[blue]📧 Latest email:[/blue] {email_preview}\n\n"
                    f"[yellow]📊 Your stats:[/yellow]\n"
                    f"  • Total: {offender['total_emails']} emails  "
                    f"• Unread: {offender['unread_emails']} ({offender['unread_percentage']:.0f}%)  "
                    f"• Last read: {last_read_str}"
                )

                self.console.print(Panel(
                    card_content,
                    border_style="cyan" if idx in selected_indices else "dim",
                    padding=(1, 2)
                ))

            # Show pagination prompt between batches with selection option
            if batch_start + batch_size < len(offenders):
                remaining = len(offenders) - (batch_start + batch_size)
                self.console.print(f"\n[dim]─── {remaining} more subscription(s) below ───[/dim]")
                user_input = self.console.input(
                    "[cyan]Enter numbers to select (e.g. 1,3), Enter for next 3, or 'done' to finish:[/cyan] "
                )

                if user_input.lower() in ['done', 'd', 'q']:
                    self.console.print("[yellow]Finished viewing.[/yellow]\n")
                    break
                elif user_input.strip():
                    # Parse selection
                    new_selections = self._parse_selection_input(user_input, len(offenders))
                    selected_indices.update(new_selections)
                    # Show confirmation
                    if new_selections:
                        self.console.print(f"[green]✓ Selected #{', #'.join(map(str, sorted(new_selections)))}[/green]")

                self.console.print()
            else:
                # Last batch - allow final selections
                user_input = self.console.input(
                    "[cyan]Enter numbers to select from this batch (or press Enter if done):[/cyan] "
                )
                if user_input.strip():
                    new_selections = self._parse_selection_input(user_input, len(offenders))
                    selected_indices.update(new_selections)

        self.console.print()

        # Convert selected indices to offender objects
        if not selected_indices:
            self.console.print("[yellow]No subscriptions selected.[/yellow]")
            return []

        selected_offenders = [offenders[i - 1] for i in sorted(selected_indices)]

        # Show summary and confirm
        self.console.print(f"[yellow]You selected {len(selected_offenders)} subscription(s) to unsubscribe from:[/yellow]")
        for idx in sorted(selected_indices):
            self.console.print(f"  #{idx}. {offenders[idx - 1]['sender_name']}")

        self.console.print()
        if Confirm.ask("[bold]Proceed with unsubscribing?[/bold]", default=True):
            return selected_offenders

        return []

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
