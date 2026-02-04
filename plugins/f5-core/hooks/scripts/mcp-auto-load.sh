#!/bin/bash
# F5 Framework MCP Auto-Load Hook
# Auto-recommend MCP servers based on current gate

# Try to get current gate from config
GATE=""
if [ -f ".f5/config.json" ]; then
    GATE=$(jq -r '.currentGate // empty' .f5/config.json 2>/dev/null)
fi

# Fallback to session file
if [ -z "$GATE" ] && [ -f ".f5/session/current-gate.txt" ]; then
    GATE=$(cat .f5/session/current-gate.txt 2>/dev/null)
fi

# Default to G2 if no gate found
if [ -z "$GATE" ]; then
    GATE="G2"
fi

echo "🔌 F5 MCP Recommendations"
echo "   Current Gate: $GATE"
echo ""

case "$GATE" in
    D1)
        echo "💡 Recommended for Research Gate:"
        echo "   • tavily    - Web search for requirements research"
        echo "   • context7  - Documentation lookup"
        echo ""
        echo "   Load profile: /f5-mcp profile research"
        ;;
    D2)
        echo "💡 Recommended for SRS Gate:"
        echo "   • context7    - Specification patterns"
        echo "   • sequential  - Spec validation and analysis"
        echo ""
        echo "   Load profile: /f5-mcp profile standard"
        ;;
    D3|D4)
        echo "💡 Recommended for Design Gates:"
        echo "   • context7  - Architecture patterns"
        echo "   • serena    - Code structure analysis"
        echo ""
        echo "   Load profile: /f5-mcp profile standard"
        ;;
    G2)
        echo "💡 Recommended for Implementation Gate:"
        echo "   • context7  - Library documentation"
        echo "   • serena    - Code understanding"
        echo "   • github    - PR management"
        echo ""
        echo "   Load profile: /f5-mcp profile full"
        ;;
    G2.5)
        echo "💡 Recommended for Verification Gate:"
        echo "   • playwright  - Integration testing"
        echo "   • sequential  - Test analysis"
        echo ""
        echo "   Load profile: /f5-mcp profile testing"
        ;;
    G3)
        echo "💡 Recommended for Testing Gate:"
        echo "   • playwright  - E2E testing automation"
        echo "   • sequential  - Test result analysis"
        echo ""
        echo "   Load profile: /f5-mcp profile testing"
        ;;
    G4)
        echo "💡 Recommended for Deployment Gate:"
        echo "   • github  - PR and release management"
        echo ""
        echo "   Load profile: /f5-mcp profile minimal"
        ;;
    *)
        echo "💡 Standard MCP profile recommended"
        echo "   Load profile: /f5-mcp profile standard"
        ;;
esac

echo ""
