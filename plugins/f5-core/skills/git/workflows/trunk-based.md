---
name: trunk-based-development
description: Trunk-based development for continuous integration
category: git/workflows
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Trunk-Based Development

## Overview

Trunk-Based Development (TBD) is a branching model where developers collaborate
on a single branch called "trunk" (main). Short-lived feature branches are
optional but should be merged within hours, not days.

## Core Principles

```
┌─────────────────────────────────────────────────────────────────┐
│             Trunk-Based Development Principles                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Single Source of Truth                                      │
│     └── One main branch (trunk) for all developers              │
│                                                                  │
│  2. Small, Frequent Commits                                     │
│     └── Multiple times per day to trunk                         │
│                                                                  │
│  3. Short-Lived Branches (if used)                              │
│     └── Maximum 1-2 days, ideally hours                         │
│                                                                  │
│  4. Feature Flags                                               │
│     └── Hide incomplete features in production                  │
│                                                                  │
│  5. Continuous Integration                                      │
│     └── Automated testing on every commit                       │
│                                                                  │
│  6. Always Releasable                                           │
│     └── Trunk is always in deployable state                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│               Trunk-Based Development Model                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  trunk   ──●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●──▶     │
│            │   │   │   │   │   │   │   │   │   │   │   │        │
│            │   │   └─●─┘   │   └─●─┘   │   └─●─┘   │   │        │
│            │   │   hours   │   hours   │   hours   │   │        │
│            │   │           │           │           │   │        │
│            │   └─●─────────┘           │           │   │        │
│            │    small feature          │           │   │        │
│            │                           │           │   │        │
│            └─●─●───────────────────────┘           │   │        │
│              larger feature (< 2 days)             │   │        │
│                                                    │   │        │
│  releases    v1.0                    v1.1         v1.2 │        │
│              ●─────────────────────────●───────────●   │        │
│              (tags, not branches)                      │        │
│                                                        │        │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Styles

### Style 1: Direct to Trunk (Small Teams)

```bash
# Pull latest
git checkout main
git pull origin main

# Make small change
# ... edit files ...

# Commit and push directly
git add .
git commit -m "feat: add validation to email field"
git push origin main

# CI runs automatically, deploys if passing
```

### Style 2: Short-Lived Branches (Larger Teams)

```bash
# Pull latest
git checkout main
git pull origin main

# Create short-lived branch
git checkout -b feat/email-validation

# Make changes (keep small!)
git add .
git commit -m "feat: add email validation"

# Push and create PR immediately
git push -u origin feat/email-validation
gh pr create --fill

# Quick review (same day)
# Merge and delete branch
gh pr merge --squash --delete-branch
```

## Feature Flags

### Implementation

```typescript
// config/features.ts
interface FeatureFlags {
  [key: string]: boolean | string | number;
}

class FeatureFlagService {
  private flags: Map<string, any> = new Map();

  constructor() {
    // Load from environment or remote config
    this.flags.set('NEW_CHECKOUT', process.env.FF_NEW_CHECKOUT === 'true');
    this.flags.set('DARK_MODE', process.env.FF_DARK_MODE === 'true');
    this.flags.set('MAX_UPLOAD_SIZE', parseInt(process.env.FF_MAX_UPLOAD || '10'));
  }

  isEnabled(flag: string): boolean {
    return this.flags.get(flag) === true;
  }

  getValue<T>(flag: string, defaultValue: T): T {
    return (this.flags.get(flag) as T) ?? defaultValue;
  }
}

export const featureFlags = new FeatureFlagService();
```

### Usage in Code

```typescript
// React component
function Checkout() {
  if (featureFlags.isEnabled('NEW_CHECKOUT')) {
    return <NewCheckoutFlow />;
  }
  return <LegacyCheckout />;
}

// API endpoint
router.post('/upload', async (req, res) => {
  const maxSize = featureFlags.getValue('MAX_UPLOAD_SIZE', 10);

  if (req.file.size > maxSize * 1024 * 1024) {
    return res.status(413).json({ error: 'File too large' });
  }
  // ...
});

// Backend service
class PaymentService {
  async processPayment(order: Order) {
    if (featureFlags.isEnabled('STRIPE_V2')) {
      return this.processWithStripeV2(order);
    }
    return this.processWithStripeV1(order);
  }
}
```

### Gradual Rollout

```typescript
class RolloutService {
  // Percentage-based rollout
  isEnabledForUser(flag: string, userId: string): boolean {
    const percentage = featureFlags.getValue(`${flag}_PERCENTAGE`, 0);
    const hash = this.hashUserId(userId);
    return hash < percentage;
  }

