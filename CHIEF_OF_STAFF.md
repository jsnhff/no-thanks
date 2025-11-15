# Chief of Staff - Goal-Aligned Inbox Intelligence

Your personal Chief of Staff that helps you achieve your Q4 2025 goals by analyzing your inbox patterns and providing actionable insights.

## What It Does

The Chief of Staff analyzes your inbox and tells you:
- **Who really matters** (VIP Relationship Tracker)
- **What's noise** (Signal vs Noise Analysis)
- **How your inbox aligns with your goals** (Goal Alignment Check)

## Your Goals (from user_profile.json)

The Chief of Staff analyzes your inbox based on **your specific goals** defined in `user_profile.json`. 

Example goals might include:
1. Professional leadership and visibility
2. Side project launches and promotion
3. Learning new skills
4. Creative output and sharing
5. Deepening friendships and community connections
6. Being present for family
7. Maintaining work-life balance

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
Add to your `~/.zshrc` or `~/.bashrc`:
```bash
alias cos='/path/to/your/gmail-cleaner/chief-of-staff.sh'
```

Then just run:
```bash
cos
```

## What You'll See

### 👥 VIP Relationship Tracker
Identifies your most important people based on:
- **Leadership Tier**: Professional peers and leadership
- **Creative Tier**: Collaborators on your projects
- **Personal Tier**: Friends, family, and community

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

**Goal: Professional leadership and visibility**
- Tracks professional leadership emails
- Flags if you're falling behind on responses

**Goal: Deepen community connections**
- Identifies personal emails from your community
- Shows connection patterns

**Goal: Be present for family**
- Measures noise stealing family time
- Calculates hours you could reclaim

**Goal: Launch side projects**
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

✅ Professional leadership
   3 unread emails from professional leadership peers
   → Review work communications

⚠️  Deepen friendships and community connections
   8 unread personal emails, 4 connections haven't emailed in 2+ weeks
   → Reach out to friends you haven't heard from

✨ CHIEF OF STAFF RECOMMENDATION

Your inbox is 34% signal. You have 12 VIP emails waiting.
Top Priority: Review work communications
```

## Why This Matters

Most inbox tools treat all emails equally. Chief of Staff understands **your specific goals** and helps you:

✅ Never miss important professional leadership emails
✅ Stay connected with friends and collaborators
✅ Reclaim time for family by cutting noise
✅ Spot side project opportunities
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
