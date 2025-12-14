```
 _   _         _____ _                 _
| \ | |       |_   _| |               | |
|  \| | ___     | | | |__   __ _ _ __ | | _____
| . ` |/ _ \    | | | '_ \ / _` | '_ \| |/ / __|
| |\  | (_) |   | | | | | | (_| | | | |   <\__ \
\_| \_/\___/    \_/ |_| |_|\__,_|_| |_|_|\_\___/
```

# No Thanks™

**Take back your inbox. One unsubscribe at a time.**

What you actually say to people trying to sell you crap—now automated.

A local Python tool that uses AI to identify email subscriptions you never read, gives you brutally honest summaries of what they send, and automates the tedious clicking to unsubscribe. Runs on your machine, not in someone else's cloud.

### 🔥 AI Hot Takes - See What You're Actually Subscribed To

The app uses AI to generate brutally honest summaries of what each sender actually sends you:

> _"Daily promotional emails for furniture you'll never buy, clogging your inbox with 'deals'"_
> — IKEA Family

> _"Weekly career advice emails you never open, pretending to help you 'level up' while gathering data"_
> — LinkedIn Job Alerts

> _"Motivational quotes and productivity tips you scroll past, ironically wasting the time they claim to save"_
> — Medium Daily Digest

> _"Another SaaS company's changelog that you didn't ask for, updating features you don't use"_
> — Random B2B Tool

> _"Restaurant deals for places you've ordered from once, three years ago, still desperately trying to win you back"_
> — Grubhub

## Features

- 🤖 **AI-Powered Hot Takes** - Get brutally honest summaries of what each sender actually sends you
- 📧 **Smart Inbox Scanning** - Finds all emails with unsubscribe links across your entire Gmail
- 🎯 **Reading Pattern Analysis** - Identifies subscriptions you never read
- ✂️ **Interactive CLI** - Swipe-style "Keep 📥 or Cut 🔪" interface for reviewing subscriptions
- 🤖 **Automated Unsubscribe Agent** - Playwright browser automation handles the clicking for you
- 🗄️ **Auto-Archive** - Automatically archives emails after unsubscribing to clean up your inbox
- 📊 **Effectiveness Tracking** - SQLite database monitors if senders actually stop emailing you
- 🔐 **Privacy-Focused** - Runs entirely locally on your machine, no data leaves your computer
- 🔑 **Secure OAuth** - Google authentication, no API keys needed

## Prerequisites

- Python 3.10 or higher (3.12 recommended)
- A Google Cloud Project with Gmail API enabled
- Gmail OAuth credentials (see setup instructions below)
- (Optional) OpenAI API key for AI-powered hot takes

## Quick Start

The easiest way to get started:

```bash
# 1. Clone and enter the directory
git clone https://github.com/jsnhff/no-thanks.git
cd no-thanks

# 2. Run the setup script (does everything for you!)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 3. Run it!
python main.py --suggest
```

That's it! The app will open a browser window for you to sign in to Gmail on first run.

## Detailed Installation

### 1. Clone the repository

```bash
git clone https://github.com/jsnhff/no-thanks.git
cd no-thanks
```

### 2. Create a virtual environment

**Important:** Make sure you have Python 3.10 or higher installed!

```bash
python3 --version  # Check your version
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browsers

```bash
playwright install chromium
```

### 5. (Optional) Set up OpenAI API for AI Hot Takes

If you want AI-powered brutally honest hot takes about what each sender actually sends:

1. Get an API key at [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
3. Add your key:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

This is **optional** - the app works fine without it, you just won't see the AI hot takes in the table. Uses GPT-4o-mini (fast & cheap!).

**Want personalized recommendations?** Create a `user_profile.json` file:

```bash
cp user_profile.example.json user_profile.json
```

Edit it with your interests, goals, and inbox preferences. The AI will use this to give you personalized hot takes like:
- "Design leadership insights - matches your role perfectly"
- "E-commerce deals - not relevant to your work"
- "AI/tech newsletters - aligns with your interests"

Without a profile, it gives generic assessments. With a profile, it's tailored to YOU.

### 6. Set up Gmail API credentials

#### a. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Give it a name like "No Thanks"

#### b. Enable Gmail API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click on it and press **Enable**

#### c. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External**
   - App name: "No Thanks"
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: You can skip this for now
   - Test users: Add your Gmail address
4. Back at Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: "No Thanks"
5. Click **Create**
6. Download the credentials JSON file
7. **Rename it to `credentials.json`** and place it in the project root directory

```
no-thanks/
├── credentials.json  ← Place your downloaded OAuth credentials here
├── main.py
├── requirements.txt
└── ...
```

## Usage

### Quick Start (Recommended)

The easiest way to use the app is with the built-in alias:

```bash
unsubscribe
```

This runs the smart suggestion mode with good defaults (90 days lookback, headless browser).

**First time setup:** Reload your shell config or open a new terminal:
```bash
source ~/.zshrc
```

### Basic Usage

Run the application:

```bash
python main.py
```

The first time you run it:
1. A browser window will open asking you to sign in to Google
2. Select your Gmail account
3. Grant the requested permissions (read-only access to Gmail)
4. The application will save your token locally for future use

### Workflow

1. **Scan**: The app scans your Gmail for emails with unsubscribe links
2. **Review**: You'll see a table of emails with unsubscribe options
3. **Approve**: Select which ones to unsubscribe from (by number, range, or 'all')
4. **Confirm**: Review your selection and confirm
5. **Watch**: The browser will open and automatically navigate to unsubscribe links
6. **Track**: Results are saved to the local database

### Command Line Options

```bash
# Run in headless mode (no visible browser window)
python main.py --headless

# Scan more emails per batch (default: 50)
python main.py --max-emails 100

# Smart suggestion mode - analyzes reading patterns (RECOMMENDED)
python main.py --suggest

# Analyze emails from the last 60 days (default: 90)
python main.py --suggest --days 60

# Daily mode - one suggestion per day (perfect for cron jobs!)
python main.py --daily

# Check effectiveness of previous unsubscribes
python main.py --check-effectiveness
```

### Smart Suggestion Mode (Recommended!)

The `--suggest` flag analyzes your email reading patterns to identify subscriptions you never read:

```bash
python main.py --suggest
```

This will:
- Analyze **all emails** (not just Promotions) from the last 90 days (configurable with `--days`)
- Search across Primary, Social, Updates, Forums, and any custom labels
- **Learn from your reading habits** - updates the database with what you actually read
- Calculate a **smart relevance score** based on:
  - **Staleness**: How long since you last read an email from them (40% weight)
  - **Unread percentage**: What % of their emails you never open (40% weight)
  - **Volume**: How many unread emails are piling up (20% weight)
- Rank by least relevant/most stale first
- Display a table showing:
  - Sender name
  - **AI-powered summary**: One-sentence description of what they send (optional, requires Anthropic API key)
  - Total emails received
  - Number of unread emails
  - Percentage unread
  - **Last read**: When you last opened their email ("Never", "3d ago", "2mo ago", etc.)
- Allow you to select which to unsubscribe from:
  - Enter numbers: `1,3,5`
  - Enter range: `1-10`
  - Enter `top 5` to select the 5 worst offenders
  - Enter `all` to select all
- **Runs in headless mode by default** (invisible browser, faster)

**Learning frequency:** Every time you run `unsubscribe` (or `--suggest`), the app refreshes its understanding of your reading patterns. This means suggestions stay current based on your latest behavior!

**Example:**
```bash
# Analyze last 60 days and find subscriptions you never read
python main.py --suggest --days 60
```

### Daily Suggestion Mode (Set & Forget!)

The `--daily` flag shows you **one subscription suggestion per day** based on your reading patterns:

```bash
python main.py --daily
```

This is perfect for:
- **Daily cron jobs** - get a quick notification each morning
- **Gradual cleanup** - unsubscribe from one thing per day without overwhelm
- **Learning mode** - the app learns from what you DO read to improve suggestions

**How it works:**
1. Analyzes your last 30 days of emails
2. Updates its understanding of your reading habits
3. Shows the #1 worst offender (lowest engagement score)
4. Quick yes/no decision
5. Unsubscribes automatically in headless mode

**Auto-run it daily:**
```bash
./setup-daily.sh
```

This interactive script will:
- Set up a macOS LaunchAgent (recommended) or cron job
- Run daily at 9 AM automatically
- Log results to `~/gmail-cleaner-daily.log`

**Want email notifications instead?**

Get a beautiful daily email with your suggestion and stats:

```bash
python send-daily-email.py
```

Setup guide: [EMAIL_SETUP.md](EMAIL_SETUP.md)

The email includes:
- 📧 Today's suggestion with engagement metrics
- 📊 Beautiful stats dashboard
- 🎨 HTML design (no ugly terminal output!)
- 💬 Simple command to run when ready
- 😄 Yes, the irony is intentional!

### Check Unsubscribe Effectiveness

To check if unsubscribes are actually working:

```bash
python main.py --check-effectiveness
```

This will:
- Scan your recent emails
- Check if you're still receiving emails from senders you unsubscribed from
- Display an effectiveness report

## How It Works

### 1. Email Scanning
The Gmail API client searches for:
- **All emails across all categories** (Primary, Social, Updates, Forums, Promotions, etc.)
- Emails containing "unsubscribe" in the body or subject
- Emails with `List-Unsubscribe` headers
- Excludes: sent emails, drafts, and trash

### 2. Link Extraction
For each email, it extracts unsubscribe links from:
- `List-Unsubscribe` email header (most reliable)
- HTML body links containing "unsubscribe", "opt-out", or "preferences"

### 3. Browser Automation
The Playwright agent:
- Opens each unsubscribe link in a browser
- Looks for unsubscribe buttons using multiple selectors
- Clicks the button and any confirmation buttons
- Checks for success messages
- Records the result

### 4. Effectiveness Tracking & Learning
The database tracks:
- Each subscription source (sender email address)
- When you unsubscribed
- How many emails were received before/after unsubscribing
- Whether unsubscribes are effective
- **Your reading patterns**: Which senders you engage with vs ignore
- **Engagement scores**: Calculated from read/unread ratios
- **Failure reasons**: Detailed logs of why unsubscribes fail (for learning)

**The app learns from your behavior:**
- Tracks which emails you actually read
- Calculates engagement scores for each sender
- Uses this to improve future suggestions
- Avoids suggesting senders you actively engage with

## Database Schema

The SQLite database (`unsubscribe_history.db`) contains:

### `subscriptions`
- Tracks each email sender
- Unsubscribe status and dates
- Email counts before and after unsubscribing

### `unsubscribe_attempts`
- Individual unsubscribe attempts
- Success/failure status
- Links used and error messages

### `post_unsubscribe_emails`
- Emails received after unsubscribing
- Used to measure effectiveness

### `reading_patterns` (NEW!)
- Tracks your engagement with each sender
- Stores read/unread counts and engagement scores
- Updated automatically when using `--daily` or `--suggest` modes
- Used to improve suggestions over time

## Privacy & Security

- **Runs locally**: All processing happens on your machine
- **Read-only Gmail access**: The app can only read emails, not send or delete
- **OAuth tokens**: Stored locally in `token.json`
- **No data sharing**: Nothing is sent to external servers except Google's Gmail API

## Troubleshooting

### "credentials.json not found"
Make sure you've downloaded OAuth credentials from Google Cloud Console and placed them in the project root as `credentials.json`.

### "Access blocked: This app's request is invalid"
1. Make sure you've enabled the Gmail API in Google Cloud Console
2. Check that you've added your email as a test user in the OAuth consent screen

### Browser automation fails
Some unsubscribe pages may be too complex or require CAPTCHA. The app will mark these as failed and you can manually unsubscribe later.

### Unsubscribes not effective
Some senders don't honor unsubscribe requests immediately or at all. Use the effectiveness report to identify these and consider:
- Creating a Gmail filter to auto-delete
- Reporting as spam
- Manually blocking the sender

## Contributing

Contributions are welcome! Whether it's:

- 🐛 Bug reports
- 💡 Feature suggestions
- 📝 Documentation improvements
- 🔧 Code contributions

Feel free to:
1. Open an issue to discuss your idea
2. Fork the repo and create a pull request
3. Share feedback on what works or doesn't work for you

## Support

If you find this tool helpful:
- ⭐ Star this repo on GitHub
- 🐦 Share it with friends who are drowning in email
- 🐛 Report bugs or suggest features via GitHub Issues

## License

**Non-Commercial Open Source License**

TL;DR: **Use it, remix it, share it - but don't sell it!** 🚫💰

This project is free for:
- ✅ Personal use
- ✅ Educational use
- ✅ Modification and remixing
- ✅ Sharing with others

But you **cannot**:
- ❌ Sell this software or derivatives
- ❌ Use it in commercial products
- ❌ Charge money for access to it
- ❌ Offer it as a paid SaaS/hosted service

See [LICENSE](LICENSE) for full legal details.

## Disclaimer

This tool is for personal use. Always review what you're unsubscribing from before confirming. The effectiveness of unsubscribes depends on the sender honoring your request.

**Privacy Note:** This app runs entirely on your local machine. Your Gmail credentials never leave your computer, and no data is sent to any third-party servers (except Google's Gmail API for authentication and OpenAI's API if you enable AI hot takes).
