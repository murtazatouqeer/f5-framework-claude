---
description: View project analytics and metrics
argument-hint: [--period <days>]
---

# /f5-analytics - F5 Framework Analytics & Metrics System

> **Purpose**: View usage metrics, track patterns, and get AI-powered insights
> **Version**: 2.0.0
> **Category**: Analytics

---

## Command Syntax

```bash
# View overview dashboard
/f5-analytics

# Specific dashboard
/f5-analytics --dashboard <name>

# Generate report
/f5-analytics report <type>

# View insights
/f5-analytics insights

# Export data
/f5-analytics export --format <json|csv|markdown>

# View specific metric category
/f5-analytics --metric <category>

# Time range filter
/f5-analytics --range <today|week|month|all>

# Verbosity control
/f5-analytics --v1|--v2|--v3|--v4|--v5
```

---

## Input Processing

### 1. Parse Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--dashboard` | Dashboard to display | `overview` |
| `report` | Generate report type | - |
| `insights` | Show AI insights | - |
| `export` | Export data | - |
| `--metric` | Specific metric category | all |
| `--range` | Time range filter | `week` |
| `--format` | Export format | `markdown` |
| `--v{1-5}` | Verbosity level | 3 |

### 2. Available Dashboards

| Dashboard | Description |
|-----------|-------------|
| `overview` | General metrics summary |
| `gates` | Quality gate progress |
| `errors` | Error tracking |
| `mcp` | MCP server health |
| `commands` | Command usage |
| `productivity` | Productivity metrics |

### 3. Report Types

| Report | Description |
|--------|-------------|
| `daily` | Today's summary |
| `weekly` | Weekly trends |
| `gate` | Gate-focused report |
| `error` | Error analysis |
| `productivity` | Productivity report |
| `custom` | Custom report |

### 4. Metric Categories

| Category | Description |
|----------|-------------|
| `commands` | Command usage |
| `agents` | Agent utilization |
| `modes` | Mode patterns |
| `personas` | Persona activation |
| `gates` | Gate progress |
| `errors` | Error tracking |
| `sessions` | Session stats |
| `mcp` | MCP usage |

---

## Execution Flow

```
/f5-analytics
     │
     ▼
┌─────────────────┐
│ Load Config     │
│ analytics/config│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load Data       │
│ (range filter)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Process Metrics │
│ Calculate Stats │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate        │
│ Insights        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Render          │
│ Dashboard/Report│
└─────────────────┘
```

---

## Dashboards

### Overview Dashboard (Default)

```
═══════════════════════════════════════════════════════════════
                    F5 ANALYTICS DASHBOARD
═══════════════════════════════════════════════════════════════

📊 QUICK STATS                               Period: Last 7 Days
───────────────────────────────────────────────────────────────
Commands Executed   │ 142          Success Rate   │ 94.3%
Active Gate         │ D4           Session Hours  │ 12.5h
Top Command         │ /f5-implement Errors Today  │ 3

📈 COMMAND USAGE (Top 5)
───────────────────────────────────────────────────────────────
/f5-implement    ████████████████████████████  45 (32%)
/f5-gate         ███████████████               28 (20%)
/f5-load         ████████████                  22 (15%)
/f5-test         ████████                      15 (11%)
/f5-spec         ██████                        12 (8%)

🚧 GATE PROGRESS
───────────────────────────────────────────────────────────────
D1 ✅ │ D2 ✅ │ D3 ✅ │ D4 🔄 │ G2 ⏳ │ G3 ⏳ │ G4 ⏳

⚡ PRODUCTIVITY SCORE: 78/100 (Good)
───────────────────────────────────────────────────────────────

💡 INSIGHTS
───────────────────────────────────────────────────────────────
• Gate D4 taking 20% longer than average - check blockers
• Consider using /f5-tdd for better test coverage
• MCP Context7 fallback rate increased - verify connection

═══════════════════════════════════════════════════════════════
```

### Gates Dashboard

