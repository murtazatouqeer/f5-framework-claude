# Claims Processing Patterns

## Overview
Design patterns cho insurance claims processing systems.

## Key Patterns

### Pattern 1: Claims Triage Engine
**When to use:** Initial claim assessment and routing
**Description:** Automated triage based on claim characteristics
**Example:**
```typescript
interface TriageEngine {
  assess(claim: Claim): Promise<TriageResult>;
  route(claim: Claim, result: TriageResult): Promise<Assignment>;
}

interface TriageResult {
  severity: ClaimSeverity;
  complexity: ClaimComplexity;
  handlerType: HandlerType;
  priority: ClaimPriority;
  fraudIndicators: FraudIndicator[];
  suggestedReserves: Reserves;
  specialHandling: string[];
}

type ClaimSeverity = 'minor' | 'moderate' | 'major' | 'catastrophic';
type ClaimComplexity = 'simple' | 'moderate' | 'complex';
type HandlerType = 'auto' | 'desk' | 'field' | 'complex' | 'siu' | 'litigation';

class ClaimsTriageEngine implements TriageEngine {
  async assess(claim: Claim): Promise<TriageResult> {
    const [
      severity,
      complexity,
      fraudScore,
      reserveEstimate
    ] = await Promise.all([
      this.assessSeverity(claim),
      this.assessComplexity(claim),
      this.assessFraudRisk(claim),
      this.estimateReserves(claim)
    ]);

    const handlerType = this.determineHandlerType(severity, complexity, fraudScore);
    const priority = this.calculatePriority(severity, claim);
    const fraudIndicators = this.identifyFraudIndicators(claim, fraudScore);

    return {
      severity,
      complexity,
      handlerType,
      priority,
      fraudIndicators,
      suggestedReserves: reserveEstimate,
      specialHandling: this.identifySpecialHandling(claim)
    };
  }

  private assessSeverity(claim: Claim): ClaimSeverity {
    const factors = {
      injuries: claim.loss.injuries,
      fatalities: claim.loss.fatalities,
      estimatedLoss: claim.loss.initialEstimate?.amount || 0,
      vehicleTotalLoss: claim.loss.vehicleTotalLoss,
      structureDamage: claim.loss.structureDamage
    };

    if (factors.fatalities || factors.estimatedLoss > 500000) {
      return 'catastrophic';
    }
    if (factors.injuries || factors.estimatedLoss > 100000) {
      return 'major';
    }
    if (factors.vehicleTotalLoss || factors.estimatedLoss > 25000) {
      return 'moderate';
    }
    return 'minor';
  }

  private determineHandlerType(
    severity: ClaimSeverity,
    complexity: ClaimComplexity,
    fraudScore: FraudScore
  ): HandlerType {
    // SIU referral for high fraud risk
    if (fraudScore.score > 0.7) return 'siu';

    // Litigation for severe injury claims
    if (severity === 'catastrophic') return 'litigation';

    // Field adjuster for complex property claims
    if (complexity === 'complex' && severity !== 'minor') return 'field';

    // Desk adjuster for moderate claims
    if (complexity === 'moderate' || severity === 'moderate') return 'desk';

    // Auto-adjudication for simple claims
    if (complexity === 'simple' && severity === 'minor') return 'auto';

    return 'desk';
  }
}
```

