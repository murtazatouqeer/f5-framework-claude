#!/bin/bash
# F5 Framework Pre-Edit Hook
# Validates quality gate requirements before allowing edits

# Get the file being edited from environment
FILE_PATH="${TOOL_INPUT_FILE_PATH:-}"

# Skip if no file path
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Get file extension
EXT="${FILE_PATH##*.}"

# Check for source code files
case "$EXT" in
    ts|tsx|js|jsx|py|java|go|rs|cs)
        # Check if current gate allows implementation
        if [ -f ".f5/session/current-gate.txt" ]; then
            CURRENT_GATE=$(cat .f5/session/current-gate.txt)

            # Only allow implementation after D4 gate
            case "$CURRENT_GATE" in
                D1|D2|D3|D4)
                    echo "Warning: Implementation should wait until G2 gate"
                    echo "Current gate: $CURRENT_GATE"
                    ;;
            esac
        fi

        # Check for traceability requirement
        if [ -f ".f5/config.yaml" ]; then
            REQUIRE_TRACE=$(grep -o 'require_traceability: true' .f5/config.yaml 2>/dev/null)
            if [ -n "$REQUIRE_TRACE" ]; then
                echo "Reminder: Add traceability comments (REQ-XXX) to new code"
            fi
        fi
        ;;
esac

exit 0
