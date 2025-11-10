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
