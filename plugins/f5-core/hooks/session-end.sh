#!/bin/bash
# F5 Framework Session End Hook
# Generates session summary and cleanup

SESSION_DIR=".f5/session"
SUMMARY_FILE="$SESSION_DIR/session-summary.md"

# Create session directory if needed
mkdir -p "$SESSION_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
DATE_ONLY=$(date +"%Y-%m-%d")

# Start summary
cat > "$SUMMARY_FILE" << EOF
# F5 Session Summary

**Date**: $DATE_ONLY
**End Time**: $TIMESTAMP

## Session Statistics

EOF

# Add edit count if available
if [ -f "$SESSION_DIR/edit-count.txt" ]; then
    EDIT_COUNT=$(cat "$SESSION_DIR/edit-count.txt")
    echo "- **Files Edited**: $EDIT_COUNT" >> "$SUMMARY_FILE"
fi

# Add current gate if available
if [ -f "$SESSION_DIR/current-gate.txt" ]; then
    CURRENT_GATE=$(cat "$SESSION_DIR/current-gate.txt")
    echo "- **Current Gate**: $CURRENT_GATE" >> "$SUMMARY_FILE"
fi

# Add recent edits if log exists
if [ -f "$SESSION_DIR/logs/edits.log" ]; then
    echo "" >> "$SUMMARY_FILE"
    echo "## Recent Edits" >> "$SUMMARY_FILE"
    echo "\`\`\`" >> "$SUMMARY_FILE"
    tail -20 "$SESSION_DIR/logs/edits.log" >> "$SUMMARY_FILE"
    echo "\`\`\`" >> "$SUMMARY_FILE"
fi

# Add pending tasks reminder
echo "" >> "$SUMMARY_FILE"
echo "## Next Steps" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"
echo "- Review session changes" >> "$SUMMARY_FILE"
echo "- Run tests before commit" >> "$SUMMARY_FILE"
echo "- Update gate status if applicable" >> "$SUMMARY_FILE"

# Display summary location
echo "Session summary saved to: $SUMMARY_FILE"

# Reset edit counter for next session
rm -f "$SESSION_DIR/edit-count.txt"

exit 0