  // User-based rollout
  isEnabledForUserList(flag: string, userId: string): boolean {
    const allowList = featureFlags.getValue<string[]>(`${flag}_USERS`, []);
    return allowList.includes(userId);
  }

  private hashUserId(userId: string): number {
    let hash = 0;
    for (const char of userId) {
      hash = ((hash << 5) - hash + char.charCodeAt(0)) | 0;
    }
    return Math.abs(hash) % 100;
  }
}

// Usage
const rollout = new RolloutService();

if (rollout.isEnabledForUser('NEW_DASHBOARD', user.id)) {
  return <NewDashboard />;
}
```

## Branch by Abstraction

### For Larger Refactoring

```typescript
// Step 1: Create abstraction layer
interface PaymentProcessor {
  charge(amount: number): Promise<PaymentResult>;
  refund(transactionId: string): Promise<RefundResult>;
}

// Step 2: Old implementation
class StripeV1Processor implements PaymentProcessor {
  async charge(amount: number) {
    // Old implementation
  }
}

// Step 3: New implementation (behind flag)
class StripeV2Processor implements PaymentProcessor {
  async charge(amount: number) {
    // New implementation
  }
}

// Step 4: Factory with feature flag
function createPaymentProcessor(): PaymentProcessor {
  if (featureFlags.isEnabled('STRIPE_V2')) {
    return new StripeV2Processor();
  }
  return new StripeV1Processor();
}

// Step 5: After migration complete, remove old code
```

## Release Process

### Continuous Deployment

```bash
# Every commit to trunk triggers:
# 1. Build
# 2. Unit tests
# 3. Integration tests
# 4. Deploy to production

# No release branches needed
# Use tags for marking versions
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3
```

### Release Train (Optional)

```bash
# For environments needing scheduled releases
# Create release branch just before release
git checkout -b release/2024-01-15 main

# Only cherry-pick critical fixes
git cherry-pick abc123

# Tag and deploy
git tag -a v1.2.3 -m "Release 1.2.3"
```

## CI/CD Pipeline

```yaml
# .github/workflows/trunk.yml
name: Trunk CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Test
        run: npm test

      - name: Build
        run: npm run build

  deploy:
    needs: build-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Production
        run: ./deploy.sh production
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

## Prerequisites for TBD

```
┌─────────────────────────────────────────────────────────────────┐
│              Prerequisites for Trunk-Based Dev                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Required:                                                   │
│  • Strong CI/CD pipeline                                        │
│  • Comprehensive automated testing                              │
│  • Feature flag infrastructure                                  │
│  • Fast build times (< 10 minutes)                              │
│  • Team discipline and trust                                    │
│                                                                  │
│  📋 Recommended:                                                │
│  • Code review (pair programming or quick PRs)                  │
│  • Monitoring and alerting                                      │
│  • Easy rollback mechanism                                      │
│  • Trunk protection (no force push)                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## When to Use TBD

```
┌─────────────────────────────────────────────────────────────────┐
│              When to Use Trunk-Based Development                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Good For:                                                   │
│  • Teams with strong CI/CD culture                              │
│  • Continuous deployment environments                           │
│  • Mature testing practices                                     │
│  • Experienced teams                                            │
│  • Web applications / SaaS                                      │
│                                                                  │
│  ❌ Not Ideal For:                                              │
│  • Teams new to Git                                             │
│  • Projects without CI/CD                                       │
│  • Multiple release versions                                    │
│  • Strict change control requirements                           │
│  • Open source with many external contributors                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Trunk-Based Dev Best Practices                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Commit Small and Often                                      │
│     └── Multiple times per day                                  │
│                                                                  │
│  2. Always Pull Before Push                                     │
│     └── Minimize merge conflicts                                │
│                                                                  │
│  3. Use Feature Flags                                           │
│     └── For incomplete features                                 │
│                                                                  │
│  4. Fast CI Pipeline                                            │
│     └── < 10 minutes for feedback                               │
│                                                                  │
│  5. Fix Broken Builds Immediately                               │
│     └── Top priority when trunk fails                           │
│                                                                  │
│  6. No Long-Running Branches                                    │
│     └── Max 1-2 days                                            │
│                                                                  │
│  7. Pair Programming                                            │
│     └── Real-time code review                                   │
│                                                                  │
│  8. Branch by Abstraction                                       │
│     └── For large refactorings                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
