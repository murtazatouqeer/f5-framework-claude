---
description: Deep research with web search and documentation
argument-hint: <topic> [--depth quick|deep|exhaustive]
mcp-servers: tavily, context7
---

# /f5-research - Deep Research

Conduct deep research with AI agents and multi-source synthesis.

## ARGUMENTS
The user's request is: $ARGUMENTS

## PURPOSE

Deep research for complex investigations:
- Multi-source information gathering
- Evidence synthesis and validation
- Structured analysis and reporting
- Quality gate D1 (Research Complete) support

## RESEARCH CAPABILITIES

| Capability | Description | Tools Used |
|------------|-------------|------------|
| Web Search | Current information from web | Tavily |
| Documentation | Official library/framework docs | Context7 |
| Code Analysis | Codebase investigation | Serena, Grep |
| Reasoning | Complex multi-step analysis | Sequential |
| Validation | Cross-reference and verify | Multiple |

## ACTIONS

### Start Research Session

```
/f5-research "React Server Components best practices"

Output:
🔍 Starting Deep Research Session

Topic: React Server Components best practices

Planning research strategy...

Research Plan:
1. Search for official React documentation
2. Find community best practices (2024)
3. Identify common patterns and anti-patterns
4. Gather performance considerations
5. Synthesize findings

Estimated sources: 10-15
Estimated time: 2-3 minutes

Beginning research...
```

### Research with Specific Focus

```
/f5-research "authentication patterns" --focus security

Output:
🔍 Deep Research: Authentication Patterns

Focus Area: Security

Research Plan:
1. Search for OWASP authentication guidelines
2. Find JWT security best practices
3. Research session management patterns
4. Identify common vulnerabilities
5. Gather mitigation strategies

Security-focused sources:
• OWASP guidelines
• CVE databases
• Security advisories
• Penetration testing reports

Beginning security-focused research...
```

### Research for Requirements (Gate D1)

```
/f5-research "user authentication requirements" --gate D1

Output:
🔍 Requirements Research (Gate D1)

Topic: User Authentication Requirements

Research aligned with Gate D1 criteria:
• Evidence count target: ≥3 sources
• Quality score target: ≥80%

Research Plan:
1. Industry standards review
2. Competitor analysis
3. User expectations research
4. Security requirements
5. Compliance requirements (if applicable)

Progress tracking:
  Sources found: 0/3 minimum
  Quality score: Calculating...

Beginning D1-focused research...
```

### Research Output

```
═══════════════════════════════════════════════════════════
📊 RESEARCH REPORT: React Server Components Best Practices
═══════════════════════════════════════════════════════════

## Executive Summary

React Server Components (RSC) represent a paradigm shift in
React development, enabling server-side rendering of components
with zero client-side JavaScript bundle impact.

## Key Findings

### 1. When to Use Server Components
**Evidence: 4 sources | Confidence: High**

• Default to Server Components for:
  - Data fetching
  - Backend resource access
  - Static content
  - Large dependencies

• Use Client Components for:
  - Interactivity (onClick, onChange)
  - Browser APIs
  - State management
  - Effects (useEffect)

### 2. Best Practices
**Evidence: 6 sources | Confidence: High**

1. **Composition Pattern**
   Wrap client components in server components for data fetching

2. **Serialization Boundary**
   Only serializable props can cross server/client boundary

3. **Streaming**
   Use Suspense for progressive rendering

### 3. Common Anti-Patterns
**Evidence: 3 sources | Confidence: Medium**

• ❌ Using 'use client' unnecessarily
• ❌ Passing non-serializable props
• ❌ Ignoring streaming opportunities
• ❌ Over-fetching data

### 4. Performance Considerations
**Evidence: 5 sources | Confidence: High**

• Reduced JavaScript bundle size
• Faster initial page load
• Better SEO capabilities
• Server-side caching benefits

## Sources

1. React Official Documentation (react.dev) - High credibility
2. Next.js Documentation (nextjs.org) - High credibility
3. Vercel Blog - Medium credibility
4. Community discussions (GitHub) - Medium credibility

## Quality Metrics

| Metric | Score |
|--------|-------|
| Source diversity | 85% |
| Evidence coverage | 90% |
| Confidence level | High |
| Overall quality | 88% |

## Recommendations

1. Start with Server Components as default
2. Only add 'use client' when necessary
3. Use composition for optimal performance
4. Implement streaming with Suspense

═══════════════════════════════════════════════════════════
Research completed | 12 sources analyzed | Quality: 88%
═══════════════════════════════════════════════════════════
```

## RESEARCH MODES

### Quick Research

```
/f5-research "topic" --quick

• 3-5 sources
• 1-2 minutes
• Key findings only
• Good for fact-checking
```

### Standard Research

```
/f5-research "topic"

• 8-12 sources
• 3-5 minutes
• Full analysis
• Default mode
```

### Deep Research

```
/f5-research "topic" --deep

• 15-20+ sources
• 5-10 minutes
• Comprehensive analysis
• Multiple perspectives
• Contradiction resolution
```

