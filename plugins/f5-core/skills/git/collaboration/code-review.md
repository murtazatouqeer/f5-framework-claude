---
name: code-review
description: Code review best practices and techniques
category: git/collaboration
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Code Review

## Overview

Code review is the process of examining code changes to find bugs, improve code
quality, share knowledge, and ensure consistency. Effective reviews improve
both the code and the team.

## Review Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    Code Review Process                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Author                          Reviewer                       │
│  ────────────────────────────────────────────────────────────   │
│  1. Create PR with context    │                                 │
│                               │  2. Understand the context      │
│                               │  3. Review code changes         │
│                               │  4. Leave constructive feedback │
│  5. Respond to feedback       │                                 │
│  6. Make necessary changes    │                                 │
│                               │  7. Re-review changes           │
│                               │  8. Approve when satisfied      │
│  9. Merge PR                  │                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## What to Review

### Code Quality Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│                  Code Review Checklist                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Functionality                                                  │
│  □ Does the code do what it's supposed to do?                   │
│  □ Are edge cases handled?                                      │
│  □ Is error handling appropriate?                               │
│                                                                  │
│  Design                                                         │
│  □ Is the code well-organized?                                  │
│  □ Does it follow project patterns?                             │
│  □ Is it at the right abstraction level?                        │
│  □ Is there unnecessary complexity?                             │
│                                                                  │
│  Readability                                                    │
│  □ Are names descriptive and consistent?                        │
│  □ Is the code self-documenting?                                │
│  □ Are comments helpful (not redundant)?                        │
│                                                                  │
│  Testing                                                        │
│  □ Are there adequate tests?                                    │
│  □ Do tests cover edge cases?                                   │
│  □ Are tests readable and maintainable?                         │
│                                                                  │
│  Security                                                       │
│  □ Is user input validated?                                     │
│  □ Are there SQL injection risks?                               │
│  □ Is sensitive data protected?                                 │
│  □ Are authentication/authorization correct?                    │
│                                                                  │
│  Performance                                                    │
│  □ Are there potential bottlenecks?                             │
│  □ Is database access efficient?                                │
│  □ Are there unnecessary computations?                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Code Smells to Watch For

```
┌─────────────────────────────────────────────────────────────────┐
│                    Common Code Smells                            │
├──────────────────────┬──────────────────────────────────────────┤
│ Smell                │ Indicator                                │
├──────────────────────┼──────────────────────────────────────────┤
│ Long functions       │ > 50 lines, multiple responsibilities   │
│ Large classes        │ > 300 lines, many methods               │
│ Deep nesting         │ > 3 levels of indentation               │
│ Magic numbers        │ Hard-coded values without explanation   │
│ Duplicate code       │ Same logic in multiple places           │
│ Complex conditions   │ Multiple && or || in one expression     │
│ Poor naming          │ Single letters, abbreviations           │
│ Dead code            │ Unreachable or commented-out code       │
│ Feature envy         │ Methods using other class's data        │
│ God classes          │ Classes that know/do too much           │
└──────────────────────┴──────────────────────────────────────────┘
```

## Giving Feedback

### Feedback Types

```typescript
// Blocking - Must be fixed before merge
// 🔴 "This introduces a SQL injection vulnerability.
//    Please use parameterized queries."

// Suggestion - Recommended improvement
// 🟡 "Consider using Array.map() here for cleaner code."

// Nitpick - Minor, optional
// 🟢 "Nit: Could rename to `isUserValid` for clarity."

// Question - Seeking understanding
// 💬 "Could you explain why we need this null check?"

// Praise - Positive reinforcement
// 👍 "Great approach to handling the edge case!"
```

### Feedback Examples

#### Good Feedback

```markdown
**🔴 Blocking:**
This query is vulnerable to SQL injection:
```sql
`SELECT * FROM users WHERE id = ${userId}`
```

Please use parameterized queries:
```sql
`SELECT * FROM users WHERE id = $1`, [userId]
```

---

**🟡 Suggestion:**
This could be simplified using optional chaining:
```typescript
// Before
const name = user && user.profile && user.profile.name;

// After
const name = user?.profile?.name;
```

---

**🟢 Nit:**
Consider using a more descriptive variable name:
```typescript
// Before
const d = new Date();

// After
const createdAt = new Date();
```

---

**💬 Question:**
I see we're caching this value. What's the expected invalidation strategy?
Is there a risk of stale data?

---

**👍 Praise:**
Nice use of the Strategy pattern here! It makes the code much more
extensible for future payment providers.
```

#### Bad Feedback (Avoid)

```markdown
❌ "This is wrong."
   → Why is it wrong? How to fix?

❌ "I would have done this differently."
   → What specifically? Is current approach wrong?

❌ "Why didn't you use X?"
   → Sounds accusatory. Try: "Have you considered X?"

❌ "..."
   → No context, confusing
```

### Commenting Conventions

