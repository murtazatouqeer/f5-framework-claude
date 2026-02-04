---
description: Switch between development modes
argument-hint: <strict|relaxed|maintenance>
---

# /f5-mode - Behavioral Mode Command

Manage and switch behavioral modes for context-aware responses.

## ARGUMENTS
$ARGUMENTS

## OVERVIEW

```
BEHAVIORAL MODES
═══════════════════════════════════════════════════════════════════

  Modes adjust Claude's behavior for different contexts:

  💻 coding      │ Code-focused, minimal explanation
  🎨 creative    │ Innovative, exploratory
  🔬 analytical  │ Data-driven, systematic
  📚 teaching    │ Educational, step-by-step
  🐛 debugging   │ Problem-solving, diagnostic
  👀 review      │ Critical, constructive feedback
  📋 planning    │ Strategic, organized
  🔒 security    │ Paranoid, threat-aware
  ⚡ performance │ Optimization-focused

═══════════════════════════════════════════════════════════════════
```

## SUBCOMMANDS

| Command | Description |
|---------|-------------|
| `list` | List all available modes |
| `show <mode>` | Show mode details |
| `set <mode>` | Activate a mode |
| `reset` | Return to default mode |
| `auto [on\|off]` | Toggle auto-detection |
| `status` | Show current mode |

---

## ACTION: LIST_MODES

### `/f5-mode list`

Display all available behavioral modes:

```markdown
## 🎭 Available Modes

| Emoji | Mode | Description | Verbosity |
|-------|------|-------------|-----------|
| 💻 | coding | Code-focused output | 2 |
| 🎨 | creative | Innovative approach | 4 |
| 🔬 | analytical | Data-driven analysis | 4 |
| 📚 | teaching | Educational guidance | 5 |
| 🐛 | debugging | Systematic problem-solving | 3 |
| 👀 | review | Code review perspective | 3 |
| 📋 | planning | Strategic thinking | 4 |
| 🔒 | security | Security-focused | 4 |
| ⚡ | performance | Optimization-focused | 3 |

### Current: {{CURRENT_MODE}}
### Auto-detection: {{AUTO_STATUS}}
```

---

## ACTION: SHOW_MODE

### `/f5-mode show <mode>`

Display detailed information about a specific mode:

```markdown
## 🔒 Security Mode

### Overview
Security-focused, paranoid approach to development.

### Characteristics
| Aspect | Value |
|--------|-------|
| Tone | Cautious, thorough |
| Verbosity | 4 (detailed) |
| Creativity | Low |
| Risk Tolerance | Zero |

### Behaviors
- Assume threats exist
- Validate all inputs
- Check OWASP Top 10
- Consider attack vectors
- Defense in depth
- Least privilege principle

### Triggers (Auto-Detection)
**Keywords:** security, auth, password, encrypt, sensitive, vulnerability

### Output Preferences
- Include threat analysis
- Show mitigations
- OWASP compliance check
- Security headers review

### Use Cases
- Authentication implementation
- Authorization logic
- Sensitive data handling
- API security
- Input validation
```

---

## ACTION: SET_MODE

### `/f5-mode set <mode>`

Activate a specific behavioral mode:

```markdown
## ✅ Mode Activated: 🔒 Security

### Characteristics
| Aspect | Value |
|--------|-------|
| Tone | Cautious, thorough |
| Verbosity | 4 (detailed) |
| Risk Tolerance | Zero |

### Behaviors
- Assume threats exist
- Validate all inputs
- Check OWASP Top 10
- Consider attack vectors
- Defense in depth

### I will now:
- Review code for vulnerabilities
- Suggest security improvements
- Warn about potential risks
- Apply security best practices

### Quick Switch
```bash
/f5-mode set coding    # Switch to coding
/f5-mode reset         # Return to default
```
```

---

## ACTION: SHOW_STATUS

### `/f5-mode status`

Display current mode status:

```markdown
## 📊 Mode Status

| Field | Value |
|-------|-------|
| Current Mode | 🔒 security |
| Auto-detection | ✅ Enabled |
| Verbosity | 4 |
| Session Start | 10 minutes ago |

### Recent Mode Changes
| Time | Mode | Trigger |
|------|------|---------|
| 10m ago | 🔒 security | Keyword: "auth" |
| 25m ago | 💻 coding | Manual |
| 1h ago | 📚 teaching | Keyword: "explain" |

### Quick Commands
```bash
/f5-mode set coding    # Switch mode
/f5-mode reset         # Default mode
/f5-mode auto off      # Disable auto
```
```

---

## ACTION: TOGGLE_AUTO

### `/f5-mode auto [on|off]`

Toggle automatic mode detection:

```markdown
## 🔄 Auto-Detection: {{STATUS}}

### When Enabled
Modes automatically switch based on:
- Keywords in your messages
- Current gate context
- Task type detection

### When Disabled
Mode only changes when you explicitly set it.

### Current Settings
| Setting | Value |
|---------|-------|
| Auto-detection | {{STATUS}} |
| Current Mode | {{MODE}} |
| Mode Locked | {{LOCKED}} |
```

---

## ACTION: RESET_MODE

### `/f5-mode reset`

Return to default mode:

