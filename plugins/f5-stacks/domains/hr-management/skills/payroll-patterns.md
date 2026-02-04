# Payroll Processing Patterns

## Overview
Design patterns cho payroll processing systems.

## Key Patterns

### Pattern 1: Pay Calculation Pipeline
**When to use:** Processing payroll for multiple employees
**Description:** Pipeline pattern for systematic pay calculation
**Example:**
```typescript
interface PayrollPipeline {
  stages: PipelineStage[];
  execute(run: PayrollRun): Promise<PayrollResult>;
}

type PipelineStage =
  | 'validate'
  | 'calculate_gross'
  | 'calculate_pretax_deductions'
  | 'calculate_taxes'
  | 'calculate_posttax_deductions'
  | 'calculate_net'
  | 'validate_results'
  | 'generate_payments';

class PayrollProcessingPipeline implements PayrollPipeline {
  stages: PipelineStage[] = [
    'validate',
    'calculate_gross',
    'calculate_pretax_deductions',
    'calculate_taxes',
    'calculate_posttax_deductions',
    'calculate_net',
    'validate_results',
    'generate_payments'
  ];

  async execute(run: PayrollRun): Promise<PayrollResult> {
    const employees = await this.getEmployeesForRun(run);
    const results: PayCalculation[] = [];
    const errors: PayrollError[] = [];

    for (const employee of employees) {
      try {
        let calculation: Partial<PayCalculation> = {
          employeeId: employee.id,
          payPeriod: run.payPeriod
        };

        // Execute each stage
        for (const stage of this.stages) {
          calculation = await this.executeStage(stage, employee, calculation, run);
        }

        results.push(calculation as PayCalculation);
      } catch (error) {
        errors.push({
          employeeId: employee.id,
          stage: error.stage,
          message: error.message,
          severity: error.severity || 'error'
        });
      }
    }

    return {
      runId: run.id,
      successful: results,
      failed: errors,
      totals: this.calculateTotals(results)
    };
  }

  private async executeStage(
    stage: PipelineStage,
    employee: Employee,
    calculation: Partial<PayCalculation>,
    run: PayrollRun
  ): Promise<Partial<PayCalculation>> {
    switch (stage) {
      case 'validate':
        await this.validateEmployee(employee, run);
        return calculation;

      case 'calculate_gross':
        const timeData = await this.getTimeData(employee.id, run.payPeriod);
        const grossPay = await this.calculateGrossPay(employee, timeData, run);
        return { ...calculation, grossPay };

      case 'calculate_pretax_deductions':
        const preTax = await this.calculatePreTaxDeductions(
          employee, calculation.grossPay!
        );
        const taxableIncome = calculation.grossPay!.total - preTax.total;
        return { ...calculation, preTaxDeductions: preTax, taxableIncome };

      case 'calculate_taxes':
        const taxes = await this.calculateTaxes(
          employee, calculation.taxableIncome!, run.payPeriod
        );
        return { ...calculation, taxes };

      case 'calculate_posttax_deductions':
        const postTax = await this.calculatePostTaxDeductions(
          employee, calculation.taxableIncome!
        );
        return { ...calculation, postTaxDeductions: postTax };

      case 'calculate_net':
        const netPay = calculation.taxableIncome! -
                       calculation.taxes!.total -
                       calculation.postTaxDeductions!.total;
        return { ...calculation, netPay };

      case 'validate_results':
        await this.validateCalculation(calculation);
        return calculation;

      case 'generate_payments':
        const payments = await this.generatePayments(employee, calculation);
        return { ...calculation, payments };

      default:
        return calculation;
    }
  }
}
```

