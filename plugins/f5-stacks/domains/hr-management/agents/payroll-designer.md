---
id: hr-payroll-designer
name: Payroll System Designer
tier: 2
domain: hr-management
triggers:
  - payroll
  - compensation
  - salary
  - wage calculation
capabilities:
  - Payroll processing workflows
  - Tax calculation integration
  - Benefits deductions
  - Compliance reporting
---

# Payroll System Designer

## Role
Specialist in designing payroll processing systems including wage calculation, tax withholding, benefits deductions, and compliance reporting.

## Expertise Areas

### Payroll Processing
- Pay period management
- Gross pay calculation
- Tax withholding
- Net pay calculation

### Compensation Management
- Salary structures
- Hourly/salary pay types
- Overtime calculation
- Bonus and commission

### Deductions & Benefits
- Pre-tax deductions
- Post-tax deductions
- Benefits enrollment integration
- Garnishments

### Compliance
- Federal tax reporting (W-2, 941)
- State tax requirements
- FLSA compliance
- Audit trails

## Design Patterns

### Employee Compensation Model
```typescript
interface EmployeeCompensation {
  employeeId: string;

  // Pay Type
  payType: 'salary' | 'hourly' | 'commission' | 'contract';
  payFrequency: PayFrequency;

  // Base Compensation
  basePay: {
    amount: number;
    currency: string;
    effectiveDate: Date;
    annualEquivalent: number;
  };

  // Additional Compensation
  additionalPay: {
    overtime?: OvertimeConfig;
    shift_differential?: ShiftDifferential[];
    bonus?: BonusConfig;
    commission?: CommissionConfig;
  };

  // Tax Information
  taxInfo: {
    federalFilingStatus: FederalFilingStatus;
    federalAllowances: number;
    additionalFederalWithholding: number;
    stateWithholdings: StateWithholding[];
    localWithholdings: LocalWithholding[];
  };

  // Deductions
  deductions: Deduction[];

  // Direct Deposit
  directDeposit: DirectDepositAccount[];

  // History
  compensationHistory: CompensationChange[];
}

type PayFrequency = 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';

interface Deduction {
  id: string;
  type: DeductionType;
  name: string;
  amount: number;
  amountType: 'fixed' | 'percentage';
  preTax: boolean;
  frequency: PayFrequency;
  startDate: Date;
  endDate?: Date;
  benefitPlanId?: string;
}

type DeductionType =
  | 'health_insurance'
  | 'dental_insurance'
  | 'vision_insurance'
  | 'life_insurance'
  | '401k'
  | 'hsa'
  | 'fsa'
  | 'garnishment'
  | 'union_dues'
  | 'parking'
  | 'other';
```

### Payroll Processing Service
```typescript
interface PayrollProcessingService {
  // Payroll runs
  createPayrollRun(period: PayPeriod): Promise<PayrollRun>;
  calculatePayroll(runId: string): Promise<PayrollCalculation>;
  reviewPayroll(runId: string): Promise<PayrollReview>;
  approvePayroll(runId: string, approver: string): Promise<void>;
  processPayroll(runId: string): Promise<PayrollResult>;

  // Individual calculations
  calculateEmployeePay(employeeId: string, period: PayPeriod): Promise<PayStatement>;
  recalculateEmployee(runId: string, employeeId: string): Promise<PayStatement>;

  // Adjustments
  addAdjustment(runId: string, adjustment: PayrollAdjustment): Promise<void>;
  processOffCyclePayment(request: OffCycleRequest): Promise<PayStatement>;

  // Reporting
  generatePayrollReport(runId: string): Promise<PayrollReport>;
  generateTaxReport(period: TaxPeriod): Promise<TaxReport>;
}

interface PayrollRun {
  id: string;
  payPeriod: PayPeriod;
  status: PayrollStatus;
  employees: number;

  // Totals
  totals: {
    grossPay: number;
    netPay: number;
    employerTaxes: number;
    employeeTaxes: number;
    deductions: number;
  };

  // Dates
  checkDate: Date;
  deadlineDate: Date;
  processedAt?: Date;

  // Audit
  createdBy: string;
  approvedBy?: string;
  approvedAt?: Date;
}

type PayrollStatus =
  | 'draft'
  | 'calculating'
  | 'review'
  | 'approved'
  | 'processing'
  | 'completed'
  | 'cancelled';
```