### Pattern 2: Reserve Management
**When to use:** Tracking and managing claim reserves
**Description:** Double-entry reserve system with audit trail
**Example:**
```typescript
interface ReserveTransaction {
  id: string;
  claimId: string;
  type: 'set' | 'increase' | 'decrease' | 'transfer';
  category: ReserveCategory;
  amount: Money;
  previousAmount: Money;
  newAmount: Money;
  reason: string;
  authorizedBy: string;
  createdAt: Date;
}

type ReserveCategory = 'indemnity' | 'expense' | 'subrogation';

class ReserveManager {
  async setInitialReserve(
    claimId: string,
    reserves: {
      indemnity: Money;
      expense: Money;
    },
    authorizedBy: string
  ): Promise<void> {
    const transactions: ReserveTransaction[] = [];

    if (reserves.indemnity.amount > 0) {
      transactions.push(this.createTransaction(
        claimId, 'set', 'indemnity',
        reserves.indemnity, { amount: 0 }, reserves.indemnity,
        'Initial reserve setting', authorizedBy
      ));
    }

    if (reserves.expense.amount > 0) {
      transactions.push(this.createTransaction(
        claimId, 'set', 'expense',
        reserves.expense, { amount: 0 }, reserves.expense,
        'Initial reserve setting', authorizedBy
      ));
    }

    await this.recordTransactions(transactions);
    await this.updateClaimReserves(claimId);
  }

  async adjustReserve(
    claimId: string,
    category: ReserveCategory,
    newAmount: Money,
    reason: string,
    authorizedBy: string
  ): Promise<void> {
    const currentReserve = await this.getCurrentReserve(claimId, category);
    const difference = newAmount.amount - currentReserve.amount;

    // Check authorization level
    await this.checkAuthorization(authorizedBy, Math.abs(difference));

    const type = difference > 0 ? 'increase' : 'decrease';

    const transaction = this.createTransaction(
      claimId, type, category,
      { amount: Math.abs(difference), currency: newAmount.currency },
      currentReserve, newAmount,
      reason, authorizedBy
    );

    await this.recordTransaction(transaction);
    await this.updateClaimReserves(claimId);

    // Notify if significant change
    if (Math.abs(difference) > this.significantChangeThreshold) {
      await this.notifyReserveChange(claimId, transaction);
    }
  }

  async getReserveHistory(claimId: string): Promise<ReserveTransaction[]> {
    return this.transactionRepository.findByClaimId(claimId);
  }

  async getReserveSummary(claimId: string): Promise<ReserveSummary> {
    const transactions = await this.getReserveHistory(claimId);
    const payments = await this.paymentService.getPayments(claimId);
    const recoveries = await this.recoveryService.getRecoveries(claimId);

    return {
      reserves: await this.getCurrentReserves(claimId),
      totalPaid: this.sumPayments(payments),
      totalRecovered: this.sumRecoveries(recoveries),
      incurred: this.calculateIncurred(transactions, payments, recoveries),
      outstanding: this.calculateOutstanding(transactions, payments)
    };
  }
}
```

### Pattern 3: Claims Adjudication Workflow
**When to use:** Structured claim evaluation process
**Description:** Step-by-step adjudication with decision support
**Example:**
```typescript
interface AdjudicationWorkflow {
  claimId: string;
  status: AdjudicationStatus;
  steps: AdjudicationStep[];
  currentStep: number;
  decisions: AdjudicationDecision[];
  assignedTo: string;
}

type AdjudicationStatus =
  | 'in_progress'
  | 'pending_info'
  | 'pending_review'
  | 'completed';

interface AdjudicationStep {
  id: string;
  name: string;
  type: StepType;
  status: 'pending' | 'in_progress' | 'completed' | 'skipped';
  requiredInputs: string[];
  outputs?: Record<string, any>;
  completedAt?: Date;
  completedBy?: string;
}

type StepType =
  | 'coverage_verification'
  | 'liability_assessment'
  | 'damage_evaluation'
  | 'settlement_calculation'
  | 'supervisor_review'
  | 'payment_approval';

class AdjudicationService {
  async createWorkflow(claimId: string): Promise<AdjudicationWorkflow> {
    const claim = await this.claimService.getClaim(claimId);
    const steps = this.buildSteps(claim);

    const workflow: AdjudicationWorkflow = {
      claimId,
      status: 'in_progress',
      steps,
      currentStep: 0,
      decisions: [],
      assignedTo: claim.assignment.adjuster.id
    };

    return this.workflowRepository.create(workflow);
  }

  private buildSteps(claim: Claim): AdjudicationStep[] {
    const steps: AdjudicationStep[] = [
      {
        id: 'coverage',
        name: 'Coverage Verification',
        type: 'coverage_verification',
        status: 'pending',
        requiredInputs: ['policy', 'loss_date', 'cause_of_loss']
      },
      {
        id: 'liability',
        name: 'Liability Assessment',
        type: 'liability_assessment',
        status: 'pending',
        requiredInputs: ['investigation_report', 'statements']
      },
      {
        id: 'damages',
        name: 'Damage Evaluation',
        type: 'damage_evaluation',
        status: 'pending',
        requiredInputs: ['inspection_report', 'estimates']
      },
      {
        id: 'settlement',
        name: 'Settlement Calculation',
        type: 'settlement_calculation',
        status: 'pending',
        requiredInputs: ['coverage_decision', 'damage_assessment']
      }
    ];

    // Add supervisor review if needed
    if (this.requiresSupervisorReview(claim)) {
      steps.push({
        id: 'supervisor',
        name: 'Supervisor Review',
        type: 'supervisor_review',
        status: 'pending',
        requiredInputs: ['settlement_calculation']
      });
    }

    steps.push({
      id: 'payment',
      name: 'Payment Approval',
      type: 'payment_approval',
      status: 'pending',
      requiredInputs: ['final_settlement']
    });

    return steps;
  }

  async completeStep(
    workflowId: string,
    stepId: string,
    output: Record<string, any>,
    adjuster: string
  ): Promise<AdjudicationWorkflow> {
    const workflow = await this.workflowRepository.findById(workflowId);
    const stepIndex = workflow.steps.findIndex(s => s.id === stepId);
    const step = workflow.steps[stepIndex];

    // Validate required inputs
    this.validateInputs(step, output);

    // Update step
    step.status = 'completed';
    step.outputs = output;
    step.completedAt = new Date();
    step.completedBy = adjuster;

    // Move to next step
    if (stepIndex < workflow.steps.length - 1) {
      workflow.currentStep = stepIndex + 1;
      workflow.steps[stepIndex + 1].status = 'in_progress';
    } else {
      workflow.status = 'completed';
    }

    // Record decision if applicable
    if (output.decision) {
      workflow.decisions.push({
        stepId,
        decision: output.decision,
        reason: output.reason,
        decidedAt: new Date(),
        decidedBy: adjuster
      });
    }

    return this.workflowRepository.update(workflow);
  }
}
```

