#!/bin/bash
# Gmail Unsubscriber - Easy launcher script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment and run with good defaults
cd "$SCRIPT_DIR"
source venv/bin/activate

# Default: suggest mode with 60 days lookback
# This finds subscriptions you never read over the last 2 months
python main.py --suggest --days 60
