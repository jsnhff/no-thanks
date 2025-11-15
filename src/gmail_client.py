"""Gmail API client for fetching and analyzing emails."""

import os
import pickle
from typing import List, Dict, Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from collections import defaultdict
from datetime import datetime, timedelta
from email.utils import parseaddr
import re
import base64
import anthropic
import os
import json

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.settings.basic'
]


class GmailClient:
    """Client for interacting with Gmail API."""

    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.anthropic_client = None
        self.user_profile = None

        # Load user profile if available
        try:
            profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_profile.json')
            if os.path.exists(profile_path):
                with open(profile_path, 'r') as f:
                    self.user_profile = json.load(f)
        except:
            pass  # Profile is optional

        # Initialize Anthropic if API key is available
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Anthropic client: {e}")
                pass  # Summaries are optional

    def authenticate(self) -> bool:
        """Authenticate with Gmail API."""
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(f"Error: {self.credentials_path} not found!")
                    print("Please download OAuth credentials from Google Cloud Console.")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)
        return True

    def find_emails_with_unsubscribe(self, max_results: int = 100) -> List[Dict]:
        """
        Find emails that likely contain unsubscribe links.

        Args:
            max_results: Maximum number of emails to scan

        Returns:
            List of email data dictionaries
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        emails_with_unsubscribe = []

        try:
            # Query for emails with unsubscribe links across all categories
            # Searches in all folders except sent, drafts, and trash
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q='(unsubscribe OR list-unsubscribe) -in:sent -in:draft -in:trash'
            ).execute()

            messages = results.get('messages', [])

            for message in messages:
                email_data = self._extract_email_data(message['id'])
                if email_data and email_data.get('unsubscribe_links'):
                    emails_with_unsubscribe.append(email_data)

        except Exception as e:
            print(f"Error fetching emails: {e}")

        return emails_with_unsubscribe

    def _extract_email_data(self, message_id: str) -> Optional[Dict]:
        """
        Extract relevant data from an email message.

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with email data or None
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = message['payload']['headers']

            # Extract headers
            subject = self._get_header(headers, 'Subject')
            from_email = self._get_header(headers, 'From')
            list_unsubscribe = self._get_header(headers, 'List-Unsubscribe')

            # Get email body
            body = self._get_email_body(message['payload'])

            # Find unsubscribe links
            unsubscribe_links = self._find_unsubscribe_links(body, list_unsubscribe)

            if not unsubscribe_links:
                return None

            return {
                'id': message_id,
                'subject': subject,
                'from': from_email,
                'unsubscribe_links': unsubscribe_links,
                'snippet': message.get('snippet', ''),
            }

        except Exception as e:
            print(f"Error extracting email data for {message_id}: {e}")
            return None

    def _get_header(self, headers: List[Dict], name: str) -> str:
        """Get header value by name."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ''

    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload."""
        body = ''

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/plain' and not body:
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        else:
            if 'body' in payload and 'data' in payload['body']:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        return body

    def _find_unsubscribe_links(self, body: str, list_unsubscribe: str) -> List[str]:
        """
        Find unsubscribe links in email body and headers.

        Args:
            body: Email body text
            list_unsubscribe: List-Unsubscribe header value

        Returns:
            List of unsubscribe URLs
        """
        links = []

        # Check List-Unsubscribe header first (most reliable)
        if list_unsubscribe:
            # Extract URLs from angle brackets
            header_links = re.findall(r'<(https?://[^>]+)>', list_unsubscribe)
            links.extend(header_links)

        # Find unsubscribe links in body
        if body:
            # Look for common unsubscribe link patterns
            patterns = [
                r'href=["\'](https?://[^"\']*unsubscribe[^"\']*)["\']',
                r'href=["\'](https?://[^"\']*opt-out[^"\']*)["\']',
                r'href=["\'](https?://[^"\']*preferences[^"\']*)["\']',
            ]

            for pattern in patterns:
                body_links = re.findall(pattern, body, re.IGNORECASE)
                links.extend(body_links)

        # Remove duplicates and clean up
        unique_links = []
        seen = set()
        for link in links:
            # Decode HTML entities if needed
            link = link.replace('&amp;', '&')
            if link not in seen and link.startswith('http'):
                seen.add(link)
                unique_links.append(link)

        return unique_links

    def _summarize_email_content(self, snippet: str, subject: str) -> str:
        """
        Generate a 3-sentence summary of what's IN this specific email.

        Args:
            snippet: Email body preview/snippet
            subject: Email subject line

        Returns:
            3-sentence summary of email content
        """
        if not self.anthropic_client or not snippet:
            return ""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=60,
                messages=[{
                    "role": "user",
                    "content": f"""In ONE short sentence (max 15 words), what's in this email?

Subject: {subject}
Preview: {snippet[:300]}

Examples:
- "Flash sale on winter jackets, 60% off until midnight."
- "New design trends report with 15 case studies."

Your summary:"""
                }]
            )

            return message.content[0].text.strip()

        except Exception as e:
            print(f"Error generating email summary: {e}")
            return ""  # Summaries are optional

    def _generate_summary(self, sender_name: str, sample_subjects: List[str]) -> str:
        """
        Generate a brutally honest, personalized hot take about what this sender actually sends.

        Args:
            sender_name: Name of sender
            sample_subjects: List of sample subject lines

        Returns:
            Hot take summary or empty string if unavailable
        """
        if not self.anthropic_client or not sample_subjects:
            return ""

        try:
            subjects_text = "\n".join([f"- {s}" for s in sample_subjects[:5]])

            # Build personalized context if profile is available
            user_context = ""
            if self.user_profile:
                interests = ", ".join(self.user_profile.get("interests", [])[:5])
                high_value = ", ".join(self.user_profile.get("inbox_preferences", {}).get("high_value_sources", [])[:3])
                low_value = ", ".join(self.user_profile.get("inbox_preferences", {}).get("low_value_sources", [])[:3])

                user_context = f"""
User context:
- Key interests: {interests}
- Values: {high_value}
- Dislikes: {low_value}
"""

            message = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=80,
                messages=[{
                    "role": "user",
                    "content": f"""Based on these subject lines from {sender_name}, write ONE brutally honest sentence (max 20 words):

{subjects_text}

What do they want from you? Is it useful or noise?

Examples:
- "Daily deals spam trying to drive impulse purchases. Marketing noise."
- "Design trends newsletter. Useful for your creative work."
- "Travel promotions with FOMO tactics. Not relevant."

Your one sentence:"""
                }]
            )

            summary = message.content[0].text.strip()
            # Allow longer summaries since we want more detail
            return summary if len(summary) < 250 else summary[:247] + "..."

        except Exception as e:
            print(f"Warning: AI summary generation failed for {sender_name}: {e}")
            return ""  # Summaries are optional, don't fail if they don't work

    def analyze_reading_patterns(self, days_back: int = 90, max_emails: int = 500,
                                update_db: bool = False, progress_callback=None) -> List[Dict]:
        """
        Analyze email reading patterns to identify worst offenders.

        Args:
            days_back: Number of days to look back (default: 90 days)
            max_emails: Maximum number of emails to analyze
            update_db: Whether to update the reading_patterns table in database

        Returns:
            List of sender statistics, sorted by worst offenders
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Calculate date for query
        since_date = datetime.now() - timedelta(days=days_back)
        date_str = since_date.strftime('%Y/%m/%d')

        sender_stats = defaultdict(lambda: {
            'sender_address': '',
            'sender_name': '',
            'total_emails': 0,
            'unread_emails': 0,
            'read_emails': 0,
            'unread_percentage': 0.0,
            'has_unsubscribe': False,
            'sample_subjects': [],
            'latest_unsubscribe_links': [],
            'last_email_timestamp': 0,
            'last_read_timestamp': 0,
            'oldest_email_timestamp': 0,
            'days_since_last_read': None,
            'relevance_score': 0.0,
            'summary': ''
        })

        try:
            # Query for emails with unsubscribe links in any category
            # This searches across all folders, not just promotions
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_emails,
                q=f'(unsubscribe OR list-unsubscribe) after:{date_str} -in:sent -in:draft -in:trash'
            ).execute()

            messages = results.get('messages', [])
            total_messages = len(messages)

            for idx, message in enumerate(messages, 1):
                if progress_callback:
                    progress_callback('fetch', idx, total_messages)

                # Get message details
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                headers = msg['payload']['headers']
                from_email = self._get_header(headers, 'From')
                subject = self._get_header(headers, 'Subject')
                list_unsubscribe = self._get_header(headers, 'List-Unsubscribe')

                # Get email timestamp (in milliseconds)
                email_timestamp = int(msg.get('internalDate', 0))

                # Check if read/unread
                is_unread = 'UNREAD' in msg.get('labelIds', [])

                # Extract sender address
                sender_name, sender_address = parseaddr(from_email)
                if not sender_address:
                    continue

                # Update stats
                stats = sender_stats[sender_address]
                stats['sender_address'] = sender_address
                stats['sender_name'] = sender_name or sender_address
                stats['total_emails'] += 1

                # Track timestamps
                if email_timestamp > stats['last_email_timestamp']:
                    stats['last_email_timestamp'] = email_timestamp

                if stats['oldest_email_timestamp'] == 0 or email_timestamp < stats['oldest_email_timestamp']:
                    stats['oldest_email_timestamp'] = email_timestamp

                if is_unread:
                    stats['unread_emails'] += 1
                else:
                    stats['read_emails'] += 1
                    # Track when we last read an email from this sender
                    if email_timestamp > stats['last_read_timestamp']:
                        stats['last_read_timestamp'] = email_timestamp

                # Store sample subjects (max 3)
                if len(stats['sample_subjects']) < 3:
                    stats['sample_subjects'].append(subject)

                # Check for unsubscribe links
                if list_unsubscribe or 'unsubscribe' in subject.lower():
                    stats['has_unsubscribe'] = True

                    # Try to get unsubscribe link AND body content from latest email
                    if not stats['latest_unsubscribe_links']:
                        body = self._get_email_body(msg['payload'])
                        links = self._find_unsubscribe_links(body, list_unsubscribe)
                        if links:
                            stats['latest_unsubscribe_links'] = links
                            # Store snippet/body for AI summary later
                            # Use Gmail's snippet (preview text) or extract from body
                            snippet = msg.get('snippet', '')
                            if snippet:
                                stats['latest_email_snippet'] = snippet
                            else:
                                # Extract text from body (strip HTML)
                                import html
                                import re
                                clean_text = re.sub('<[^<]+?>', '', body)
                                clean_text = html.unescape(clean_text)
                                stats['latest_email_snippet'] = clean_text[:500]  # First 500 chars

        except Exception as e:
            print(f"Error analyzing reading patterns: {e}")

        # Calculate percentages, staleness, and relevance scores
        worst_offenders = []
        now = datetime.now().timestamp() * 1000  # Convert to milliseconds

        # Get list of senders to skip (unsubscribed + recently attempted)
        senders_to_skip = set()
        if update_db:
            from src.database import UnsubscribeDatabase
            db = UnsubscribeDatabase()
            senders_to_skip = db.get_senders_to_skip()

        ai_progress_count = 0
        total_to_process = len([s for s in sender_stats.values() if s.get('sample_subjects')])

        for sender_address, stats in sender_stats.items():
            # Skip if already unsubscribed or recently attempted
            if sender_address in senders_to_skip:
                continue
            if stats['total_emails'] > 0:
                stats['unread_percentage'] = (stats['unread_emails'] / stats['total_emails']) * 100

                # Calculate days since last read
                if stats['last_read_timestamp'] > 0:
                    days_since_read = (now - stats['last_read_timestamp']) / (1000 * 60 * 60 * 24)
                    stats['days_since_last_read'] = int(days_since_read)
                else:
                    # Never read any email from this sender
                    stats['days_since_last_read'] = 999  # Essentially infinite

                # Calculate relevance score (lower is worse/less relevant)
                # Factors:
                # - Unread percentage (higher = worse)
                # - Days since last read (more days = worse)
                # - Total unread count (more unread = worse)
                # - Email frequency (more emails but never read = worse)

                unread_factor = stats['unread_percentage']
                staleness_factor = min(stats['days_since_last_read'], 365) / 365 * 100  # Cap at 1 year, normalize to 0-100
                volume_factor = min(stats['unread_emails'] / 50, 1) * 100  # Normalize to 0-100

                # Weighted score: prioritize never-read (staleness) and high unread percentage
                stats['relevance_score'] = (
                    staleness_factor * 0.4 +  # 40% weight on staleness
                    unread_factor * 0.4 +      # 40% weight on unread percentage
                    volume_factor * 0.2         # 20% weight on volume
                )

                # Update database with reading patterns if requested
                if update_db:
                    from src.database import UnsubscribeDatabase
                    db = UnsubscribeDatabase()
                    db.update_reading_pattern(
                        sender_address,
                        stats['total_emails'],
                        stats['read_emails'],
                        stats['unread_emails']
                    )

                # Generate AI summaries for this sender
                if stats['sample_subjects']:
                    ai_progress_count += 1
                    if progress_callback:
                        progress_callback('ai', ai_progress_count, total_to_process)

                    # Generate overall sender assessment
                    stats['summary'] = self._generate_summary(
                        stats['sender_name'],
                        stats['sample_subjects']
                    )

                    # Generate specific email content summary
                    if stats.get('latest_email_snippet') and stats['sample_subjects']:
                        stats['email_content_summary'] = self._summarize_email_content(
                            stats['latest_email_snippet'],
                            stats['sample_subjects'][0]
                        )

                # Only include senders with unsubscribe links and at least 3 emails
                if stats['has_unsubscribe'] and stats['total_emails'] >= 3:
                    worst_offenders.append(stats)

        # Sort by relevance score (highest = worst/least relevant)
        worst_offenders.sort(
            key=lambda x: x['relevance_score'],
            reverse=True
        )

        return worst_offenders

    def get_emails_from_sender(self, sender_address: str, max_results: int = 1) -> List[Dict]:
        """
        Get recent emails from a specific sender with unsubscribe links.

        Args:
            sender_address: Email address to search for
            max_results: Number of emails to fetch

        Returns:
            List of email data dictionaries
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        emails = []

        try:
            # Search for emails from this sender
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=f'from:{sender_address}'
            ).execute()

            messages = results.get('messages', [])

            for message in messages:
                email_data = self._extract_email_data(message['id'])
                if email_data:
                    emails.append(email_data)

        except Exception as e:
            print(f"Error fetching emails from {sender_address}: {e}")

        return emails