### Exhaustive Research

```
/f5-research "topic" --exhaustive

• 25+ sources
• 10-15 minutes
• Academic-level depth
• Full citation chain
• Expert synthesis
```

## RESEARCH STRATEGIES

### By Topic Type

| Topic Type | Strategy | Primary Tools |
|------------|----------|---------------|
| Technical | Docs + Code | Context7, Serena |
| Current Events | Web Search | Tavily |
| Best Practices | Multi-source | Tavily, Context7 |
| Architecture | Analysis | Sequential, Serena |
| Security | Specialized | Tavily (OWASP focus) |

### Multi-Hop Research

```
/f5-research "microservices communication patterns" --multi-hop

Research Flow:
  Hop 1: Overview of patterns
    → Found: REST, gRPC, Message Queues, Event Sourcing

  Hop 2: Deep dive each pattern
    → REST: 5 sources
    → gRPC: 4 sources
    → Message Queues: 6 sources
    → Event Sourcing: 4 sources

  Hop 3: Comparison and trade-offs
    → Performance comparisons
    → Use case recommendations
    → Migration patterns

Total sources: 24
Hops completed: 3
```

## INTEGRATION WITH GATES

### Gate D1: Research Complete

```
/f5-research "feature requirements" --gate D1

Gate D1 Requirements:
  ✓ Minimum 3 evidence sources
  ✓ Quality score ≥ 80%
  ✓ Key findings documented
  ✓ Recommendations provided

Research Output:
  → Saved to .f5/research/feature-requirements/
  → Gate D1 checklist updated
  → Ready for /f5-gate check D1
```

### Research to SRS Flow

```
/f5-research "user authentication"
    ↓
Research complete, findings documented
    ↓
/f5-spec generate srs --from-research
    ↓
SRS generated with research citations
    ↓
/f5-gate check D2
```

## RESEARCH OUTPUT

### File Structure

```
.f5/research/
├── topic-name/
│   ├── report.md           # Full research report
│   ├── sources.json        # Source metadata
│   ├── findings.md         # Key findings summary
│   └── raw/                # Raw search results
│       ├── search-1.json
│       └── search-2.json
```

### Export Formats

```
/f5-research export --format markdown
/f5-research export --format pdf
/f5-research export --format json
```

## EXAMPLES

```bash
# Basic research
/f5-research "React hooks best practices"

# Quick fact check
/f5-research "Node.js 22 features" --quick

# Deep technical research
/f5-research "distributed systems patterns" --deep

# Security focused
/f5-research "API security" --focus security

# Gate D1 aligned
/f5-research "feature X requirements" --gate D1

# Multi-hop investigation
/f5-research "microservices architecture" --multi-hop

# Specific depth
/f5-research "GraphQL vs REST" --sources 15

# Export research
/f5-research export authentication --format pdf

# Continue previous research
/f5-research continue authentication

# List research sessions
/f5-research list
```

## CONFIGURATION

Research settings in `.f5/config.json`:

```json
{
  "research": {
    "defaultDepth": "standard",
    "minSources": 5,
    "qualityThreshold": 80,
    "saveResults": true,
    "outputPath": ".f5/research/",
    "preferredSources": [
      "official-docs",
      "academic",
      "industry-reports"
    ],
    "excludeDomains": [
      "spam-site.com"
    ]
  }
}
```

## MCP SERVER USAGE

### Tavily - Web Search

```yaml
usage:
  - General web research
  - Current information
  - News and updates
  - Multiple source discovery

capabilities:
  - Domain filtering
  - Date filtering
  - Content extraction
  - News-specific search
```

### Context7 - Documentation

```yaml
usage:
  - Official library docs
  - Framework guides
  - API references
  - Version-specific info

capabilities:
  - Curated documentation
  - Code examples
  - Pattern guidance
```

### Sequential - Analysis

```yaml
usage:
  - Complex reasoning
  - Synthesis across sources
  - Contradiction resolution
  - Structured analysis

capabilities:
  - Multi-step thinking
  - Hypothesis testing
  - Evidence evaluation
```

## QUALITY METRICS

| Metric | Description | Target |
|--------|-------------|--------|
| Source Count | Number of sources | ≥5 |
| Source Diversity | Different domains | ≥3 |
| Credibility Score | Source reliability | ≥80% |
| Coverage | Topic completeness | ≥85% |
| Confidence | Finding reliability | High/Medium |

## TROUBLESHOOTING

### "Insufficient sources found"

```
Expand search terms or try:
/f5-research "topic" --expand-queries

Generates alternative search queries automatically.
```

### "Low quality score"

```
Add higher-quality sources:
/f5-research "topic" --prefer-academic
/f5-research "topic" --prefer-official
```

### "Contradictory findings"

```
Research auto-detects contradictions.
Review in report under "Conflicting Views" section.

For resolution:
/f5-research resolve "topic"
```

---

**Tip:** Use `/f5-research --gate D1` when gathering requirements to ensure your research meets quality gate standards!