```
═══════════════════════════════════════════════════════════════
                    GATES PROGRESS DASHBOARD
═══════════════════════════════════════════════════════════════

📊 OVERALL PROGRESS
───────────────────────────────────────────────────────────────
[██████████████████░░░░░░░░░░░░] 57% (4/7 gates)

📋 GATE DETAILS
───────────────────────────────────────────────────────────────
Gate │ Status │ Duration │ Target │ Deviation
─────┼────────┼──────────┼────────┼───────────
D1   │ ✅     │ 2d       │ 3d     │ -1d (early)
D2   │ ✅     │ 4d       │ 5d     │ -1d (early)
D3   │ ✅     │ 8d       │ 7d     │ +1d (late)
D4   │ 🔄     │ 6d...    │ 5d     │ +1d (over)
G2   │ ⏳     │ -        │ 14d    │ -
G3   │ ⏳     │ -        │ 7d     │ -
G4   │ ⏳     │ -        │ 3d     │ -

📈 TIMELINE
───────────────────────────────────────────────────────────────
Jan 1      Jan 8      Jan 15     Jan 22     Today
│          │          │          │          │
├──D1──┤   │          │          │          │
       ├───D2───┤     │          │          │
              ├────D3────┤       │          │
                       ├───D4────┼──────────▶
                                            Est: Jan 25

🚧 CURRENT BLOCKERS
───────────────────────────────────────────────────────────────
• API spec review pending customer approval
• Security audit not yet scheduled

═══════════════════════════════════════════════════════════════
```

### Errors Dashboard

```
═══════════════════════════════════════════════════════════════
                    ERRORS DASHBOARD
═══════════════════════════════════════════════════════════════

📊 ERROR SUMMARY                             Period: Last 7 Days
───────────────────────────────────────────────────────────────
Total Errors   │ 23           Recovery Rate  │ 82.6%
Critical       │ 2            Auto-Fixed     │ 15
Warnings       │ 21           Manual Fix     │ 6

📈 ERROR TREND
───────────────────────────────────────────────────────────────
Mon │ ███                    3
Tue │ █████                  5
Wed │ ██████                 6
Thu │ ████                   4
Fri │ ██                     2
Sat │ █                      1
Sun │ ██                     2

🏷️ BY CATEGORY
───────────────────────────────────────────────────────────────
⚙️ CFG (Configuration)  │ ████████████          8 (35%)
🔌 MCP (MCP Server)     │ ████████              6 (26%)
🔄 WFL (Workflow)       │ █████                 4 (17%)
📁 FIL (File)           │ ████                  3 (13%)
🚧 GAT (Gate)           │ ██                    2 (9%)

🔝 TOP RECURRING ERRORS
───────────────────────────────────────────────────────────────
1. MCP001: Context7 timeout (4 occurrences)
2. CFG003: Profile missing (3 occurrences)
3. WFL004: Traceability broken (2 occurrences)

💡 PREVENTION TIPS
───────────────────────────────────────────────────────────────
• Run /f5-selftest --fix to resolve configuration issues
• Check MCP server health with /f5-analytics --dashboard mcp
• Use /f5-implement traceability checker before commits

═══════════════════════════════════════════════════════════════
```

### MCP Dashboard

```
═══════════════════════════════════════════════════════════════
                    MCP SERVER HEALTH
═══════════════════════════════════════════════════════════════

🔌 SERVER STATUS
───────────────────────────────────────────────────────────────
Server      │ Status │ Calls │ Fallback │ Avg Response
────────────┼────────┼───────┼──────────┼─────────────
Context7    │ ✅     │ 89    │ 4%       │ 1.2s
Sequential  │ ✅     │ 45    │ 2%       │ 2.8s
Serena      │ ⚠️     │ 23    │ 15%      │ 3.5s
Playwright  │ ✅     │ 12    │ 0%       │ 4.1s
Magic       │ ✅     │ 18    │ 1%       │ 1.8s

📈 USAGE DISTRIBUTION
───────────────────────────────────────────────────────────────
Context7    ████████████████████████████████████   48%
Sequential  █████████████████████                   24%
Serena      ████████████                            12%
Magic       █████████                               10%
Playwright  ██████                                   6%

⚠️ ALERTS
───────────────────────────────────────────────────────────────
• Serena fallback rate above threshold (15% > 10%)
• Recommendation: Check Serena server configuration

📊 FALLBACK USAGE
───────────────────────────────────────────────────────────────
Primary Failed → Fallback Used:
• Context7 → WebSearch: 4 times
• Serena → Native Analysis: 3 times
• Sequential → Native Reasoning: 1 time

═══════════════════════════════════════════════════════════════
```

---

## Reports

### Daily Report

```markdown
# F5 Daily Report - January 15, 2024

## Summary
- **Session Duration**: 4.5 hours
- **Commands Executed**: 28
- **Success Rate**: 96.4%
- **Errors**: 1

## Activity Breakdown
| Category | Count | Time |
|----------|-------|------|
| Implementation | 12 | 2.1h |
| Testing | 8 | 1.2h |
| Documentation | 5 | 0.8h |
| Other | 3 | 0.4h |

## Gate Progress
- **Current**: D4 (Detail Design)
- **Progress**: 60% complete
- **Items Done**: 3/5

## Key Achievements
1. Completed API spec for user module
2. Fixed authentication flow
3. Updated database schema

## Tomorrow's Focus
- Complete remaining D4 items
- Begin implementation phase
```

