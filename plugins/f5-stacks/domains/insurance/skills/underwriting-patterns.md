# Underwriting Patterns

## Overview
Design patterns cho insurance underwriting systems.

## Key Patterns

### Pattern 1: Rules Engine Architecture
**When to use:** Automated underwriting decisions
**Description:** Configurable rules engine for underwriting logic
**Example:**
```typescript
interface UnderwritingRule {
  id: string;
  name: string;
  product: string;
  state?: string;
  category: 'knockout' | 'referral' | 'rating' | 'conditional';
  priority: number;
  condition: RuleCondition;
  action: RuleAction;
  effectiveDate: Date;
  expirationDate?: Date;
  version: number;
}

interface RuleCondition {
  type: 'simple' | 'composite';
  field?: string;
  operator?: ComparisonOperator;
  value?: any;
  logicalOperator?: 'AND' | 'OR' | 'NOT';
  conditions?: RuleCondition[];
}

type ComparisonOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'greater_or_equal'
  | 'less_or_equal'
  | 'in'
  | 'not_in'
  | 'contains'
  | 'starts_with'
  | 'between'
  | 'is_null'
  | 'is_not_null';

interface RuleAction {
  type: 'decline' | 'refer' | 'approve' | 'rate_adjustment' | 'add_condition' | 'add_exclusion';
  parameters: Record<string, any>;
  message?: string;
}

class RulesEngine {
  private rules: Map<string, UnderwritingRule[]> = new Map();

  async loadRules(product: string, state?: string): Promise<void> {
    const key = `${product}:${state || 'default'}`;
    const rules = await this.ruleRepository.findByProductState(product, state);
    this.rules.set(key, rules.sort((a, b) => a.priority - b.priority));
  }

  evaluate(submission: UnderwritingSubmission): RuleEvaluationResult {
    const results: RuleResult[] = [];
    const rules = this.getRulesForSubmission(submission);

    for (const rule of rules) {
      const matches = this.evaluateCondition(rule.condition, submission);

      if (matches) {
        results.push({
          ruleId: rule.id,
          ruleName: rule.name,
          matched: true,
          action: rule.action
        });

        // Stop on knockout rules
        if (rule.category === 'knockout') {
          return { decision: 'decline', results, stoppedAt: rule.id };
        }
      }
    }

    return this.determineDecision(results);
  }

  private evaluateCondition(condition: RuleCondition, data: any): boolean {
    if (condition.type === 'simple') {
      const fieldValue = this.getFieldValue(data, condition.field!);
      return this.compare(fieldValue, condition.operator!, condition.value);
    }

    // Composite condition
    const childResults = condition.conditions!.map(c =>
      this.evaluateCondition(c, data)
    );

    switch (condition.logicalOperator) {
      case 'AND': return childResults.every(r => r);
      case 'OR': return childResults.some(r => r);
      case 'NOT': return !childResults[0];
      default: return false;
    }
  }
}
```

### Pattern 2: Risk Scoring Model
**When to use:** Quantitative risk assessment
**Description:** Weighted scoring model for risk classification
**Example:**
```typescript
interface RiskScoringModel {
  id: string;
  name: string;
  product: string;
  version: string;
  factors: RiskFactor[];
  classificationThresholds: ClassificationThreshold[];
}

interface RiskFactor {
  id: string;
  name: string;
  weight: number;
  dataField: string;
  scoringFunction: string;
  range: { min: number; max: number };
  nullHandling: 'average' | 'worst' | 'best' | 'exclude';
}

interface ClassificationThreshold {
  className: string;
  minScore: number;
  maxScore: number;
  tierCode: string;
}

class RiskScoringService {
  async scoreSubmission(
    submission: UnderwritingSubmission,
    model: RiskScoringModel
  ): Promise<RiskScore> {
    const factorScores: FactorScore[] = [];
    let totalWeight = 0;
    let weightedSum = 0;

    for (const factor of model.factors) {
      const rawValue = this.extractValue(submission, factor.dataField);
      const normalizedScore = await this.calculateFactorScore(factor, rawValue);

      factorScores.push({
        factorId: factor.id,
        factorName: factor.name,
        rawValue,
        normalizedScore,
        weightedScore: normalizedScore * factor.weight,
        weight: factor.weight
      });

      if (normalizedScore !== null) {
        weightedSum += normalizedScore * factor.weight;
        totalWeight += factor.weight;
      }
    }

    const compositeScore = totalWeight > 0 ? weightedSum / totalWeight : 0;
    const classification = this.classifyScore(compositeScore, model.classificationThresholds);

    return {
      modelId: model.id,
      modelVersion: model.version,
      compositeScore,
      factorScores,
      classification,
      confidence: this.calculateConfidence(factorScores, totalWeight),
      calculatedAt: new Date()
    };
  }

  private async calculateFactorScore(
    factor: RiskFactor,
    value: any
  ): Promise<number | null> {
    if (value === null || value === undefined) {
      switch (factor.nullHandling) {
        case 'average': return (factor.range.min + factor.range.max) / 2;
        case 'worst': return factor.range.min;
        case 'best': return factor.range.max;
        case 'exclude': return null;
      }
    }

    // Apply scoring function
    const scoringFn = this.getScoringFunction(factor.scoringFunction);
    return scoringFn(value, factor);
  }
}
```

