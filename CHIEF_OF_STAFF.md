# Chief of Staff - Goal-Aligned Inbox Intelligence

Your personal Chief of Staff that helps you achieve your Q4 2025 goals by analyzing your inbox patterns and providing actionable insights.

## What It Does

The Chief of Staff analyzes your inbox and tells you:
- **Who really matters** (VIP Relationship Tracker)
- **What's noise** (Signal vs Noise Analysis)
- **How your inbox aligns with your goals** (Goal Alignment Check)

## Your Q4 2025 Goals (from user_profile.json)

1. Lead more visibly and assertively at Shopify ('from the front')
2. Launch and promote Regender.xyz
3. Advance Spanish fluency
4. Create and share 1–2 new artworks per year
5. Deepen friendships and community connections in Los Angeles
6. Be present and engaged as a husband and dad
7. Maintain financial clarity and personal balance

## How To Use

### Quick Start
```bash
./chief-of-staff.sh
```

This analyzes the last 30 days and gives you a comprehensive report.

### Custom Time Period
```bash
python main.py --chief-of-staff --days 60  # Analyze last 60 days
python main.py --chief-of-staff --days 7   # Just the last week
```

### Add an Alias
Add to your `~/.zshrc`:
```bash
alias cos='/Users/jasonhuff/gmail-cleaner/chief-of-staff.sh'
```

Then just run:
```bash
cos
```

## What You'll See

### 👥 VIP Relationship Tracker
Identifies your most important people based on:
- **Leadership Tier**: Shopify peers and leadership
- **Creative Tier**: Collaborators on projects like Regender.xyz
- **Personal Tier**: Friends, family, LA community

Shows you:
- Who you respond to fastest
- Who you might be neglecting
- Unread emails from VIPs

### 🧹 Signal vs Noise Analysis
Quantifies the clutter:
- % of inbox that's marketing noise vs real humans
- Time wasted processing spam
- Worst noise offenders
- Potential time savings if you cut the noise

### 🎯 Goal Alignment Check
Shows how your inbox helps/hurts each goal:

**Goal: Lead more visibly at Shopify**
- Tracks Shopify leadership emails
- Flags if you're falling behind on responses

**Goal: Deepen LA friendships**
- Identifies personal emails from LA community
- Shows connection patterns

**Goal: Be present as husband and dad**
- Measures noise stealing family time
- Calculates hours you could reclaim

**Goal: Launch Regender.xyz**
- Flags creative collaborator emails
- Identifies project opportunities

## Example Output

```
┌──────────────────────────────────────────────┐
│ Chief of Staff Inbox Report                 │
│ Last 30 days | 847 emails                   │
└──────────────────────────────────────────────┘

👥 VIP RELATIONSHIP TRACKER

Person                   Tier        Emails  Unread  Status
Sarah Chen              Leadership    12      3      ⚠️  3 emails need attention
David Park              Creative      8       0      ✓ Engaged
Emma Rodriguez          Personal      5       2      ⚠️  2 emails need attention

🧹 SIGNAL vs NOISE ANALYSIS

📊 Inbox Composition: 287 signal | 560 noise (66%)
⏱️  Estimated Time Wasted: 4.7 hours this period
💡 Potential Monthly Savings: 4.7 hours/month

🎯 GOAL ALIGNMENT CHECK

📬 Email Debt Score: 12 VIP emails unread
✉️  VIPs Needing Response: 5
📈 Signal Quality: 34% high-value

✅ Lead more visibly at Shopify
   3 unread emails from Shopify leadership peers
   → Review Shopify communications

⚠️  Deepen friendships and community connections
   8 unread personal emails, 4 connections haven't emailed in 2+ weeks
   → Reach out to friends you haven't heard from

✨ CHIEF OF STAFF RECOMMENDATION

Your inbox is 34% signal. You have 12 VIP emails waiting.
Top Priority: Review Shopify communications
```

## Why This Matters

Most inbox tools treat all emails equally. Chief of Staff understands **your specific goals** and helps you:

✅ Never miss important Shopify leadership emails
✅ Stay connected with LA friends and collaborators
✅ Reclaim time for family by cutting noise
✅ Spot Regender.xyz opportunities
✅ Maintain the balance you need to lead effectively

## Integration with Unsubscribe Feature

Use Chief of Staff to **identify** the noise, then use the regular unsubscribe feature to **eliminate** it:

```bash
# 1. See what's noise
./chief-of-staff.sh

# 2. Cut the noise
./unsubscribe.sh
```

## Technical Details

Chief of Staff uses:
- Gmail API to fetch email metadata (no content read)
- Your `user_profile.json` to understand your goals and values
- Pattern analysis to classify relationships (VIP, creative, personal, noise)
- Engagement metrics (read rates, response times, staleness)

**Privacy**: All analysis happens locally. Nothing is sent anywhere except the Gmail API requests.

## First Run Note

The first time you run Chief of Staff with expanded Gmail API scopes, you'll need to re-authenticate. This is normal - it's requesting permission to read labels and filters.

Just follow the OAuth flow in your browser and you're set!