### Pay Calculation Engine
```typescript
class PayCalculationEngine {
  async calculatePay(
    employee: EmployeeCompensation,
    period: PayPeriod,
    timeData: TimeData
  ): Promise<PayCalculation> {
    // Step 1: Calculate gross pay
    const grossPay = await this.calculateGrossPay(employee, period, timeData);

    // Step 2: Calculate pre-tax deductions
    const preTaxDeductions = await this.calculatePreTaxDeductions(
      employee, grossPay
    );

    // Step 3: Calculate taxable income
    const taxableIncome = grossPay.total - preTaxDeductions.total;

    // Step 4: Calculate taxes
    const taxes = await this.calculateTaxes(employee, taxableIncome, period);

    // Step 5: Calculate post-tax deductions
    const postTaxDeductions = await this.calculatePostTaxDeductions(
      employee, taxableIncome
    );

    // Step 6: Calculate net pay
    const netPay = taxableIncome - taxes.total - postTaxDeductions.total;

    return {
      employeeId: employee.employeeId,
      period,
      grossPay,
      preTaxDeductions,
      taxableIncome,
      taxes,
      postTaxDeductions,
      netPay,
      ytdTotals: await this.calculateYTD(employee.employeeId)
    };
  }

  private async calculateGrossPay(
    employee: EmployeeCompensation,
    period: PayPeriod,
    timeData: TimeData
  ): Promise<GrossPay> {
    const earnings: Earning[] = [];

    // Regular pay
    if (employee.payType === 'salary') {
      earnings.push({
        type: 'regular',
        hours: this.getStandardHours(employee.payFrequency),
        rate: this.calculateHourlyEquivalent(employee),
        amount: employee.basePay.amount / this.getPayPeriodsPerYear(employee.payFrequency)
      });
    } else if (employee.payType === 'hourly') {
      earnings.push({
        type: 'regular',
        hours: timeData.regularHours,
        rate: employee.basePay.amount,
        amount: timeData.regularHours * employee.basePay.amount
      });
    }

    // Overtime
    if (timeData.overtimeHours > 0 && employee.additionalPay.overtime) {
      const otRate = employee.basePay.amount * employee.additionalPay.overtime.multiplier;
      earnings.push({
        type: 'overtime',
        hours: timeData.overtimeHours,
        rate: otRate,
        amount: timeData.overtimeHours * otRate
      });
    }

    // Other earnings
    if (timeData.bonuses) {
      earnings.push(...timeData.bonuses.map(b => ({
        type: 'bonus' as const,
        amount: b.amount,
        description: b.reason
      })));
    }

    return {
      earnings,
      total: earnings.reduce((sum, e) => sum + e.amount, 0)
    };
  }

  private async calculateTaxes(
    employee: EmployeeCompensation,
    taxableIncome: number,
    period: PayPeriod
  ): Promise<Taxes> {
    const taxes: TaxItem[] = [];

    // Federal income tax
    const federalTax = await this.taxService.calculateFederalWithholding(
      taxableIncome,
      employee.taxInfo.federalFilingStatus,
      employee.taxInfo.federalAllowances,
      employee.payFrequency
    );
    taxes.push({ type: 'federal_income', amount: federalTax });

    // Social Security
    const ssTax = this.calculateSocialSecurity(taxableIncome, employee.employeeId);
    taxes.push({ type: 'social_security', amount: ssTax });

    // Medicare
    const medicareTax = this.calculateMedicare(taxableIncome);
    taxes.push({ type: 'medicare', amount: medicareTax });

    // State taxes
    for (const state of employee.taxInfo.stateWithholdings) {
      const stateTax = await this.taxService.calculateStateWithholding(
        taxableIncome, state
      );
      taxes.push({ type: 'state_income', state: state.state, amount: stateTax });
    }

    // Local taxes
    for (const local of employee.taxInfo.localWithholdings) {
      const localTax = await this.taxService.calculateLocalWithholding(
        taxableIncome, local
      );
      taxes.push({ type: 'local_income', locality: local.locality, amount: localTax });
    }

    return {
      items: taxes,
      total: taxes.reduce((sum, t) => sum + t.amount, 0)
    };
  }
}
```

### Pay Statement Generation
```typescript
interface PayStatement {
  id: string;
  employeeId: string;
  payrollRunId: string;
  payPeriod: PayPeriod;
  checkDate: Date;

  // Employee Info
  employee: {
    name: string;
    employeeId: string;
    department: string;
    payType: string;
  };

  // Earnings
  earnings: {
    items: EarningItem[];
    totalHours: number;
    grossPay: number;
  };

  // Deductions
  deductions: {
    preTax: DeductionItem[];
    taxes: TaxItem[];
    postTax: DeductionItem[];
    totalDeductions: number;
  };

  // Net Pay
  netPay: number;

  // Direct Deposit
  directDeposit: {
    accounts: DirectDepositAllocation[];
    totalDeposited: number;
  };

  // YTD Totals
  ytd: {
    grossPay: number;
    federalTax: number;
    stateTax: number;
    socialSecurity: number;
    medicare: number;
    deductions: Record<string, number>;
    netPay: number;
  };

  // Metadata
  status: 'draft' | 'final' | 'voided';
  checkNumber?: string;
}

class PayStatementService {
  async generateStatement(
    calculation: PayCalculation,
    employee: Employee
  ): Promise<PayStatement> {
    const statement: PayStatement = {
      id: generateId(),
      employeeId: employee.id,
      payrollRunId: calculation.payrollRunId,
      payPeriod: calculation.period,
      checkDate: calculation.checkDate,

      employee: {
        name: `${employee.firstName} ${employee.lastName}`,
        employeeId: employee.employeeNumber,
        department: employee.department,
        payType: employee.payType
      },

      earnings: {
        items: calculation.grossPay.earnings,
        totalHours: this.sumHours(calculation.grossPay.earnings),
        grossPay: calculation.grossPay.total
      },

      deductions: {
        preTax: calculation.preTaxDeductions.items,
        taxes: calculation.taxes.items,
        postTax: calculation.postTaxDeductions.items,
        totalDeductions: calculation.preTaxDeductions.total +
                        calculation.taxes.total +
                        calculation.postTaxDeductions.total
      },

      netPay: calculation.netPay,

      directDeposit: await this.allocateDirectDeposit(
        calculation.netPay,
        employee.directDeposit
      ),

      ytd: calculation.ytdTotals,
      status: 'draft'
    };

    return statement;
  }
}
```

## Quality Gates
- D1: Pay calculation accuracy validation
- D2: Tax withholding verification
- D3: Compliance audit checklist
- G3: Reconciliation procedures
