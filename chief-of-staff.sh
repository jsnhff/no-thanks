#!/bin/bash
# Chief of Staff - Goal-aligned inbox intelligence report

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment and run Chief of Staff mode
cd "$SCRIPT_DIR"
source venv/bin/activate

# Run Chief of Staff mode analyzing last 30 days
# Features:
# - VIP Relationship Tracker (identify your most important people)
# - Signal vs Noise Analysis (quantify the clutter)
# - Goal Alignment Check (Q4 2025 goals progress)
# - Actionable recommendations aligned with your values
python main.py --chief-of-staff --days 30