### Pattern 4: Fraud Detection Integration
**When to use:** Identifying potentially fraudulent claims
**Description:** Multi-factor fraud scoring and SIU referral
**Example:**
```typescript
interface FraudDetectionService {
  scoreClaim(claim: Claim): Promise<FraudScore>;
  identifyIndicators(claim: Claim): Promise<FraudIndicator[]>;
  referToSIU(claimId: string, score: FraudScore): Promise<SIUReferral>;
}

interface FraudScore {
  score: number; // 0-1
  confidence: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  factors: FraudFactor[];
  modelVersion: string;
  scoredAt: Date;
}

interface FraudIndicator {
  code: string;
  name: string;
  severity: 'info' | 'warning' | 'alert';
  description: string;
  evidence?: string;
}

class FraudDetectionEngine implements FraudDetectionService {
  private readonly RED_FLAGS = [
    { code: 'RF001', name: 'Recent Policy', check: (c: Claim) => this.isRecentPolicy(c) },
    { code: 'RF002', name: 'Premium Payment Issues', check: (c: Claim) => this.hasPremiumIssues(c) },
    { code: 'RF003', name: 'Prior Claims History', check: (c: Claim) => this.hasHighClaimsHistory(c) },
    { code: 'RF004', name: 'Inconsistent Statements', check: (c: Claim) => this.hasInconsistentStatements(c) },
    { code: 'RF005', name: 'Delayed Reporting', check: (c: Claim) => this.isDelayedReport(c) },
    { code: 'RF006', name: 'Suspicious Loss Location', check: (c: Claim) => this.isSuspiciousLocation(c) },
    { code: 'RF007', name: 'Attorney Involvement Early', check: (c: Claim) => this.hasEarlyAttorney(c) },
    { code: 'RF008', name: 'Staged Accident Patterns', check: (c: Claim) => this.matchesStagedPatterns(c) }
  ];

  async scoreClaim(claim: Claim): Promise<FraudScore> {
    const indicators = await this.identifyIndicators(claim);
    const externalScore = await this.getExternalFraudScore(claim);
    const networkAnalysis = await this.analyzeClaimantNetwork(claim);

    // Combine scores
    const internalScore = this.calculateInternalScore(indicators);
    const combinedScore = this.combineScores(internalScore, externalScore, networkAnalysis);

    return {
      score: combinedScore,
      confidence: this.calculateConfidence(indicators.length, externalScore),
      riskLevel: this.classifyRisk(combinedScore),
      factors: this.extractFactors(indicators, externalScore, networkAnalysis),
      modelVersion: 'fraud-model-v2.1',
      scoredAt: new Date()
    };
  }

  async identifyIndicators(claim: Claim): Promise<FraudIndicator[]> {
    const indicators: FraudIndicator[] = [];

    for (const redFlag of this.RED_FLAGS) {
      const result = await redFlag.check(claim);
      if (result.triggered) {
        indicators.push({
          code: redFlag.code,
          name: redFlag.name,
          severity: result.severity,
          description: result.description,
          evidence: result.evidence
        });
      }
    }

    return indicators;
  }

  async referToSIU(claimId: string, score: FraudScore): Promise<SIUReferral> {
    const claim = await this.claimService.getClaim(claimId);

    const referral: SIUReferral = {
      claimId,
      claimNumber: claim.claimNumber,
      referralDate: new Date(),
      fraudScore: score,
      indicators: await this.identifyIndicators(claim),
      priority: this.determinePriority(score),
      status: 'pending',
      assignedTo: null
    };

    await this.siuRepository.create(referral);
    await this.notifySIU(referral);
    await this.claimService.updateStatus(claimId, 'siu_review');

    return referral;
  }
}
```

## Best Practices
- Automate triage for consistent routing
- Use double-entry for reserve tracking
- Implement fraud scoring early in process
- Maintain comprehensive audit trails
- Set appropriate reserve review thresholds

## Anti-Patterns to Avoid
- Manual reserve tracking without audit
- Skipping fraud checks for speed
- No SLA monitoring on workflows
- Inconsistent adjudication criteria