### Pattern 3: Straight-Through Processing
**When to use:** High-volume, low-risk submissions
**Description:** Automated approval without manual review
**Example:**
```typescript
interface STPCriteria {
  product: string;
  maxPremium: Money;
  requiredDataFields: string[];
  knockoutRules: string[];
  riskScoreRange: { min: number; max: number };
  externalDataRequired: string[];
}

class STPProcessor {
  async processSTP(submission: UnderwritingSubmission): Promise<STPResult> {
    const criteria = await this.getCriteria(submission.product);
    const checks: STPCheck[] = [];

    // Check 1: Data completeness
    const completenessCheck = this.checkDataCompleteness(submission, criteria);
    checks.push(completenessCheck);
    if (!completenessCheck.passed) {
      return this.createResult('refer', checks, 'Incomplete data');
    }

    // Check 2: Premium threshold
    const premiumCheck = this.checkPremiumThreshold(submission, criteria);
    checks.push(premiumCheck);
    if (!premiumCheck.passed) {
      return this.createResult('refer', checks, 'Premium exceeds STP limit');
    }

    // Check 3: Knockout rules
    const knockoutCheck = await this.checkKnockoutRules(submission, criteria);
    checks.push(knockoutCheck);
    if (!knockoutCheck.passed) {
      return this.createResult('decline', checks, knockoutCheck.reason);
    }

    // Check 4: External data verification
    const externalCheck = await this.checkExternalData(submission, criteria);
    checks.push(externalCheck);
    if (!externalCheck.passed) {
      return this.createResult('refer', checks, 'External data verification failed');
    }

    // Check 5: Risk score
    const riskScore = await this.scoringService.scoreSubmission(submission);
    const riskCheck = this.checkRiskScore(riskScore, criteria);
    checks.push(riskCheck);
    if (!riskCheck.passed) {
      return this.createResult('refer', checks, 'Risk score outside STP range');
    }

    // All checks passed - approve via STP
    return this.createResult('approve', checks, 'STP approval', riskScore);
  }

  private createResult(
    decision: 'approve' | 'refer' | 'decline',
    checks: STPCheck[],
    reason: string,
    riskScore?: RiskScore
  ): STPResult {
    return {
      decision,
      stpEligible: decision === 'approve',
      checks,
      reason,
      riskScore,
      processedAt: new Date(),
      processType: decision === 'approve' ? 'stp' : 'manual'
    };
  }
}
```

### Pattern 4: Referral Workflow
**When to use:** Manual underwriter review required
**Description:** Structured workflow for referred submissions
**Example:**
```typescript
interface ReferralWorkflow {
  submissionId: string;
  referralReasons: string[];
  assignedTo?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  sla: {
    targetDate: Date;
    escalationDate: Date;
  };
  status: ReferralStatus;
  activities: WorkflowActivity[];
}

type ReferralStatus =
  | 'pending_assignment'
  | 'assigned'
  | 'in_review'
  | 'pending_info'
  | 'pending_approval'
  | 'completed';

class ReferralService {
  async createReferral(
    submission: UnderwritingSubmission,
    reasons: string[],
    stpResult: STPResult
  ): Promise<ReferralWorkflow> {
    const priority = this.calculatePriority(submission, reasons);
    const sla = this.calculateSLA(priority);
    const underwriter = await this.assignUnderwriter(submission, priority);

    const referral: ReferralWorkflow = {
      submissionId: submission.id,
      referralReasons: reasons,
      assignedTo: underwriter?.id,
      priority,
      sla,
      status: underwriter ? 'assigned' : 'pending_assignment',
      activities: [{
        type: 'created',
        timestamp: new Date(),
        description: 'Referral created from STP process',
        data: { reasons, stpResult }
      }]
    };

    await this.referralRepository.create(referral);
    await this.notifyUnderwriter(underwriter, referral);

    return referral;
  }

  async assignUnderwriter(
    submission: UnderwritingSubmission,
    priority: string
  ): Promise<Underwriter | null> {
    // Find available underwriter based on:
    // 1. Workload
    // 2. Expertise (product, risk type)
    // 3. Authority level
    // 4. Availability

    const candidates = await this.findQualifiedUnderwriters(submission);
    return this.selectBestCandidate(candidates, priority);
  }
}
```

## Best Practices
- Version all rules with effective dates
- Audit trail for all underwriting decisions
- Separate business rules from code
- Cache external data with appropriate TTL
- Monitor STP rates and quality

## Anti-Patterns to Avoid
- Hard-coding business rules
- Ignoring data quality issues
- No audit trail for decisions
- Over-reliance on single data source
