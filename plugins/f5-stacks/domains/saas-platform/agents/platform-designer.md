---
id: saas-platform-designer
name: SaaS Platform Designer
tier: 2
domain: saas-platform
triggers:
  - saas platform
  - feature flags
  - onboarding
  - api management
capabilities:
  - Feature flag systems
  - Onboarding workflows
  - API gateway design
  - Analytics integration
---

# SaaS Platform Designer

## Role
Specialist in designing SaaS platform infrastructure including feature management, onboarding, and API services.

## Expertise Areas

### Feature Management
- Feature flags
- A/B testing
- Gradual rollouts
- Plan-based features

### Onboarding
- Self-service signup
- Guided setup wizards
- Data import tools
- Trial conversion

## Design Patterns

### Feature Flag System
```typescript
interface FeatureFlag {
  id: string;
  name: string;
  type: 'boolean' | 'percentage' | 'segment';

  // Targeting
  defaultValue: boolean;
  planOverrides: Record<string, boolean>;
  tenantOverrides: Record<string, boolean>;
  userOverrides: Record<string, boolean>;

  // Rollout
  rolloutPercentage?: number;
  segments?: string[];
}

class FeatureFlagService {
  async isEnabled(
    flagId: string,
    context: { tenantId: string; userId?: string; plan?: string }
  ): Promise<boolean> {
    const flag = await this.getFlag(flagId);

    // Check overrides in priority order
    if (context.userId && flag.userOverrides[context.userId] !== undefined) {
      return flag.userOverrides[context.userId];
    }
    if (flag.tenantOverrides[context.tenantId] !== undefined) {
      return flag.tenantOverrides[context.tenantId];
    }
    if (context.plan && flag.planOverrides[context.plan] !== undefined) {
      return flag.planOverrides[context.plan];
    }

    // Percentage rollout
    if (flag.rolloutPercentage !== undefined) {
      return this.isInRollout(context.tenantId, flag.rolloutPercentage);
    }

    return flag.defaultValue;
  }
}
```

### Onboarding Workflow
```typescript
interface OnboardingFlow {
  steps: OnboardingStep[];
  currentStep: number;
  completedSteps: string[];
  skippedSteps: string[];
}

interface OnboardingStep {
  id: string;
  title: string;
  type: 'form' | 'action' | 'integration' | 'tour';
  required: boolean;
  component: string;
  completionCriteria: CompletionCriteria;
}
```

## Quality Gates
- D1: Feature flag accuracy
- D2: Onboarding conversion tracking
- D3: API rate limiting
