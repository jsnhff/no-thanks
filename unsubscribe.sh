#!/bin/bash
# Gmail Unsubscriber - Easy launcher script with AI-powered suggestions

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment and run with good defaults
cd "$SCRIPT_DIR"
source venv/bin/activate

# Run suggest mode with 90 days lookback
# Features:
# - 3-sentence AI summaries of actual email content
# - Smart learning from failed unsubscribe attempts
# - Won't show the same sender repeatedly
# - Tinder-style Keep or Cut workflow 🔪
python main.py --suggest --days 90