### Pattern 2: Tax Withholding Calculator
**When to use:** Calculating federal, state, and local tax withholding
**Description:** Strategy pattern for different tax jurisdictions
**Example:**
```typescript
interface TaxCalculator {
  calculate(
    taxableIncome: number,
    employeeInfo: TaxEmployeeInfo,
    period: PayPeriod
  ): Promise<TaxWithholding>;
}

interface TaxEmployeeInfo {
  filingStatus: string;
  allowances: number;
  additionalWithholding: number;
  exempt: boolean;
  ytdWages: number;
  ytdTaxWithheld: number;
}

class FederalTaxCalculator implements TaxCalculator {
  private readonly TAX_TABLES_2024 = {
    single: [
      { min: 0, max: 11600, rate: 0.10, base: 0 },
      { min: 11600, max: 47150, rate: 0.12, base: 1160 },
      { min: 47150, max: 100525, rate: 0.22, base: 5426 },
      { min: 100525, max: 191950, rate: 0.24, base: 17168.50 },
      { min: 191950, max: 243725, rate: 0.32, base: 39110.50 },
      { min: 243725, max: 609350, rate: 0.35, base: 55678.50 },
      { min: 609350, max: Infinity, rate: 0.37, base: 183647.25 }
    ],
    married_filing_jointly: [
      { min: 0, max: 23200, rate: 0.10, base: 0 },
      { min: 23200, max: 94300, rate: 0.12, base: 2320 },
      // ... more brackets
    ]
  };

  async calculate(
    taxableIncome: number,
    employeeInfo: TaxEmployeeInfo,
    period: PayPeriod
  ): Promise<TaxWithholding> {
    if (employeeInfo.exempt) {
      return { amount: 0, breakdown: { regular: 0 } };
    }

    // Annualize income
    const periodsPerYear = this.getPeriodsPerYear(period.frequency);
    const annualizedIncome = taxableIncome * periodsPerYear;

    // Apply standard deduction
    const standardDeduction = this.getStandardDeduction(employeeInfo.filingStatus);
    const adjustedIncome = Math.max(0, annualizedIncome - standardDeduction);

    // Calculate annual tax
    const taxBrackets = this.TAX_TABLES_2024[employeeInfo.filingStatus] ||
                        this.TAX_TABLES_2024.single;
    const annualTax = this.calculateFromBrackets(adjustedIncome, taxBrackets);

    // Convert to per-period withholding
    let periodWithholding = annualTax / periodsPerYear;

    // Add additional withholding
    periodWithholding += employeeInfo.additionalWithholding;

    return {
      amount: Math.round(periodWithholding * 100) / 100,
      breakdown: {
        regular: annualTax / periodsPerYear,
        additional: employeeInfo.additionalWithholding
      },
      annualProjection: annualTax
    };
  }

  private calculateFromBrackets(income: number, brackets: TaxBracket[]): number {
    for (const bracket of brackets) {
      if (income <= bracket.max) {
        return bracket.base + (income - bracket.min) * bracket.rate;
      }
    }
    const lastBracket = brackets[brackets.length - 1];
    return lastBracket.base + (income - lastBracket.min) * lastBracket.rate;
  }
}

class StateTaxCalculatorFactory {
  private calculators: Map<string, TaxCalculator> = new Map();

  getCalculator(stateCode: string): TaxCalculator {
    if (!this.calculators.has(stateCode)) {
      this.calculators.set(stateCode, this.createCalculator(stateCode));
    }
    return this.calculators.get(stateCode)!;
  }

  private createCalculator(stateCode: string): TaxCalculator {
    // States with no income tax
    const noTaxStates = ['TX', 'FL', 'WA', 'NV', 'SD', 'WY', 'AK', 'TN', 'NH'];
    if (noTaxStates.includes(stateCode)) {
      return new NoTaxCalculator();
    }

    // Flat tax states
    const flatTaxStates: Record<string, number> = {
      'IL': 0.0495,
      'PA': 0.0307,
      'MI': 0.0425,
      'IN': 0.0315,
      // ... more flat tax states
    };
    if (flatTaxStates[stateCode]) {
      return new FlatRateTaxCalculator(flatTaxStates[stateCode]);
    }

    // Progressive tax states
    return new ProgressiveStateTaxCalculator(stateCode);
  }
}
```

