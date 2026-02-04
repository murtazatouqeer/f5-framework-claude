#!/bin/bash
# F5 Husky — Pre-Edit Checklist Reminder
# Nhắc nhở khi Claude Code sửa file mà có checklist active

FILE_PATH="${TOOL_INPUT_FILE_PATH:-}"

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Tìm checklist active liên quan đến file đang sửa
CHECKLIST_DIR=".claude/checklist"
if [ -d "$CHECKLIST_DIR" ]; then
    for CL_FILE in "$CHECKLIST_DIR"/*.md; do
        [ -f "$CL_FILE" ] || continue
        # Skip templates
        echo "$CL_FILE" | grep -q "_templates" && continue

        # Check nếu file đang sửa được mention trong checklist
        if grep -q "$FILE_PATH" "$CL_FILE" 2>/dev/null; then
            TICKET_ID=$(basename "$CL_FILE" .md)
            echo "📋 Reminder: File này liên quan đến checklist #$TICKET_ID"
            echo "   Xem: $CL_FILE"
        fi
    done
fi

exit 0
