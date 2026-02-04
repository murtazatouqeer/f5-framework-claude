# F5 Framework Modes

> Behavioral flags that modify how Claude Code executes commands.
> Add these flags to any /f5- command to change behavior.

## Available Modes

### --think (Deep Reasoning)

**Purpose:** Activate extended thinking and show chain of thought.

**When to use:**
- Complex architectural decisions
- Debugging difficult issues
- Trade-off analysis
- Security review

**Behavior:**
- Shows step-by-step reasoning
- Considers multiple alternatives
- Explains why decisions were made
- Takes more time but higher quality

**Example:**
```
/f5-implement "auth system" --think
/f5-strict-validate --think
```

**Token impact:** +50-100% tokens

---

### --think-hard (Extended Deep Reasoning)

**Purpose:** Maximum depth reasoning for critical decisions.

**When to use:**
- Critical architecture choices
- Security-sensitive implementations
- Performance optimization
- Complex refactoring

**Behavior:**
- Multi-pass analysis
- Considers edge cases extensively
- Validates assumptions
- Provides confidence levels

**Example:**
```
/f5-implement "payment processing" --think-hard
```

**Token impact:** +100-200% tokens

---

### --safe-mode (Preview First)

**Purpose:** Preview all changes before applying them.

**When to use:**
- Refactoring existing code
- Critical production code
- When uncertain about impact
- Learning the codebase

**Behavior:**
- Shows proposed changes without applying
- Asks for confirmation before each change
- Creates backup points
- Allows selective application

**Example:**
```
/f5-implement "refactor auth" --safe-mode
```

**Interactive prompts:**
```
Proposed change to src/auth.ts:
[diff preview]

Apply this change? [y/n/skip/abort]
```

---

### --compress (Token Efficient)

**Purpose:** Reduce output by 30-50% while preserving information.

**When to use:**
- Large codebases
- Long sessions approaching context limit
- When you need concise answers
- Batch operations

**Behavior:**
- Uses symbols instead of verbose text
- Shorter explanations
- Tables instead of lists
- Code-only responses when appropriate

**Symbol System:**
| Symbol | Meaning |
|--------|---------|
| -> | leads to, results in |
| <- | caused by |
| ++ | added, increased |
| -- | removed, decreased |
| !! | important, warning |
| ?? | uncertain, needs review |
| ok | passed, success |
| xx | failed, error |

**Example:**
```
/f5-strict-validate --compress

# Output:
## Validation
ok Coverage: 92%
ok REQ-001: src/auth.ts:10-45
ok REQ-002: src/user.ts:20-80
xx REQ-003: Missing trace
-> Fix: Add // REQ-003 comment
```

**Token impact:** -30-50% tokens

---

### --brainstorm (Discovery Mode)

**Purpose:** Switch to exploration mode, ask questions instead of providing solutions.

**When to use:**
- Vague requirements
- Exploring new features
- Understanding user needs
- Early planning stages

**Behavior:**
- Asks clarifying questions
- Presents multiple options
- Doesn't assume solutions
- Collaborative exploration

**Example:**
```
/f5-implement "improve performance" --brainstorm

# Output:
## Discovery Questions

1. Which parts are slow?
   - API responses?
   - Database queries?
   - Frontend rendering?

2. What metrics are you targeting?
   - Response time < Xms?
   - Throughput > Y req/s?

3. What constraints exist?
   - Budget for infrastructure?
   - Code freeze areas?

Please answer these before I propose solutions.
```

---

### --introspect (Transparency Mode)

**Purpose:** Show reasoning process and why decisions were made.

**When to use:**
- Learning how Claude thinks
- Debugging AI decisions
- Understanding trade-offs
- Building trust in suggestions

**Behavior:**
- Explains reasoning steps
- Shows alternatives considered
- Reveals assumptions made
- Highlights confidence levels

**Example:**
```
/f5-implement "caching layer" --introspect

# Output:
## Reasoning Process

### Step 1: Understand Requirements
- Need: Caching for API responses
- Assumption: Redis available (from config)

### Step 2: Consider Alternatives
| Option | Pros | Cons | Score |
|--------|------|------|-------|
| Redis | Fast, distributed | Extra infra | 8/10 |
| In-memory | Simple | Not distributed | 6/10 |
| File cache | Persistent | Slow | 4/10 |

### Step 3: Decision
Chose Redis because:
- Config shows Redis available
- Microservices architecture needs distributed cache
- Performance requirements suggest need for speed

Confidence: 85%
```

---

### --dry-run (Simulate Only)

**Purpose:** Simulate execution without making changes.

**When to use:**
- Testing command behavior
- Understanding impact
- CI/CD validation
- Training

**Behavior:**
- Shows what would happen
- No file modifications
- No external calls
- Safe exploration

**Example:**
```
/f5-strict-start requirements.md --dry-run

# Output:
## Dry Run: SIP Session Start

Would create:
- .f5/strict-session.json
- Checklist with 15 requirements

Would NOT:
- Actually create files
- Modify any existing files

Run without --dry-run to execute.
```

---

### --verbose (Detailed Output)

**Purpose:** Maximum detail in output.

**When to use:**
- Debugging issues
- Learning the framework
- Documentation purposes
- When --compress is too brief

**Behavior:**
- Full explanations
- All intermediate steps
- Complete file paths
- Extensive context

**Token impact:** +30-50% tokens

---

### --quiet (Minimal Output)

**Purpose:** Minimum necessary output only.

**When to use:**
- Scripting
- CI/CD pipelines
- When you know what to expect
- Batch operations

**Behavior:**
- Success/failure only
- No explanations
- Machine-readable where possible

**Example:**
```
/f5-strict-validate --quiet
# Output: PASS 92%
```

---

## Mode Combinations

### Recommended Combinations

| Scenario | Flags |
|----------|-------|
| Learning | `--introspect --verbose` |
| Production changes | `--safe-mode --think` |
| Quick validation | `--quiet --compress` |
| Architecture decision | `--think-hard --introspect` |
| Exploration | `--brainstorm` |
| CI/CD | `--quiet --dry-run` |

### Invalid Combinations

| Combination | Why Invalid |
|-------------|-------------|
| `--verbose --compress` | Contradictory |
| `--verbose --quiet` | Contradictory |
| `--brainstorm --quiet` | Brainstorm needs interaction |

---

## Default Behaviors

### By Command Type

| Command Type | Default Mode |
|--------------|--------------|
| `/f5-implement` | Normal |
| `/f5-strict-*` | `--safe-mode` implicit |
| `/f5-research` | `--think` implicit |
| `/f5-gate` | `--quiet` available |
| `/f5-doctor` | `--verbose` default |

### By Context

| Context | Auto-Applied Mode |
|---------|-------------------|
| Production branch | `--safe-mode` |
| > 80% context used | `--compress` |
| Security-related | `--think` |
| First time setup | `--verbose` |

---

## Implementation Notes

### For Claude Code

When processing flags:
1. Check for mode flags in $ARGUMENTS
2. Apply behavior modifications
3. Adjust output format
4. Track token usage if --compress

### Flag Priority

```
--safe-mode > --think-hard > --think > --compress > --quiet
```

Higher priority flags take precedence in conflicts.

---
*F5 Framework v2.0*