### Pattern 3: Deduction Processing
**When to use:** Managing various payroll deductions
**Description:** Strategy pattern for different deduction types
**Example:**
```typescript
interface DeductionProcessor {
  process(
    employee: Employee,
    grossPay: Money,
    ytdDeductions: YTDDeductions
  ): Promise<ProcessedDeduction>;
}

interface ProcessedDeduction {
  deductionId: string;
  type: DeductionType;
  amount: number;
  ytdTotal: number;
  maxReached: boolean;
}

class DeductionEngine {
  private processors: Map<DeductionType, DeductionProcessor> = new Map();

  constructor() {
    this.processors.set('401k', new Retirement401kProcessor());
    this.processors.set('health_insurance', new HealthInsuranceProcessor());
    this.processors.set('hsa', new HSAProcessor());
    this.processors.set('fsa', new FSAProcessor());
    this.processors.set('garnishment', new GarnishmentProcessor());
  }

  async processDeductions(
    employee: Employee,
    grossPay: Money,
    category: 'pre_tax' | 'post_tax'
  ): Promise<DeductionSummary> {
    const deductions = employee.deductions.filter(d =>
      (category === 'pre_tax' && d.preTax) ||
      (category === 'post_tax' && !d.preTax)
    );

    const ytdDeductions = await this.getYTDDeductions(employee.id);
    const processed: ProcessedDeduction[] = [];

    for (const deduction of deductions) {
      const processor = this.processors.get(deduction.type);
      if (!processor) continue;

      const result = await processor.process(employee, grossPay, ytdDeductions);
      processed.push(result);
    }

    return {
      items: processed,
      total: processed.reduce((sum, d) => sum + d.amount, 0)
    };
  }
}

class Retirement401kProcessor implements DeductionProcessor {
  private readonly ANNUAL_LIMIT_2024 = 23000;
  private readonly CATCH_UP_LIMIT = 7500;
  private readonly CATCH_UP_AGE = 50;

  async process(
    employee: Employee,
    grossPay: Money,
    ytdDeductions: YTDDeductions
  ): Promise<ProcessedDeduction> {
    const deduction = employee.deductions.find(d => d.type === '401k');
    if (!deduction) {
      return { deductionId: '', type: '401k', amount: 0, ytdTotal: 0, maxReached: false };
    }

    // Calculate annual limit
    const age = this.calculateAge(employee.dateOfBirth);
    const annualLimit = age >= this.CATCH_UP_AGE
      ? this.ANNUAL_LIMIT_2024 + this.CATCH_UP_LIMIT
      : this.ANNUAL_LIMIT_2024;

    // Calculate deduction amount
    let amount: number;
    if (deduction.amountType === 'percentage') {
      amount = grossPay.amount * (deduction.amount / 100);
    } else {
      amount = deduction.amount;
    }

    // Check YTD limit
    const ytd401k = ytdDeductions['401k'] || 0;
    const remaining = annualLimit - ytd401k;

    if (remaining <= 0) {
      return {
        deductionId: deduction.id,
        type: '401k',
        amount: 0,
        ytdTotal: ytd401k,
        maxReached: true
      };
    }

    const finalAmount = Math.min(amount, remaining);

    return {
      deductionId: deduction.id,
      type: '401k',
      amount: finalAmount,
      ytdTotal: ytd401k + finalAmount,
      maxReached: ytd401k + finalAmount >= annualLimit
    };
  }
}

class GarnishmentProcessor implements DeductionProcessor {
  async process(
    employee: Employee,
    grossPay: Money,
    ytdDeductions: YTDDeductions
  ): Promise<ProcessedDeduction> {
    const garnishments = employee.deductions.filter(d => d.type === 'garnishment');
    if (garnishments.length === 0) {
      return { deductionId: '', type: 'garnishment', amount: 0, ytdTotal: 0, maxReached: false };
    }

    // Calculate disposable income (after mandatory deductions)
    const disposableIncome = this.calculateDisposableIncome(grossPay, employee);

    // Apply garnishment limits (max 25% of disposable income typically)
    const maxGarnishment = disposableIncome * 0.25;

    // Process in priority order
    let totalGarnishment = 0;
    for (const garnishment of garnishments.sort((a, b) => a.priority - b.priority)) {
      const remaining = maxGarnishment - totalGarnishment;
      if (remaining <= 0) break;

      const amount = Math.min(garnishment.amount, remaining);
      totalGarnishment += amount;
    }

    return {
      deductionId: garnishments[0].id,
      type: 'garnishment',
      amount: totalGarnishment,
      ytdTotal: (ytdDeductions['garnishment'] || 0) + totalGarnishment,
      maxReached: false
    };
  }
}
```

