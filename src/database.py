"""SQLite database for tracking unsubscribe actions and monitoring effectiveness."""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager


class UnsubscribeDatabase:
    """Database for tracking email unsubscriptions and their effectiveness."""

    def __init__(self, db_path: str = 'unsubscribe_history.db'):
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Table for subscription sources (sender addresses)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_address TEXT NOT NULL UNIQUE,
                    sender_name TEXT,
                    first_seen_date TEXT NOT NULL,
                    unsubscribed_date TEXT,
                    unsubscribe_status TEXT DEFAULT 'active',
                    last_email_date TEXT,
                    email_count_before_unsub INTEGER DEFAULT 0,
                    email_count_after_unsub INTEGER DEFAULT 0,
                    notes TEXT
                )
            ''')

            # Table for individual unsubscribe attempts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unsubscribe_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id INTEGER NOT NULL,
                    email_id TEXT NOT NULL,
                    attempt_date TEXT NOT NULL,
                    unsubscribe_link TEXT,
                    success BOOLEAN NOT NULL,
                    message TEXT,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
                )
            ''')

            # Table for monitoring emails received after unsubscribe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS post_unsubscribe_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id INTEGER NOT NULL,
                    email_id TEXT NOT NULL,
                    received_date TEXT NOT NULL,
                    subject TEXT,
                    days_after_unsub INTEGER,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
                )
            ''')

            # Table for tracking reading engagement (to improve suggestions)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reading_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_address TEXT NOT NULL,
                    total_received INTEGER DEFAULT 0,
                    total_read INTEGER DEFAULT 0,
                    total_unread INTEGER DEFAULT 0,
                    engagement_score REAL DEFAULT 0.0,
                    last_updated TEXT NOT NULL,
                    UNIQUE(sender_address)
                )
            ''')

            # Table for learning from unsubscribe attempts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unsubscribe_link_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    link_pattern TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_attempt_date TEXT,
                    notes TEXT,
                    UNIQUE(domain, link_pattern)
                )
            ''')

            # Create indices for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sender_address
                ON subscriptions(sender_address)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_email_id
                ON unsubscribe_attempts(email_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_reading_patterns_sender
                ON reading_patterns(sender_address)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_link_patterns_domain
                ON unsubscribe_link_patterns(domain)
            ''')

            # Table for Chief of Staff historical analysis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chief_of_staff_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_date TEXT NOT NULL,
                    period_days INTEGER NOT NULL,
                    total_emails INTEGER DEFAULT 0,
                    vip_count INTEGER DEFAULT 0,
                    signal_count INTEGER DEFAULT 0,
                    noise_count INTEGER DEFAULT 0,
                    noise_percentage REAL DEFAULT 0,
                    email_debt_score INTEGER DEFAULT 0,
                    signal_percentage REAL DEFAULT 0,
                    time_wasted_hours REAL DEFAULT 0,
                    analysis_data TEXT
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cos_history_date
                ON chief_of_staff_history(analysis_date)
            ''')

    def add_subscription(self, sender_address: str, sender_name: str = "") -> int:
        """
        Add or get a subscription entry.

        Args:
            sender_address: Email address of sender
            sender_name: Display name of sender

        Returns:
            Subscription ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if subscription exists
            cursor.execute(
                'SELECT id FROM subscriptions WHERE sender_address = ?',
                (sender_address,)
            )
            result = cursor.fetchone()

            if result:
                return result['id']

            # Create new subscription
            cursor.execute('''
                INSERT INTO subscriptions (sender_address, sender_name, first_seen_date)
                VALUES (?, ?, ?)
            ''', (sender_address, sender_name, datetime.now().isoformat()))

            return cursor.lastrowid

    def record_unsubscribe_attempt(
        self,
        subscription_id: int,
        email_id: str,
        unsubscribe_link: str,
        success: bool,
        message: str = ""
    ):
        """
        Record an unsubscribe attempt.

        Args:
            subscription_id: ID of the subscription
            email_id: Gmail message ID
            unsubscribe_link: URL used for unsubscribe
            success: Whether the attempt was successful
            message: Additional message/error
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Record attempt
            cursor.execute('''
                INSERT INTO unsubscribe_attempts
                (subscription_id, email_id, attempt_date, unsubscribe_link, success, message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                subscription_id,
                email_id,
                datetime.now().isoformat(),
                unsubscribe_link,
                success,
                message
            ))

            # Update subscription if successful
            if success:
                cursor.execute('''
                    UPDATE subscriptions
                    SET unsubscribed_date = ?, unsubscribe_status = 'unsubscribed'
                    WHERE id = ?
                ''', (datetime.now().isoformat(), subscription_id))

    def update_email_counts(self, sender_address: str, received_date: str):
        """
        Update email counts for a subscription.

        Args:
            sender_address: Email address of sender
            received_date: Date email was received
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get subscription
            cursor.execute(
                'SELECT id, unsubscribed_date FROM subscriptions WHERE sender_address = ?',
                (sender_address,)
            )
            result = cursor.fetchone()

            if not result:
                return

            subscription_id = result['id']
            unsubscribed_date = result['unsubscribed_date']

            # Update last email date
            cursor.execute('''
                UPDATE subscriptions
                SET last_email_date = ?
                WHERE id = ?
            ''', (received_date, subscription_id))

            # Increment appropriate counter
            if unsubscribed_date:
                # Check if email is after unsubscribe
                if received_date > unsubscribed_date:
                    cursor.execute('''
                        UPDATE subscriptions
                        SET email_count_after_unsub = email_count_after_unsub + 1
                        WHERE id = ?
                    ''', (subscription_id,))
                else:
                    cursor.execute('''
                        UPDATE subscriptions
                        SET email_count_before_unsub = email_count_before_unsub + 1
                        WHERE id = ?
                    ''', (subscription_id,))
            else:
                cursor.execute('''
                    UPDATE subscriptions
                    SET email_count_before_unsub = email_count_before_unsub + 1
                    WHERE id = ?
                ''', (subscription_id,))

    def record_post_unsubscribe_email(
        self,
        subscription_id: int,
        email_id: str,
        received_date: str,
        subject: str
    ):
        """
        Record an email received after unsubscribing.

        Args:
            subscription_id: ID of the subscription
            email_id: Gmail message ID
            received_date: Date email was received
            subject: Email subject
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get unsubscribe date
            cursor.execute(
                'SELECT unsubscribed_date FROM subscriptions WHERE id = ?',
                (subscription_id,)
            )
            result = cursor.fetchone()

            if not result or not result['unsubscribed_date']:
                return

            unsubscribed_date = datetime.fromisoformat(result['unsubscribed_date'])
            received_datetime = datetime.fromisoformat(received_date)
            days_after = (received_datetime - unsubscribed_date).days

            # Record the email
            cursor.execute('''
                INSERT INTO post_unsubscribe_emails
                (subscription_id, email_id, received_date, subject, days_after_unsub)
                VALUES (?, ?, ?, ?, ?)
            ''', (subscription_id, email_id, received_date, subject, days_after))

    def is_already_processed(self, email_id: str) -> bool:
        """
        Check if an email has already been processed.

        Args:
            email_id: Gmail message ID

        Returns:
            True if already processed
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) as count FROM unsubscribe_attempts WHERE email_id = ?',
                (email_id,)
            )
            result = cursor.fetchone()
            return result['count'] > 0

    def get_all_unsubscribed(self) -> List[Dict]:
        """
        Get all subscriptions that have been unsubscribed.

        Returns:
            List of unsubscribed subscription dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM subscriptions
                WHERE unsubscribe_status = 'unsubscribed'
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_senders_to_skip(self) -> set:
        """
        Get sender addresses that should be skipped in suggestions.
        Includes successfully unsubscribed and recently attempted (even if failed).

        Returns:
            Set of sender addresses to skip
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            skip_senders = set()

            # Get all successfully unsubscribed
            cursor.execute('''
                SELECT sender_address FROM subscriptions
                WHERE unsubscribe_status = 'unsubscribed'
            ''')
            skip_senders.update(row['sender_address'] for row in cursor.fetchall())

            # Get senders with recent attempts (within last 7 days) to avoid showing repeatedly
            # This includes both successful and failed attempts
            cursor.execute('''
                SELECT DISTINCT s.sender_address
                FROM subscriptions s
                INNER JOIN unsubscribe_attempts ua ON s.id = ua.subscription_id
                WHERE ua.attempt_date >= datetime('now', '-7 days')
            ''')
            skip_senders.update(row['sender_address'] for row in cursor.fetchall())

            return skip_senders

    def get_subscription_by_sender(self, sender_address: str) -> Optional[Dict]:
        """
        Get subscription details by sender address.

        Args:
            sender_address: Email address of sender

        Returns:
            Subscription data or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM subscriptions WHERE sender_address = ?',
                (sender_address,)
            )
            result = cursor.fetchone()

            if result:
                return dict(result)
            return None

    def get_unsubscribe_effectiveness_report(self) -> List[Dict]:
        """
        Get a report of unsubscribe effectiveness.

        Returns:
            List of subscriptions with effectiveness metrics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    s.sender_address,
                    s.sender_name,
                    s.unsubscribed_date,
                    s.email_count_after_unsub,
                    s.last_email_date,
                    CASE
                        WHEN s.email_count_after_unsub = 0 THEN 'Effective'
                        WHEN s.email_count_after_unsub <= 2 THEN 'Mostly Effective'
                        ELSE 'Not Effective'
                    END as effectiveness
                FROM subscriptions s
                WHERE s.unsubscribe_status = 'unsubscribed'
                ORDER BY s.email_count_after_unsub DESC, s.unsubscribed_date DESC
            ''')

            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """
        Get overall statistics.

        Returns:
            Dictionary with statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Total subscriptions
            cursor.execute('SELECT COUNT(*) as count FROM subscriptions')
            stats['total_subscriptions'] = cursor.fetchone()['count']

            # Unsubscribed count
            cursor.execute(
                "SELECT COUNT(*) as count FROM subscriptions WHERE unsubscribe_status = 'unsubscribed'"
            )
            stats['unsubscribed_count'] = cursor.fetchone()['count']

            # Successful unsubscribes (no emails after)
            cursor.execute('''
                SELECT COUNT(*) as count FROM subscriptions
                WHERE unsubscribe_status = 'unsubscribed' AND email_count_after_unsub = 0
            ''')
            stats['effective_unsubscribes'] = cursor.fetchone()['count']

            # Failed unsubscribes (still receiving emails)
            cursor.execute('''
                SELECT COUNT(*) as count FROM subscriptions
                WHERE unsubscribe_status = 'unsubscribed' AND email_count_after_unsub > 0
            ''')
            stats['failed_unsubscribes'] = cursor.fetchone()['count']

            # Total unsubscribe attempts
            cursor.execute('SELECT COUNT(*) as count FROM unsubscribe_attempts')
            stats['total_attempts'] = cursor.fetchone()['count']

            # Successful attempts
            cursor.execute('SELECT COUNT(*) as count FROM unsubscribe_attempts WHERE success = 1')
            stats['successful_attempts'] = cursor.fetchone()['count']

            return stats

    def update_reading_pattern(self, sender_address: str, total_received: int,
                              total_read: int, total_unread: int):
        """
        Update reading engagement pattern for a sender.

        Args:
            sender_address: Email address of sender
            total_received: Total emails received from this sender
            total_read: Total emails read from this sender
            total_unread: Total unread emails from this sender
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Calculate engagement score (0-100, higher = more engaged)
            if total_received > 0:
                engagement_score = (total_read / total_received) * 100
            else:
                engagement_score = 0.0

            cursor.execute('''
                INSERT OR REPLACE INTO reading_patterns
                (sender_address, total_received, total_read, total_unread,
                 engagement_score, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                sender_address,
                total_received,
                total_read,
                total_unread,
                engagement_score,
                datetime.now().isoformat()
            ))

    def get_daily_suggestion(self) -> Optional[Dict]:
        """
        Get one subscription suggestion for the day.

        Picks the worst offender that hasn't been suggested recently.

        Returns:
            Sender info for daily suggestion or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get senders with low engagement that we haven't unsubscribed from
            cursor.execute('''
                SELECT rp.sender_address, rp.total_received, rp.total_read,
                       rp.total_unread, rp.engagement_score
                FROM reading_patterns rp
                LEFT JOIN subscriptions s ON rp.sender_address = s.sender_address
                WHERE (s.unsubscribe_status IS NULL OR s.unsubscribe_status != 'unsubscribed')
                  AND rp.total_received >= 3
                  AND rp.engagement_score < 30
                ORDER BY rp.engagement_score ASC, rp.total_unread DESC
                LIMIT 1
            ''')

            result = cursor.fetchone()
            if result:
                return dict(result)
            return None

    def record_link_pattern_result(self, unsubscribe_link: str, success: bool):
        """
        Record the result of an unsubscribe link attempt to learn patterns.

        Args:
            unsubscribe_link: The unsubscribe URL that was tried
            success: Whether the attempt succeeded
        """
        if not unsubscribe_link:
            return

        try:
            from urllib.parse import urlparse
            parsed = urlparse(unsubscribe_link)
            domain = parsed.netloc

            # Extract pattern (e.g., 'unsubscribe', 'opt-out', 'preferences')
            path_lower = parsed.path.lower()
            pattern = 'other'
            if 'unsubscribe' in path_lower:
                pattern = 'unsubscribe'
            elif 'opt-out' in path_lower or 'optout' in path_lower:
                pattern = 'opt-out'
            elif 'preferences' in path_lower or 'settings' in path_lower:
                pattern = 'preferences'
            elif 'remove' in path_lower:
                pattern = 'remove'

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check if pattern exists
                cursor.execute('''
                    SELECT id, success_count, failure_count
                    FROM unsubscribe_link_patterns
                    WHERE domain = ? AND link_pattern = ?
                ''', (domain, pattern))

                result = cursor.fetchone()

                if result:
                    # Update existing pattern
                    if success:
                        cursor.execute('''
                            UPDATE unsubscribe_link_patterns
                            SET success_count = success_count + 1,
                                last_attempt_date = ?
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), result['id']))
                    else:
                        cursor.execute('''
                            UPDATE unsubscribe_link_patterns
                            SET failure_count = failure_count + 1,
                                last_attempt_date = ?
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), result['id']))
                else:
                    # Create new pattern entry
                    cursor.execute('''
                        INSERT INTO unsubscribe_link_patterns
                        (domain, link_pattern, success_count, failure_count, last_attempt_date)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        domain,
                        pattern,
                        1 if success else 0,
                        0 if success else 1,
                        datetime.now().isoformat()
                    ))

        except Exception:
            pass  # Don't fail the main operation if learning fails

    def get_best_link_patterns_for_domain(self, domain: str) -> List[str]:
        """
        Get the most successful link patterns for a domain based on history.

        Args:
            domain: The domain to look up

        Returns:
            List of patterns sorted by success rate (best first)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT link_pattern, success_count, failure_count,
                       CAST(success_count AS FLOAT) / NULLIF(success_count + failure_count, 0) as success_rate
                FROM unsubscribe_link_patterns
                WHERE domain = ?
                  AND (success_count + failure_count) >= 2
                ORDER BY success_rate DESC, success_count DESC
            ''', (domain,))

            results = cursor.fetchall()
            return [row['link_pattern'] for row in results]

    def get_link_learning_stats(self) -> Dict:
        """
        Get statistics about learned link patterns.

        Returns:
            Dictionary with learning statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Total domains learned
            cursor.execute('SELECT COUNT(DISTINCT domain) as count FROM unsubscribe_link_patterns')
            stats['domains_learned'] = cursor.fetchone()['count']

            # Total patterns tracked
            cursor.execute('SELECT COUNT(*) as count FROM unsubscribe_link_patterns')
            stats['total_patterns'] = cursor.fetchone()['count']

            # Most successful pattern overall
            cursor.execute('''
                SELECT link_pattern, SUM(success_count) as total_success, SUM(failure_count) as total_failure
                FROM unsubscribe_link_patterns
                GROUP BY link_pattern
                ORDER BY total_success DESC
                LIMIT 1
            ''')
            result = cursor.fetchone()
            if result:
                stats['best_pattern'] = result['link_pattern']
                stats['best_pattern_success'] = result['total_success']
                stats['best_pattern_failure'] = result['total_failure']
            else:
                stats['best_pattern'] = None

            return stats

    def save_chief_of_staff_analysis(self, analysis: Dict):
        """
        Save Chief of Staff analysis to history for trend tracking.

        Args:
            analysis: The complete analysis dictionary from ChiefOfStaff
        """
        import json

        with self._get_connection() as conn:
            cursor = conn.cursor()

            vip_insights = analysis.get('vip_insights', {})
            noise_analysis = analysis.get('noise_analysis', {})
            goal_alignment = analysis.get('goal_alignment', {})

            cursor.execute('''
                INSERT INTO chief_of_staff_history
                (analysis_date, period_days, total_emails, vip_count, signal_count,
                 noise_count, noise_percentage, email_debt_score, signal_percentage,
                 time_wasted_hours, analysis_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                analysis.get('period_days', 30),
                analysis.get('total_emails', 0),
                vip_insights.get('vip_count', 0),
                noise_analysis.get('signal_count', 0),
                noise_analysis.get('noise_count', 0),
                noise_analysis.get('noise_percentage', 0),
                goal_alignment.get('email_debt_score', 0),
                goal_alignment.get('inbox_composition_signal_pct', 0),
                noise_analysis.get('estimated_time_wasted_hours', 0),
                json.dumps(analysis)
            ))

    def get_chief_of_staff_trends(self, limit: int = 5) -> List[Dict]:
        """
        Get historical Chief of Staff analyses to show trends.

        Args:
            limit: Number of past analyses to retrieve

        Returns:
            List of historical analyses
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM chief_of_staff_history
                ORDER BY analysis_date DESC
                LIMIT ?
            ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]
