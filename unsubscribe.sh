#!/bin/bash
# Gmail Unsubscriber - Easy launcher script with AI-powered suggestions

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
cd "$SCRIPT_DIR"
source venv/bin/activate

# If no arguments provided, use good defaults
if [ $# -eq 0 ]; then
    # Run suggest mode with 90 days lookback
    # Features:
    # - AI summaries of what each sender actually sends
    # - Smart learning from failed unsubscribe attempts
    # - Won't show the same sender repeatedly
    python main.py --suggest --days 90
else
    # Pass all arguments through to main.py
    # Examples:
    #   unsubscribe --days 30
    #   unsubscribe --max-emails 100
    #   unsubscribe --aggressive
    python main.py "$@"
fi
