#!/usr/bin/env python3
"""
Send daily unsubscribe suggestion via email.
Requires .env file with email settings.
"""

import os
import sys
import secrets
import json
from pathlib import Path
from dotenv import load_dotenv

from src.gmail_client import GmailClient
from src.database import UnsubscribeDatabase
from src.email_notifier import EmailNotifier

# Load environment variables
load_dotenv()

def main():
    """Send daily suggestion email."""
    # Check for required environment variables
    email_address = os.getenv('EMAIL_ADDRESS')
    email_password = os.getenv('EMAIL_PASSWORD')

    if not email_address or not email_password:
        print("Error: EMAIL_ADDRESS and EMAIL_PASSWORD must be set in .env file")
        print("See .env.example for setup instructions")
        return 1

    # Initialize clients
    gmail = GmailClient()
    db = UnsubscribeDatabase()
    notifier = EmailNotifier()

    print("Authenticating with Gmail...")
    if not gmail.authenticate():
        print("Failed to authenticate")
        return 1

    print("Analyzing reading patterns...")
    gmail.analyze_reading_patterns(
        days_back=30,
        max_emails=200,
        update_db=True
    )

    print("Getting daily suggestion...")
    suggestion = db.get_daily_suggestion()
    stats = db.get_statistics()

    print(f"Sending email to {email_address}...")
    success = notifier.send_daily_suggestion(
        to_email=email_address,
        sender_email=email_address,
        sender_password=email_password,
        suggestion=suggestion,
        stats=stats
    )

    if success:
        print("✓ Email sent successfully!")
        if suggestion:
            print("\nNext steps:")
            print("1. Check your email for today's suggestion")
            print("2. If you want to unsubscribe, run: unsubscribe")
        else:
            print("\nNo suggestions today - inbox looking clean!")
        return 0
    else:
        print("✗ Failed to send email")
        return 1


if __name__ == '__main__':
    sys.exit(main())
