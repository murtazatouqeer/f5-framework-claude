#!/bin/bash
# F5 Husky — Post-Edit Change Tracker
# Log mỗi file edit để giúp review sau

FILE_PATH="${TOOL_INPUT_FILE_PATH:-}"

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Log edit
LOG_DIR=".claude/review-history/edits"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] $FILE_PATH" >> "$LOG_DIR/$(date +%Y-%m-%d).log"

exit 0
