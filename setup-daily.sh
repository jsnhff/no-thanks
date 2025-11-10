#!/bin/bash
# Setup script for daily unsubscribe suggestions

echo "Gmail Unsubscriber - Daily Suggestion Setup"
echo "==========================================="
echo ""
echo "This will set up a daily notification at 9 AM showing you"
echo "one subscription suggestion based on your reading patterns."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create the daily runner script
cat > "$SCRIPT_DIR/daily-suggestion.sh" << 'EOFSCRIPT'
#!/bin/bash
# Daily suggestion runner

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source venv/bin/activate
python main.py --daily
EOFSCRIPT

chmod +x "$SCRIPT_DIR/daily-suggestion.sh"

echo "✓ Created daily-suggestion.sh"
echo ""
echo "Setup Options:"
echo ""
echo "Option 1: macOS LaunchAgent (Recommended for Mac)"
echo "  - Runs every day at 9 AM"
echo "  - Survives reboots"
echo "  - Shows in terminal"
echo ""
echo "Option 2: Cron Job (Works on Mac/Linux)"
echo "  - Classic Unix scheduling"
echo "  - Simpler but less reliable on Mac"
echo ""

read -p "Choose option (1 or 2): " option

if [ "$option" = "1" ]; then
    # LaunchAgent setup for macOS
    PLIST_PATH="$HOME/Library/LaunchAgents/com.gmail-cleaner.daily.plist"

    cat > "$PLIST_PATH" << EOFPLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gmail-cleaner.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_DIR/daily-suggestion.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$HOME/gmail-cleaner-daily.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/gmail-cleaner-daily-error.log</string>
</dict>
</plist>
EOFPLIST

    # Load the agent
    launchctl load "$PLIST_PATH" 2>/dev/null || launchctl unload "$PLIST_PATH" && launchctl load "$PLIST_PATH"

    echo ""
    echo "✓ LaunchAgent installed!"
    echo ""
    echo "Daily suggestions will run at 9 AM every day."
    echo "Logs: ~/gmail-cleaner-daily.log"
    echo ""
    echo "To test now: ./daily-suggestion.sh"
    echo "To disable: launchctl unload ~/Library/LaunchAgents/com.gmail-cleaner.daily.plist"

elif [ "$option" = "2" ]; then
    # Cron setup
    CRON_LINE="0 9 * * * $SCRIPT_DIR/daily-suggestion.sh >> $HOME/gmail-cleaner-daily.log 2>&1"

    # Check if already in crontab
    (crontab -l 2>/dev/null | grep -v "daily-suggestion.sh"; echo "$CRON_LINE") | crontab -

    echo ""
    echo "✓ Cron job installed!"
    echo ""
    echo "Daily suggestions will run at 9 AM every day."
    echo "Logs: ~/gmail-cleaner-daily.log"
    echo ""
    echo "To view crontab: crontab -l"
    echo "To test now: ./daily-suggestion.sh"
    echo "To disable: crontab -e (then remove the gmail-cleaner line)"
else
    echo ""
    echo "Invalid option. Run this script again to try again."
    exit 1
fi

echo ""
echo "Done! 🎉"
