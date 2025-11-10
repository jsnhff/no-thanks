# Email Notification Setup

Get a beautiful daily email with your unsubscribe suggestion and stats!

## Setup (5 minutes)

### 1. Enable Gmail App Password

You need an **App Password** (not your regular Gmail password):

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if you haven't already
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select **Mail** and **Mac** (or your device)
5. Click **Generate**
6. Copy the 16-character password

### 2. Create `.env` File

Copy the example and fill in your details:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
```

### 3. Install Flask

```bash
source venv/bin/activate
pip install flask
```

### 4. Test It

```bash
python send-daily-email.py
```

Check your email! You should receive a beautiful HTML email with:
- Today's suggestion (or "inbox clean!")
- Engagement score and metrics
- Your overall stats
- Clear instructions to unsubscribe

## What the Email Looks Like

**Subject:** 📧 Daily Unsubscribe Suggestion - November 10, 2024

**Body includes:**
- 🎯 Top candidate for unsubscription
- 📊 Engagement score (how often you read their emails)
- 📈 Total emails, unread count, unread percentage
- 📉 Your overall unsubscribe stats
- ✨ Beautiful gradient design
- 💻 Simple command to run

**No buttons to click!** Just a reminder email. When you're ready, run `unsubscribe` in your terminal.

## Automate It

Add to your daily cron/LaunchAgent to get the email automatically:

### Option 1: Update existing LaunchAgent

If you already set up the daily mode, edit your plist:

```bash
nano ~/Library/LaunchAgents/com.gmail-cleaner.daily.plist
```

Change the `ProgramArguments` to:

```xml
<array>
    <string>/Users/your-username/gmail-cleaner/venv/bin/python</string>
    <string>/Users/your-username/gmail-cleaner/send-daily-email.py</string>
</array>
```

Reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.gmail-cleaner.daily.plist
launchctl load ~/Library/LaunchAgents/com.gmail-cleaner.daily.plist
```

### Option 2: New Cron Job

```bash
crontab -e
```

Add:
```
0 9 * * * cd /Users/your-username/gmail-cleaner && source venv/bin/activate && python send-daily-email.py >> ~/gmail-cleaner-email.log 2>&1
```

## Benefits

- 📧 **Email reminder** - see it in your inbox each morning
- 📊 **Stats at a glance** - track your progress
- 🎨 **Beautiful HTML** - much nicer than terminal output
- 🚀 **No servers needed** - just sends you an email
- 🔄 **Set and forget** - cron job handles everything

## Troubleshooting

### "Failed to send email"

- Check your app password is correct (16 chars, no spaces)
- Make sure 2FA is enabled on your Google account
- Try generating a new app password

### "Authentication failed"

- Use an **App Password**, not your regular Gmail password
- Make sure `EMAIL_ADDRESS` matches the Gmail account

### No email received

- Check spam folder
- Verify `.env` file has correct email address
- Check logs: `~/gmail-cleaner-email.log`

## The Irony

Yes, we're sending you an email to help you unsubscribe from emails. 😄

But this one you actually want! It's helping you clean up your inbox.