```markdown
## 🔄 Mode Reset

Returned to default mode.

| Field | Value |
|-------|-------|
| Mode | Default |
| Verbosity | 3 |
| Auto-detection | Enabled |

### Default Characteristics
- Balanced explanations
- Consider multiple approaches
- Ask clarifying questions when needed
- Provide context appropriately
```

---

## MODE DETAILS

### 💻 Coding Mode
```yaml
focus: Code implementation
verbosity: 2
behaviors:
  - Code-first responses
  - Minimal explanations
  - Follow existing patterns
  - Production-ready code
  - Include error handling
  - Type-safe implementations
triggers:
  - "implement", "code", "write"
  - Gate G2 context
```

### 🎨 Creative Mode
```yaml
focus: Innovation and exploration
verbosity: 4
behaviors:
  - Explore unconventional solutions
  - Suggest innovative approaches
  - Think outside the box
  - Propose experimental features
triggers:
  - "brainstorm", "creative", "innovative"
  - "new approach", "different way"
```

### 🔬 Analytical Mode
```yaml
focus: Deep analysis
verbosity: 4
behaviors:
  - Systematic analysis
  - Data-driven decisions
  - Identify edge cases
  - Quantify trade-offs
triggers:
  - "analyze", "compare", "evaluate"
  - "assess", "investigate"
```

### 📚 Teaching Mode
```yaml
focus: Education
verbosity: 5
behaviors:
  - Step-by-step explanations
  - Use analogies and examples
  - Check understanding
  - Build on fundamentals
triggers:
  - "explain", "teach", "how does"
  - "why", "help me understand"
```

### 🐛 Debugging Mode
```yaml
focus: Problem-solving
verbosity: 3
behaviors:
  - Systematic diagnosis
  - Root cause analysis
  - Hypothesis testing
  - Verification of fixes
triggers:
  - "bug", "error", "not working"
  - "fix", "issue", "problem"
```

### 👀 Review Mode
```yaml
focus: Code review
verbosity: 3
behaviors:
  - Identify issues proactively
  - Suggest improvements
  - Check for security issues
  - Constructive feedback
triggers:
  - "review", "check", "feedback"
  - "pr", "improve"
```

### 📋 Planning Mode
```yaml
focus: Strategic thinking
verbosity: 4
behaviors:
  - Big picture thinking
  - Break down into phases
  - Identify dependencies
  - Consider risks
triggers:
  - "plan", "roadmap", "strategy"
  - Gates D1-D4 context
```

### 🔒 Security Mode
```yaml
focus: Security-first
verbosity: 4
risk_tolerance: zero
behaviors:
  - Assume threats exist
  - Validate all inputs
  - Check OWASP Top 10
  - Defense in depth
triggers:
  - "security", "auth", "password"
  - "encrypt", "vulnerability"
```

### ⚡ Performance Mode
```yaml
focus: Optimization
verbosity: 3
behaviors:
  - Measure before optimize
  - Identify bottlenecks
  - Big O complexity analysis
  - Caching strategies
triggers:
  - "slow", "optimize", "performance"
  - "fast", "efficient"
```

---

## MODE COMBINATIONS

Combine modes for specialized behavior:

| Combination | Modes | Use Case |
|-------------|-------|----------|
| `secure_coding` | security + coding | Auth implementation |
| `deep_review` | analytical + review | PR reviews |
| `innovative_design` | creative + planning | New feature design |
| `guided_debugging` | teaching + debugging | Junior dev assistance |
| `perf_analysis` | performance + analytical | Bottleneck investigation |
| `security_audit` | security + review | Vulnerability assessment |

```bash
/f5-mode set secure_coding
/f5-mode set deep_review
```

---

## GATE-BASED RECOMMENDATIONS

| Gate | Recommended Mode | Alternatives |
|------|------------------|--------------|
| D1 | 📋 planning | analytical, creative |
| D2 | 🔬 analytical | planning |
| D3 | 📋 planning | analytical, creative |
| D4 | 🔬 analytical | coding |
| G2 | 💻 coding | review, security |
| G3 | 🐛 debugging | analytical |
| G4 | 👀 review | security, performance |

---

## AUTO-DETECTION PRIORITY

When multiple triggers match, modes are prioritized:

1. 🔒 **security** - Security always first
2. 🐛 **debugging** - Active issues
3. 👀 **review** - Code review context
4. 💻 **coding** - Implementation
5. 🔬 **analytical** - Analysis tasks
6. 📋 **planning** - Planning tasks
7. 📚 **teaching** - Educational context
8. 🎨 **creative** - Creative tasks
9. ⚡ **performance** - Optimization
10. **default** - Fallback

---

## EXAMPLES

```bash
# Check current mode
/f5-mode status

# List all modes
/f5-mode list

# Activate security mode
/f5-mode set security

# Show mode details
/f5-mode show debugging

# Enable auto-detection
/f5-mode auto on

# Return to default
/f5-mode reset

# Use mode combination
/f5-mode set secure_coding

# Use mode with other commands
/f5-implement auth --mode security
/f5-review full --mode analytical
```

---

## CONFIGURATION

Modes are configured in `.f5/config/behavioral.yaml`.

---

## SEE ALSO

- `.f5/config/behavioral.yaml` - Mode configuration
- `.f5/config/token-optimization.yaml` - Verbosity settings
- `/f5-persona` - Role-based context (who)
- `/f5-agent` - Task-based agents (what)