```markdown
# Prefix conventions
🔴 or [blocking]: Must fix
🟡 or [suggestion]: Should consider
🟢 or [nit]: Minor, optional
💬 or [question]: Need clarification
👍 or [praise]: Positive feedback

# Example comments
🔴 Security: Input not validated. Please add sanitization.

🟡 Performance: This N+1 query could be optimized with eager loading.

🟢 Nit: Prefer `const` over `let` for this variable.

💬 Question: Why did we choose this approach over X?

👍 Great: Clean separation of concerns here!
```

## Receiving Feedback

### Best Practices for Authors

```
┌─────────────────────────────────────────────────────────────────┐
│               Responding to Review Feedback                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DO:                                                            │
│  • Assume positive intent                                       │
│  • Respond to every comment                                     │
│  • Explain reasoning if you disagree                            │
│  • Ask for clarification when unclear                           │
│  • Thank reviewers for their time                               │
│  • Learn from feedback                                          │
│                                                                  │
│  DON'T:                                                         │
│  • Take feedback personally                                     │
│  • Get defensive                                                │
│  • Ignore comments                                              │
│  • Just say "done" without context                              │
│  • Merge with unresolved comments                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Response Examples

```markdown
# Acknowledging valid feedback
"Good catch! Fixed in abc123."

# Disagreeing respectfully
"I considered that approach, but went with this because [reason].
Open to discussion if you feel strongly about it."

# Asking for clarification
"Could you elaborate on this? I'm not sure I understand the concern."

# Explaining context
"This looks unusual, but it's needed because [reason]. Added a comment
to explain."

# Deferring to future work
"Agreed this could be better. Created issue #456 to address this in a
follow-up PR to keep this one focused."
```

## Review Efficiency

### Reviewer Guidelines

```
┌─────────────────────────────────────────────────────────────────┐
│                 Efficient Code Review                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Time Management:                                               │
│  • Review within 24 hours of request                            │
│  • Spend 30-60 minutes max per review                           │
│  • Take breaks for large PRs                                    │
│                                                                  │
│  Review Order:                                                  │
│  1. Read PR description and context                             │
│  2. Look at tests first (understand intent)                     │
│  3. Review main logic changes                                   │
│  4. Check edge cases and error handling                         │
│  5. Verify style and naming                                     │
│                                                                  │
│  Focus Areas by PR Size:                                        │
│  • Small (< 50 LOC): Detailed review                            │
│  • Medium (50-200 LOC): Focus on logic                          │
│  • Large (> 200 LOC): High-level + spot checks                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Review Tools

```bash
# GitHub CLI review commands
gh pr review 123                     # Interactive review
gh pr review 123 --approve           # Approve
gh pr review 123 --request-changes   # Request changes
gh pr review 123 --comment           # Comment only

# View changed files
gh pr diff 123

# Check PR locally
gh pr checkout 123

# Run tests on PR branch
gh pr checkout 123
npm test

# Compare with main
git diff main...HEAD
```

## Review Culture

### Building a Healthy Review Culture

```
┌─────────────────────────────────────────────────────────────────┐
│                 Healthy Review Culture                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Principles:                                                    │
│  • Reviews are about code, not people                           │
│  • Learning opportunity for everyone                            │
│  • Collaboration over gatekeeping                               │
│  • Timely feedback is respectful                                │
│                                                                  │
│  Team Agreements:                                               │
│  • Response time expectations (e.g., 24 hours)                  │
│  • Required approvals before merge                              │
│  • When to request specific reviewers                           │
│  • How to handle disagreements                                  │
│                                                                  │
│  Continuous Improvement:                                        │
│  • Share learnings from reviews                                 │
│  • Update guidelines based on patterns                          │
│  • Celebrate good practices                                     │
│  • Regular retros on review process                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Pair Programming Alternative

```
┌─────────────────────────────────────────────────────────────────┐
│                Pair vs Review Comparison                         │
├──────────────────┬──────────────────────────────────────────────┤
│ Code Review      │ Pair Programming                             │
├──────────────────┼──────────────────────────────────────────────┤
│ Asynchronous     │ Real-time                                    │
│ After completion │ During development                           │
│ Written feedback │ Verbal discussion                            │
│ Scales well      │ 2 people max                                 │
│ Context gap      │ Shared context                               │
├──────────────────┴──────────────────────────────────────────────┤
│                                                                  │
│ When to Pair Instead:                                           │
│ • Complex feature design                                        │
│ • Onboarding new team members                                   │
│ • Tricky debugging                                              │
│ • Knowledge sharing                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                 Code Review Best Practices                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  For Authors:                                                   │
│  • Write clear PR descriptions                                  │
│  • Keep PRs small and focused                                   │
│  • Self-review before requesting                                │
│  • Respond promptly to feedback                                 │
│  • Be open to suggestions                                       │
│                                                                  │
│  For Reviewers:                                                 │
│  • Review promptly (within 24 hours)                            │
│  • Be constructive and specific                                 │
│  • Distinguish blocking vs suggestions                          │
│  • Explain the "why" behind feedback                            │
│  • Acknowledge good code                                        │
│                                                                  │
│  For Teams:                                                     │
│  • Set clear expectations                                       │
│  • Rotate reviewers for knowledge sharing                       │
│  • Use automated tools for style checks                         │
│  • Review the review process periodically                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
