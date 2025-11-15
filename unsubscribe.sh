#!/bin/bash
# Gmail Unsubscriber - Easy launcher script with AI-powered suggestions

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
cd "$SCRIPT_DIR"
source venv/bin/activate

# If no arguments provided, use good defaults
if [ $# -eq 0 ]; then
    # Run suggest mode with 90 days lookback (fast mode, no AI)
    # Features:
    # - Smart learning from failed unsubscribe attempts
    # - Won't show the same sender repeatedly
    # - Lightning fast (no AI API calls)
    # To enable AI summaries, use: unsubscribe --suggest --days 90
    python main.py --suggest --days 90 --no-ai
else
    # Pass all arguments through to main.py
    # Examples:
    #   unsubscribe --days 30
    #   unsubscribe --max-emails 100
    #   unsubscribe --aggressive
    python main.py "$@"
fi
