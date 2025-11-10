# Gmail Unsubscriber

A local Python application that helps you automatically unsubscribe from unwanted emails in Gmail with your approval. Uses Playwright to intelligently navigate unsubscribe links and tracks effectiveness over time.

## Features

- **Scans Gmail** for emails with unsubscribe links
- **Interactive CLI** for reviewing and approving unsubscribe actions
- **Automated browser agent** (Playwright) that navigates to unsubscribe links and completes the process
- **SQLite database** to track:
  - All subscriptions and unsubscribe attempts
  - Effectiveness monitoring (checks if emails still arrive after unsubscribing)
  - Statistics on successful vs failed unsubscribes
- **Privacy-focused**: Runs entirely locally on your machine
- **OAuth authentication**: Secure Google authentication (no API keys)

## Prerequisites

- Python 3.8 or higher
- A Google Cloud Project with Gmail API enabled
- Gmail OAuth credentials (see setup instructions below)

## Installation

### 1. Clone the repository

```bash
cd gmail-cleaner
```

### 2. Create a virtual environment

```bash
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

### 5. (Optional) Set up Anthropic API for AI Summaries

If you want AI-powered one-sentence summaries of what each sender's emails are about:

1. Get an API key at [Anthropic Console](https://console.anthropic.com/)
2. Create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
3. Add your key:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

This is **optional** - the app works fine without it, you just won't see the AI summaries in the table.

### 6. Set up Gmail API credentials

#### a. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Give it a name like "Gmail Unsubscriber"

#### b. Enable Gmail API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click on it and press **Enable**

#### c. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External**
   - App name: "Gmail Unsubscriber"
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: You can skip this for now
   - Test users: Add your Gmail address
4. Back at Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: "Gmail Unsubscriber"
5. Click **Create**
6. Download the credentials JSON file
7. **Rename it to `credentials.json`** and place it in the project root directory

```
gmail-cleaner/
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

This runs the smart suggestion mode with good defaults (60 days lookback, headless browser).

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

Feel free to submit issues or pull requests to improve the tool!

## License

MIT License - Feel free to use and modify as needed.

## Disclaimer

This tool is for personal use. Always review what you're unsubscribing from before confirming. The effectiveness of unsubscribes depends on the sender honoring your request