### Pattern 4: Payroll Reconciliation
**When to use:** Validating payroll calculations before processing
**Description:** Multi-level reconciliation checks
**Example:**
```typescript
interface ReconciliationService {
  reconcile(run: PayrollRun): Promise<ReconciliationResult>;
}

interface ReconciliationResult {
  passed: boolean;
  checks: ReconciliationCheck[];
  warnings: ReconciliationWarning[];
  errors: ReconciliationError[];
}

class PayrollReconciliationService implements ReconciliationService {
  private readonly checks: ReconciliationCheck[] = [
    { name: 'gross_pay_variance', threshold: 0.1, severity: 'warning' },
    { name: 'tax_rate_validation', threshold: 0, severity: 'error' },
    { name: 'negative_net_pay', threshold: 0, severity: 'error' },
    { name: 'deduction_limits', threshold: 0, severity: 'error' },
    { name: 'hours_validation', threshold: 0.05, severity: 'warning' },
    { name: 'ytd_accumulation', threshold: 0.01, severity: 'error' }
  ];

  async reconcile(run: PayrollRun): Promise<ReconciliationResult> {
    const calculations = await this.getCalculations(run.id);
    const previousRun = await this.getPreviousRun(run);

    const warnings: ReconciliationWarning[] = [];
    const errors: ReconciliationError[] = [];

    for (const calculation of calculations) {
      // Check 1: Gross pay variance from previous period
      if (previousRun) {
        const prevCalc = await this.getPreviousCalculation(
          calculation.employeeId, previousRun.id
        );
        if (prevCalc) {
          const variance = Math.abs(
            (calculation.grossPay.total - prevCalc.grossPay.total) /
            prevCalc.grossPay.total
          );
          if (variance > 0.5) {
            warnings.push({
              employeeId: calculation.employeeId,
              check: 'gross_pay_variance',
              message: `Gross pay changed by ${(variance * 100).toFixed(1)}%`,
              previousValue: prevCalc.grossPay.total,
              currentValue: calculation.grossPay.total
            });
          }
        }
      }

      // Check 2: Negative net pay
      if (calculation.netPay < 0) {
        errors.push({
          employeeId: calculation.employeeId,
          check: 'negative_net_pay',
          message: 'Net pay is negative',
          value: calculation.netPay
        });
      }

      // Check 3: Tax rate reasonableness
      const effectiveTaxRate = calculation.taxes.total / calculation.taxableIncome;
      if (effectiveTaxRate > 0.5) {
        warnings.push({
          employeeId: calculation.employeeId,
          check: 'high_tax_rate',
          message: `Effective tax rate is ${(effectiveTaxRate * 100).toFixed(1)}%`,
          value: effectiveTaxRate
        });
      }

      // Check 4: YTD accumulation
      const ytdValid = await this.validateYTD(calculation);
      if (!ytdValid.passed) {
        errors.push({
          employeeId: calculation.employeeId,
          check: 'ytd_accumulation',
          message: ytdValid.message,
          details: ytdValid.details
        });
      }

      // Check 5: Deduction limits
      for (const deduction of calculation.preTaxDeductions.items) {
        if (deduction.maxReached && deduction.amount > 0) {
          warnings.push({
            employeeId: calculation.employeeId,
            check: 'deduction_limit',
            message: `${deduction.type} approaching annual limit`,
            value: deduction.ytdTotal
          });
        }
      }
    }

    return {
      passed: errors.length === 0,
      checks: this.checks,
      warnings,
      errors
    };
  }
}
```

## Best Practices
- Use pipeline pattern for payroll processing
- Implement comprehensive reconciliation
- Cache tax tables with version control
- Maintain detailed audit trails
- Test edge cases (negative, zero, max limits)

## Anti-Patterns to Avoid
- Hard-coding tax rates
- Skipping reconciliation for speed
- Ignoring YTD limit calculations
- No rollback capability for payroll
