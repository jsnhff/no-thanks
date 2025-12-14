# LinkedIn Post Prompt for ChatGPT

Write a LinkedIn post announcing the public release of my new open-source project: **No Thanks**

## Project Details

**Name:** No Thanks
**Tagline:** What you actually say to people trying to sell you crap—now automated.
**Repository:** https://github.com/jsnhff/no-thanks
**License:** Non-Commercial Open Source (free to use, remix, share - but not sell)
**Tech Stack:** Python, Gmail API, Playwright browser automation, OpenAI GPT-4o-mini

## Key Features to Highlight

1. **AI-Powered "Hot Takes"** - Uses GPT-4o-mini to generate brutally honest one-sentence summaries of what each sender actually sends you. Examples:
   - "Daily promotional emails for furniture you'll never buy, clogging your inbox with 'deals'" (IKEA Family)
   - "Weekly career advice emails you never open, pretending to help you 'level up' while gathering data" (LinkedIn Job Alerts)
   - "Motivational quotes and productivity tips you scroll past, ironically wasting the time they claim to save" (Medium Daily Digest)

2. **Smart Reading Pattern Analysis** - Analyzes your last 90 days of emails to identify subscriptions you never actually read

3. **Interactive "Keep or Cut" Interface** - Fun, swipe-style CLI with emojis (💚 keep | 🔪 cut)

4. **Automated Browser Agent** - Playwright automation that clicks unsubscribe buttons for you

5. **Auto-Archive** - Automatically archives emails after unsubscribing to clean up your inbox

6. **Privacy-First** - Runs entirely locally on your machine, no data leaves your computer (except Gmail API auth and optional OpenAI API for hot takes)

7. **Effectiveness Tracking** - SQLite database monitors whether senders actually stop emailing you after unsubscribing

## Development Timeline

- Started building this a few weeks ago out of personal frustration with inbox clutter
- Spent evenings and weekends iterating on features
- Just pushed v1.0 public release today (November 17, 2025)
- Built with significant collaboration from Claude Code (Anthropic's AI coding assistant)

## The AI + Human Collaboration Story

This project is a perfect example of human-AI collaboration:
- **I brought:** The vision, UX decisions, problem understanding, and real-world pain points
- **Claude Code brought:** Rapid prototyping, code architecture, debugging, security auditing, and documentation polish
- **Together:** We built something in weeks that would have taken months solo

We pair-programmed through:
- Gmail API integration and OAuth flows
- Playwright browser automation (handling complex unsubscribe flows)
- Reading pattern analysis algorithms
- AI hot takes integration
- CLI interface design
- Security hardening for public release

The back-and-forth was natural - I'd describe what I wanted, Claude would implement it, I'd test and give feedback, and we'd iterate. It felt less like "coding" and more like "building together."

## Why This Matters

**The Problem:**
- Average person receives 100+ emails per day
- 60% of those are promotional/automated
- Unsubscribing is tedious: find link, click through multi-step forms, confirm, repeat
- Many people just let subscriptions pile up, creating inbox anxiety

**The Solution:**
- Automates the tedious parts
- Uses AI to help you see WHAT you're actually subscribed to (eye-opening!)
- Makes decisions quick and fun (swipe-style interface)
- Actually works - browser automation handles complex unsubscribe flows
- Tracks effectiveness so you know if senders honor your requests

## Why I'm Sharing It

1. **It solved a real problem for me** - My inbox went from 1,000+ unread to manageable
2. **Others are drowning too** - Inbox overwhelm is universal
3. **Open source community** - Want others to benefit and improve it
4. **Educational value** - Shows practical AI integration, browser automation, and CLI design

## The License (Non-Commercial)

Released under a non-commercial open source license:
- ✅ Free for personal, educational use
- ✅ Modify, remix, and share
- ❌ Can't sell it or use commercially
- ❌ Can't turn it into a paid SaaS

Why? I want this to help people, not become another product that monetizes your email data.

## Call to Action

**Try it out:** https://github.com/jsnhff/gmail-ai-unsubscriber

**Contribute:**
- Found a bug? Open an issue
- Have ideas? Submit a PR
- Love it? Star the repo ⭐

**Share:**
If you know someone drowning in email, send them the link. Let's help people take back their inboxes!

---

## Tone & Style Guidelines for the LinkedIn Post

- Professional but conversational
- Excited/enthusiastic about the launch
- Highlight the AI collaboration aspect (it's timely and interesting)
- Include some personality (the hot takes examples are funny)
- Not too long - people scroll fast on LinkedIn
- Include a clear CTA to try it or contribute
- Use emojis sparingly but effectively
- Make it shareable - people should want to repost

## Post Structure Suggestion

1. Hook (grab attention - maybe start with a relatable inbox stat or pain point)
2. The problem (inbox overwhelm)
3. The solution (my project - quick feature highlights)
4. The AI collaboration story (what made this special)
5. Results/impact (what it did for me)
6. The license philosophy (why non-commercial)
7. Call to action (try it, contribute, share)

Keep it punchy. Maybe 200-300 words max. LinkedIn readers skim.

## Optional Elements to Consider

- A question to drive engagement ("What's your inbox count right now? 👀")
- A stat about email overload
- Mention it took weeks not months thanks to AI pair programming
- The irony of LinkedIn sending emails you might want to unsubscribe from 😄

---

Now write me a great LinkedIn post! Make it engaging, shareable, and true to my voice as a builder who's excited about AI collaboration and open source.
