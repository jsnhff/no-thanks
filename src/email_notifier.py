"""Email notification system for daily suggestions."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from datetime import datetime


class EmailNotifier:
    """Send email notifications for daily suggestions."""

    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_daily_suggestion(
        self,
        to_email: str,
        sender_email: str,
        sender_password: str,
        suggestion: Dict,
        stats: Dict,
        token: str = ""
    ) -> bool:
        """
        Send a daily suggestion email.

        Args:
            to_email: Recipient email address
            sender_email: Gmail address to send from
            sender_password: App-specific password (not regular Gmail password)
            suggestion: Daily suggestion data
            stats: Overall statistics

        Returns:
            True if email sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📧 Daily Unsubscribe Suggestion - {datetime.now().strftime('%B %d, %Y')}"
            msg['From'] = sender_email
            msg['To'] = to_email

            # Create HTML content
            html_content = self._create_html_email(suggestion, stats, token)

            # Attach HTML
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def _create_html_email(self, suggestion: Optional[Dict], stats: Dict, token: str = "") -> str:
        """Create HTML email content."""

        if not suggestion:
            # No suggestion today
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    h1 {{ color: #00c9a7; margin-top: 0; }}
                    .stats {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                    .stat-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e9ecef; }}
                    .stat-item:last-child {{ border-bottom: none; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎉 Inbox Clean!</h1>
                    <p>Great news! No new subscription suggestions for today. Your inbox is looking good.</p>

                    <div class="stats">
                        <h3>Your Stats</h3>
                        <div class="stat-item">
                            <span>Total Subscriptions Tracked:</span>
                            <strong>{stats.get('total_subscriptions', 0)}</strong>
                        </div>
                        <div class="stat-item">
                            <span>Successfully Unsubscribed:</span>
                            <strong style="color: #00c9a7;">{stats.get('unsubscribed_count', 0)}</strong>
                        </div>
                        <div class="stat-item">
                            <span>Effective Unsubscribes:</span>
                            <strong style="color: #00c9a7;">{stats.get('effective_unsubscribes', 0)}</strong>
                        </div>
                        <div class="stat-item">
                            <span>Still Receiving After Unsub:</span>
                            <strong style="color: #dc3545;">{stats.get('failed_unsubscribes', 0)}</strong>
                        </div>
                    </div>

                    <div class="footer">
                        <p>Gmail Unsubscriber - Daily Report<br>
                        This is an automated email from your local Gmail Unsubscriber app.</p>
                    </div>
                </div>
            </body>
            </html>
            """

        # Has a suggestion
        sender = suggestion['sender_address']
        total = suggestion['total_received']
        unread = suggestion['total_unread']
        engagement = suggestion['engagement_score']

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #667eea; margin-top: 0; }}
                .suggestion-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 8px; margin: 20px 0; }}
                .suggestion-box h2 {{ margin: 0 0 15px 0; font-size: 18px; }}
                .sender {{ font-size: 24px; font-weight: bold; margin: 10px 0; word-break: break-all; }}
                .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 20px; }}
                .metric {{ text-align: center; background: rgba(255,255,255,0.2); padding: 15px; border-radius: 6px; }}
                .metric-value {{ font-size: 32px; font-weight: bold; display: block; }}
                .metric-label {{ font-size: 12px; opacity: 0.9; margin-top: 5px; }}
                .engagement {{ font-size: 48px; font-weight: bold; text-align: center; margin: 20px 0; }}
                .engagement-label {{ font-size: 16px; text-align: center; opacity: 0.9; }}
                .cta {{ background: #10b981; color: white; padding: 15px 30px; text-decoration: none; display: inline-block; border-radius: 6px; margin: 20px 0; font-weight: bold; }}
                .stats {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                .stat-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e9ecef; }}
                .stat-item:last-child {{ border-bottom: none; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 14px; }}
                .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; background: #ffc107; color: #000; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📧 Daily Unsubscribe Suggestion</h1>
                <p>Based on your reading patterns, here's today's recommendation:</p>

                <div class="suggestion-box">
                    <h2>🎯 Top Candidate</h2>
                    <div class="sender">{sender}</div>

                    <div class="engagement">
                        <div class="engagement-label">Engagement Score</div>
                        <span style="font-size: 64px;">{engagement:.0f}%</span>
                        <div class="engagement-label">You read {engagement:.0f}% of their emails</div>
                    </div>

                    <div class="metrics">
                        <div class="metric">
                            <span class="metric-value">{total}</span>
                            <span class="metric-label">Total Emails</span>
                        </div>
                        <div class="metric">
                            <span class="metric-value">{unread}</span>
                            <span class="metric-label">Unread</span>
                        </div>
                        <div class="metric">
                            <span class="metric-value">{(unread/total*100):.0f}%</span>
                            <span class="metric-label">Unread Rate</span>
                        </div>
                    </div>
                </div>

                <div style="text-align: center; margin: 30px 0; background: #f8f9fa; padding: 25px; border-radius: 8px;">
                    <p style="font-size: 18px; color: #495057; margin-bottom: 15px;">Ready to unsubscribe?</p>
                    <p style="color: #6c757d; margin-bottom: 10px;">Simply run this in your terminal:</p>
                    <div style="background: #2d3748; color: #e2e8f0; padding: 15px 25px; border-radius: 6px;
                                font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; font-size: 16px;
                                display: inline-block; margin: 10px 0;">
                        unsubscribe
                    </div>
                    <p style="color: #6c757d; font-size: 14px; margin-top: 15px;">
                        Or run: <code style="background: #e9ecef; padding: 4px 8px; border-radius: 4px;">python main.py --daily</code>
                    </p>
                </div>

                <div class="stats">
                    <h3>Your Overall Stats</h3>
                    <div class="stat-item">
                        <span>Total Subscriptions Tracked:</span>
                        <strong>{stats.get('total_subscriptions', 0)}</strong>
                    </div>
                    <div class="stat-item">
                        <span>Successfully Unsubscribed:</span>
                        <strong style="color: #00c9a7;">{stats.get('unsubscribed_count', 0)}</strong>
                    </div>
                    <div class="stat-item">
                        <span>Effective Unsubscribes:</span>
                        <strong style="color: #00c9a7;">{stats.get('effective_unsubscribes', 0)}</strong>
                    </div>
                    <div class="stat-item">
                        <span>Total Attempts:</span>
                        <strong>{stats.get('total_attempts', 0)}</strong>
                    </div>
                </div>

                <div class="footer">
                    <p>Gmail Unsubscriber - Daily Report<br>
                    This is an automated email from your local Gmail Unsubscriber app.<br>
                    <small>Yes, the irony of sending an email to help you unsubscribe from emails is not lost on us. 😄</small></p>
                </div>
            </div>
        </body>
        </html>
        """