### Weekly Report

```markdown
# F5 Weekly Report - Week 3, January 2024

## Overview
| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Commands | 142 | 128 | +11% |
| Errors | 23 | 31 | -26% |
| Session Hours | 12.5h | 14.2h | -12% |
| Gates Completed | 1 | 2 | -1 |

## Command Usage Trends
[Chart showing daily command usage]

## Error Analysis
- **Most Common**: MCP timeout (4)
- **Resolution Rate**: 82.6%
- **Improvement**: -26% from last week

## Gate Progress
- D3 completed (Jan 12)
- D4 in progress (60%)
- Projected G2 start: Jan 20

## Insights
1. **Productivity**: Above average this week
2. **Quality**: Error rate decreased significantly
3. **Pace**: Slightly behind schedule on D4

## Recommendations
1. Focus on completing D4 blockers
2. Schedule customer review for API specs
3. Consider using TDD for implementation phase
```

---

## Insights Engine

### Automatic Insights

The insights engine analyzes usage patterns and provides:

1. **Productivity Insights**
   - Command efficiency
   - Time distribution
   - Gate velocity

2. **Optimization Insights**
   - MCP health recommendations
   - Workflow improvements
   - Error prevention tips

3. **Learning Insights**
   - Command discovery
   - Persona suggestions
   - Mode recommendations

### Example Insights

```
💡 INSIGHTS

🎯 Productivity
   • Your most productive hours are 9-11 AM
   • Consider batching similar tasks

⚡ Optimization
   • MCP fallback rate is high - check configurations
   • Gate D4 could benefit from breaking into smaller tasks

📚 Learning
   • Try /f5-tdd for test-driven development
   • The security persona might help with auth implementation
```

---

## Data Export

### JSON Export
```bash
/f5-analytics export --format json --range month
```

Output: `.f5/analytics/exports/export-2024-01-15.json`

### CSV Export
```bash
/f5-analytics export --format csv --metric commands
```

Output: `.f5/analytics/exports/commands-2024-01-15.csv`

### Markdown Export
```bash
/f5-analytics export --format markdown
```

Output: `.f5/analytics/exports/report-2024-01-15.md`

---

## Verbosity Levels

### Level 1 (--v1): Ultra-Concise
```
Analytics: 142 cmds | 94% success | Gate D4 | 12.5h
```

### Level 2 (--v2): Concise
```
## Analytics Summary

📊 142 commands | 94% success | 23 errors
🚧 Gate D4 (60%) | 12.5h session time

💡 Gate D4 over target | MCP fallback high
```

### Level 3 (--v3): Balanced (Default)
Overview dashboard with key metrics and insights.

### Level 4 (--v4): Detailed
Full dashboard with charts, trends, and recommendations.

### Level 5 (--v5): Comprehensive
Complete analytics with historical data, benchmarks, and detailed insights.

---

## Configuration

Analytics configuration is in `.f5/analytics/config.yaml`:
- Metrics categories and tracking
- Data collection settings
- Insights rules
- Report templates
- Dashboard configurations
- Alert thresholds

---

## Data Storage

Analytics data is stored in `.f5/analytics/data/`:
- `command-usage.json` - Command invocations
- `agent-usage.json` - Agent delegations
- `mode-usage.json` - Mode activations
- `persona-usage.json` - Persona activations
- `gate-progress.json` - Gate timeline
- `error-log.json` - Error occurrences
- `session-stats.json` - Session metrics
- `mcp-usage.json` - MCP server calls

---

## Privacy

By default, analytics:
- Does NOT track file paths
- Does NOT track file content
- Only tracks aggregate metrics
- Stays local (no external transmission)

---

## Examples

### View Overview
```bash
/f5-analytics
```

### View Gates Progress
```bash
/f5-analytics --dashboard gates
```

### Generate Weekly Report
```bash
/f5-analytics report weekly
```

### Export Commands Data
```bash
/f5-analytics export --format csv --metric commands
```

### View Insights Only
```bash
/f5-analytics insights
```

### Last Month's Errors
```bash
/f5-analytics --dashboard errors --range month
```

---

## Related Commands

| Command | Description |
|---------|-------------|
| `/f5-status` | Quick status check |
| `/f5-selftest` | System diagnostics |
| `/f5-gate` | Gate management |
| `/f5-load` | Load project context |

---

*F5 Framework Analytics & Metrics System v2.0.0*
