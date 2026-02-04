#!/bin/bash
# F5 Framework Post-Edit Hook
# Tracks changes and validates quality requirements after edits

# Get the file being edited from environment
FILE_PATH="${TOOL_INPUT_FILE_PATH:-}"

# Skip if no file path
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Get file extension
EXT="${FILE_PATH##*.}"

# Track edit in session log
LOG_DIR=".f5/session/logs"
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
fi

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Edited: $FILE_PATH" >> "$LOG_DIR/edits.log"

# Check for source code files
case "$EXT" in
    ts|tsx|js|jsx)
        # Check for console.log in production code
        if ! [[ "$FILE_PATH" == *".test."* || "$FILE_PATH" == *".spec."* || "$FILE_PATH" == *"__tests__"* ]]; then
            if grep -q "console.log" "$FILE_PATH" 2>/dev/null; then
                echo "Warning: console.log found in $FILE_PATH"
                echo "Consider removing before G3 gate"
            fi
        fi
        ;;

    py)
        # Check for print statements in production code
        if ! [[ "$FILE_PATH" == *"test_"* || "$FILE_PATH" == *"_test.py" ]]; then
            if grep -q "^[^#]*print(" "$FILE_PATH" 2>/dev/null; then
                echo "Warning: print() found in $FILE_PATH"
                echo "Consider using logging module"
            fi
        fi
        ;;
esac

# Update edit counter
COUNTER_FILE=".f5/session/edit-count.txt"
if [ -f "$COUNTER_FILE" ]; then
    COUNT=$(cat "$COUNTER_FILE")
    echo $((COUNT + 1)) > "$COUNTER_FILE"
else
    echo "1" > "$COUNTER_FILE"
fi

exit 0
