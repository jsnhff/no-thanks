"""Chief of Staff - Goal-aligned inbox intelligence and relationship tracking."""

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from email.utils import parseaddr


class ChiefOfStaff:
    """
    Chief of Staff agent that provides goal-aligned inbox intelligence.
    Helps you lead visibly, deepen connections, and maintain balance.
    """

    def __init__(self, gmail_client, database, user_profile_path='user_profile.json'):
        self.gmail = gmail_client
        self.db = database
        self.user_profile = self._load_user_profile(user_profile_path)

    def _load_user_profile(self, profile_path: str) -> Dict:
        """Load user profile with goals and preferences."""
        try:
            full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), profile_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load user profile: {e}")

        return {}

    def analyze_inbox_health(self, days_back: int = 30, progress_callback=None) -> Dict:
        """
        Comprehensive inbox health analysis aligned with user goals.

        Args:
            days_back: Number of days to analyze
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with all Chief of Staff insights
        """
        # Calculate date range
        since_date = datetime.now() - timedelta(days=days_back)
        date_str = since_date.strftime('%Y/%m/%d')

        try:
            # Fetch recent emails
            if progress_callback:
                progress_callback('fetch', 0, 100)

            results = self.gmail.service.users().messages().list(
                userId='me',
                maxResults=500,
                q=f'after:{date_str} -in:sent -in:draft -in:trash'
            ).execute()

            messages = results.get('messages', [])

            if progress_callback:
                progress_callback('fetch', 100, 100)

            # Analyze the emails
            if progress_callback:
                progress_callback('analyze', 0, 100)

            vip_insights = self._analyze_relationships(messages, progress_callback)

            if progress_callback:
                progress_callback('analyze', 100, 100)

            noise_analysis = self._analyze_signal_vs_noise(messages)

            if progress_callback:
                progress_callback('goals', 0, 100)

            goal_alignment = self._analyze_goal_alignment(messages, vip_insights, noise_analysis)

            if progress_callback:
                progress_callback('done')

            return {
                'period_days': days_back,
                'total_emails': len(messages),
                'vip_insights': vip_insights,
                'noise_analysis': noise_analysis,
                'goal_alignment': goal_alignment,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error analyzing inbox: {e}")
            return {}

    def _analyze_relationships(self, messages: List[Dict], progress_callback=None) -> Dict:
        """
        VIP Relationship Tracker - identify important people and engagement patterns.
        """
        sender_data = defaultdict(lambda: {
            'sender_address': '',
            'sender_name': '',
            'total_emails': 0,
            'unread_count': 0,
            'read_count': 0,
            'timestamps': [],
            'subjects': [],
            'unread_email_ids': [],  # Store IDs for linking
            'avg_response_time': None,
            'days_since_last_email': None,
            'is_real_human': False,
            'relationship_tier': 'unknown'
        })

        total_messages = len(messages)
        for idx, message in enumerate(messages, 1):
            try:
                # Update progress
                if progress_callback and idx % 10 == 0:
                    progress = int((idx / total_messages) * 100)
                    progress_callback('analyze', progress, 100)

                msg = self.gmail.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                from_email = headers.get('From', '')
                subject = headers.get('Subject', '')

                sender_name, sender_address = parseaddr(from_email)
                if not sender_address:
                    continue

                is_unread = 'UNREAD' in msg.get('labelIds', [])
                timestamp = int(msg.get('internalDate', 0))

                data = sender_data[sender_address]
                data['sender_address'] = sender_address
                data['sender_name'] = sender_name or sender_address
                data['total_emails'] += 1
                data['timestamps'].append(timestamp)

                if len(data['subjects']) < 3:
                    data['subjects'].append(subject)

                if is_unread:
                    data['unread_count'] += 1
                    # Store up to 3 unread email IDs for linking
                    if len(data['unread_email_ids']) < 3:
                        data['unread_email_ids'].append(message['id'])
                else:
                    data['read_count'] += 1

                # Check if this looks like a real human
                data['is_real_human'] = self._is_real_human_email(sender_address, sender_name, subject)

            except Exception:
                continue

        # Calculate metrics for each sender
        now = datetime.now().timestamp() * 1000
        vips = []

        for sender_address, data in sender_data.items():
            if data['total_emails'] == 0:
                continue

            # Calculate engagement rate
            engagement_rate = (data['read_count'] / data['total_emails']) * 100

            # Calculate days since last email
            if data['timestamps']:
                last_timestamp = max(data['timestamps'])
                days_since = (now - last_timestamp) / (1000 * 60 * 60 * 24)
                data['days_since_last_email'] = int(days_since)

            # Determine relationship tier based on profile + engagement
            data['relationship_tier'] = self._classify_relationship_tier(
                sender_address,
                sender_name,
                engagement_rate,
                data['is_real_human']
            )
            data['engagement_rate'] = engagement_rate

            # VIPs are: real humans with high engagement or leadership/creative contacts
            if data['relationship_tier'] in ['leadership', 'creative', 'personal'] or \
               (data['is_real_human'] and engagement_rate > 70):
                vips.append(data)

        # Sort VIPs by importance
        vips.sort(key=lambda x: (
            x['relationship_tier'] == 'personal',
            x['relationship_tier'] == 'leadership',
            x['relationship_tier'] == 'creative',
            x['engagement_rate']
        ), reverse=True)

        return {
            'vip_count': len(vips),
            'vips': vips[:20],  # Top 20 VIPs
            'total_unique_senders': len(sender_data)
        }

    def _analyze_signal_vs_noise(self, messages: List[Dict]) -> Dict:
        """
        Noise Filter Analysis - quantify marketing spam and low-value sources.
        """
        noise_senders = defaultdict(int)
        signal_count = 0
        noise_count = 0

        low_value_keywords = self.user_profile.get('inbox_preferences', {}).get('low_value_sources', [])

        for message in messages:
            try:
                msg = self.gmail.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject']
                ).execute()

                headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                from_email = headers.get('From', '')
                subject = headers.get('Subject', '').lower()

                sender_name, sender_address = parseaddr(from_email)

                # Check if this is noise based on profile
                is_noise = self._is_noise_email(sender_address, sender_name, subject, low_value_keywords)

                if is_noise:
                    noise_count += 1
                    noise_senders[sender_address] += 1
                else:
                    signal_count += 1

            except Exception:
                continue

        # Get worst noise offenders
        worst_offenders = sorted(
            [{'sender': k, 'count': v} for k, v in noise_senders.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]

        total = signal_count + noise_count
        noise_percentage = (noise_count / total * 100) if total > 0 else 0

        # Estimate time wasted (assuming 30 seconds per noise email to process/delete)
        estimated_time_wasted_hours = (noise_count * 0.5) / 60

        return {
            'total_analyzed': total,
            'signal_count': signal_count,
            'noise_count': noise_count,
            'noise_percentage': round(noise_percentage, 1),
            'worst_offenders': worst_offenders,
            'estimated_time_wasted_hours': round(estimated_time_wasted_hours, 1)
        }

    def _analyze_goal_alignment(self, messages: List[Dict], vip_insights: Dict, noise_analysis: Dict) -> Dict:
        """
        Goal-Aligned Analysis - how is your inbox helping/hurting your Q4 2025 goals?
        """
        goals = self.user_profile.get('current_goals_q4_2025', [])

        # Calculate email debt (unread VIP emails)
        vip_unread = sum(vip['unread_count'] for vip in vip_insights.get('vips', []))

        # Calculate average age of unread VIP emails
        vip_emails_needing_response = [
            vip for vip in vip_insights.get('vips', [])
            if vip['unread_count'] > 0
        ]

        # Inbox composition
        total = noise_analysis['total_analyzed']
        signal_pct = round((noise_analysis['signal_count'] / total * 100) if total > 0 else 0, 1)

        # Goal-specific insights
        goal_insights = []

        # Goal 1: Lead visibly at Shopify
        shopify_vips = [v for v in vip_insights.get('vips', []) if v['relationship_tier'] == 'leadership']
        if shopify_vips:
            shopify_unread = sum(v['unread_count'] for v in shopify_vips)
            goal_insights.append({
                'goal': 'Lead more visibly at Shopify',
                'status': 'needs_attention' if shopify_unread > 5 else 'on_track',
                'insight': f"{shopify_unread} unread emails from Shopify leadership peers",
                'action': 'Review Shopify communications' if shopify_unread > 5 else 'Keep up the engagement'
            })

        # Goal 2: Deepen LA connections
        personal_vips = [v for v in vip_insights.get('vips', []) if v['relationship_tier'] == 'personal']
        if personal_vips:
            personal_unread = sum(v['unread_count'] for v in personal_vips)
            stale_connections = [v for v in personal_vips if v.get('days_since_last_email', 0) > 14]
            goal_insights.append({
                'goal': 'Deepen friendships and community connections',
                'status': 'needs_attention' if len(stale_connections) > 3 else 'on_track',
                'insight': f"{personal_unread} unread personal emails, {len(stale_connections)} connections haven't emailed in 2+ weeks",
                'action': 'Reach out to friends you haven\'t heard from' if stale_connections else 'Connections are active'
            })

        # Goal 3: Be present / maintain balance
        goal_insights.append({
            'goal': 'Be present as husband and dad',
            'status': 'on_track' if noise_analysis['noise_percentage'] < 60 else 'needs_attention',
            'insight': f"{noise_analysis['noise_percentage']}% of inbox is noise, wasting ~{noise_analysis['estimated_time_wasted_hours']}hrs",
            'action': f"Cut noise to reclaim {noise_analysis['estimated_time_wasted_hours']}hrs/month for family" if noise_analysis['noise_percentage'] > 60 else 'Noise is under control'
        })

        # Goal 4: Launch Regender.xyz
        creative_vips = [v for v in vip_insights.get('vips', []) if v['relationship_tier'] == 'creative']
        if creative_vips:
            creative_unread = sum(v['unread_count'] for v in creative_vips)
            goal_insights.append({
                'goal': 'Launch and promote Regender.xyz',
                'status': 'on_track' if creative_unread < 5 else 'needs_attention',
                'insight': f"{creative_unread} unread emails from creative collaborators",
                'action': 'Check for Regender-related opportunities' if creative_unread > 0 else 'Stay engaged with creative network'
            })

        return {
            'email_debt_score': vip_unread,
            'vips_needing_response': len(vip_emails_needing_response),
            'inbox_composition_signal_pct': signal_pct,
            'goal_insights': goal_insights
        }

    def _is_real_human_email(self, sender_address: str, sender_name: str, subject: str) -> bool:
        """Detect if email is from a real human vs automated system."""
        # Common automated sender patterns
        automated_patterns = [
            'noreply', 'no-reply', 'donotreply', 'notifications', 'automated',
            'newsletter', 'digest', 'updates', 'team@', 'support@', 'hello@',
            'info@', 'news@', 'marketing@', 'promo'
        ]

        sender_lower = sender_address.lower()

        # Check for automated patterns
        if any(pattern in sender_lower for pattern in automated_patterns):
            return False

        # Check for personal email domains
        personal_domains = ['gmail.com', 'icloud.com', 'me.com', 'hey.com', 'proton.me']
        domain = sender_address.split('@')[-1].lower()
        if domain in personal_domains:
            return True

        # Check if sender name looks like a real person (has space, proper case)
        if sender_name and ' ' in sender_name and any(c.isupper() for c in sender_name):
            return True

        return False

    def _is_noise_email(self, sender_address: str, sender_name: str, subject: str, low_value_keywords: List[str]) -> bool:
        """Determine if email is noise based on user profile."""
        subject_lower = subject.lower()
        sender_lower = sender_address.lower()

        # Check against low-value keywords from profile
        for keyword in low_value_keywords:
            if keyword.lower() in subject_lower or keyword.lower() in sender_lower:
                return True

        # Common noise patterns
        noise_indicators = [
            'sale', 'discount', 'off', 'deal', 'promo', 'limited time',
            'unsubscribe', 'click here', 'act now', 'don\'t miss',
            'special offer', 'free shipping', '% off', 'save now'
        ]

        if any(indicator in subject_lower for indicator in noise_indicators):
            return True

        return False

    def _generate_gmail_link(self, email_id: str) -> str:
        """Generate a direct link to email in Gmail web interface."""
        return f"https://mail.google.com/mail/u/0/#inbox/{email_id}"

    def _classify_relationship_tier(self, sender_address: str, sender_name: str,
                                   engagement_rate: float, is_real_human: bool) -> str:
        """Classify relationship tier based on profile and engagement."""

        if not self.user_profile:
            return 'unknown'

        sender_lower = sender_address.lower()
        name_lower = sender_name.lower()

        # Check for Shopify leadership
        if 'shopify' in sender_lower and is_real_human:
            return 'leadership'

        # Check for creative collaborators (personal domains with high engagement)
        personal_domains = ['gmail.com', 'icloud.com', 'me.com', 'hey.com', 'proton.me']
        domain = sender_address.split('@')[-1].lower()
        if domain in personal_domains and is_real_human and engagement_rate > 60:
            return 'personal'

        # Creative/collaborator signals
        creative_indicators = ['design', 'artist', 'writer', 'creative', 'studio']
        if any(ind in name_lower or ind in sender_lower for ind in creative_indicators):
            return 'creative'

        # High engagement real humans are likely personal
        if is_real_human and engagement_rate > 80:
            return 'personal'

        return 'other'
