#!/bin/bash
# Gmail Unsubscriber - Easy launcher script with AI-powered suggestions

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
cd "$SCRIPT_DIR"
source venv/bin/activate

# If no arguments provided, use good defaults
if [ $# -eq 0 ]; then
    # Run suggest mode with 90 days lookback + AI hot takes!
    # Features:
    # - Brutally honest AI summaries of what each sender sends
    # - Smart learning from failed unsubscribe attempts
    # - Won't show the same sender repeatedly
    # To disable AI (faster), use: unsubscribe --suggest --days 90 --no-ai
    python main.py --suggest --days 90
else
    # Pass all arguments through to main.py
    # Examples:
    #   unsubscribe --days 30
    #   unsubscribe --max-emails 100
    #   unsubscribe --aggressive
    python main.py "$@"
fi
