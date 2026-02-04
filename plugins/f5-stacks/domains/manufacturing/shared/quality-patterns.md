# Quality Management Patterns

## Inspection Workflow Pattern

```typescript
interface InspectionService {
  createInspection(request: InspectionRequest): Promise<Inspection>;
  recordMeasurement(inspectionId: string, measurement: Measurement): Promise<void>;
  makeDisposition(inspectionId: string, decision: DispositionDecision): Promise<void>;
}

interface InspectionRequest {
  type: 'receiving' | 'in_process' | 'final' | 'audit';
  referenceType: 'work_order' | 'purchase_order' | 'lot';
  referenceId: string;
  inspectionPlanId: string;
  quantity: number;
}

interface Inspection {
  id: string;
  type: string;

  // Reference
  reference: {
    type: string;
    id: string;
  };

  // Plan
  plan: InspectionPlan;
  sampleSize: number;

  // Results
  measurements: Measurement[];

  // Decision
  status: 'pending' | 'in_progress' | 'completed';
  decision?: 'accept' | 'reject' | 'conditional';

  // Metadata
  inspector: string;
  startedAt?: Date;
  completedAt?: Date;
}

// Implementation
async function createInspection(request: InspectionRequest): Promise<Inspection> {
  const plan = await getInspectionPlan(request.inspectionPlanId);
  const sampleSize = calculateSampleSize(plan.samplingPlan, request.quantity);

  const inspection: Inspection = {
    id: generateId(),
    type: request.type,
    reference: {
      type: request.referenceType,
      id: request.referenceId
    },
    plan,
    sampleSize,
    measurements: [],
    status: 'pending',
    inspector: getCurrentUser()
  };

  // Create measurement records for each characteristic
  for (const char of plan.characteristics) {
    for (let i = 0; i < sampleSize; i++) {
      inspection.measurements.push({
        characteristicId: char.id,
        sampleNumber: i + 1,
        value: null,
        passed: null
      });
    }
  }

  await saveInspection(inspection);
  return inspection;
}
```

## Sampling Plan Pattern

```typescript
interface SamplingPlan {
  type: 'aql' | 'ltpd' | 'skip_lot' | 'custom';
  inspectionLevel: 'I' | 'II' | 'III' | 'S1' | 'S2' | 'S3' | 'S4';
  aql?: number;

  // Normal/Tightened/Reduced switching
  switchingRules?: {
    toTightened: number; // rejections to switch
    toReduced: number;   // acceptances to switch
    toNormal: number;    // lots to return
  };
}

interface SampleSizeResult {
  sampleSize: number;
  acceptNumber: number;
  rejectNumber: number;
  code: string;
}

// AQL-based sample size calculation
function calculateSampleSize(
  plan: SamplingPlan,
  lotSize: number
): SampleSizeResult {
  const codeTable = getCodeTable(plan.inspectionLevel);
  const code = codeTable.find(
    row => lotSize >= row.minLot && lotSize <= row.maxLot
  )?.code;

  const sampleTable = getSampleTable(plan.type);
  const sample = sampleTable[code][plan.aql];

  return {
    sampleSize: sample.n,
    acceptNumber: sample.ac,
    rejectNumber: sample.re,
    code
  };
}

// Inspection decision
function evaluateInspection(
  measurements: Measurement[],
  plan: SamplingPlan
): 'accept' | 'reject' {
  const { acceptNumber, rejectNumber } = calculateSampleSize(
    plan,
    measurements.length
  );

  const defects = measurements.filter(m => !m.passed).length;

  if (defects <= acceptNumber) return 'accept';
  if (defects >= rejectNumber) return 'reject';

  // Double sampling - need more samples
  throw new Error('Double sampling required');
}
```

## SPC (Statistical Process Control) Pattern

```typescript
interface SPCService {
  addDataPoint(chartId: string, value: number, subgroup?: string): Promise<void>;
  calculateControlLimits(chartId: string): Promise<ControlLimits>;
  detectOutOfControl(chartId: string): Promise<Violation[]>;
  calculateCapability(chartId: string): Promise<CapabilityIndices>;
}

interface SPCChart {
  id: string;
  characteristicId: string;
  chartType: 'xbar_r' | 'xbar_s' | 'individuals' | 'p' | 'np' | 'c' | 'u';

  // Limits
  controlLimits: ControlLimits;
  specLimits?: SpecLimits;

  // Data
  subgroups: Subgroup[];

  // Rules
  rules: ControlRule[];
}

interface ControlLimits {
  ucl: number;  // Upper control limit
  lcl: number;  // Lower control limit
  cl: number;   // Center line
}

interface Subgroup {
  id: string;
  timestamp: Date;
  values: number[];
  mean: number;
  range: number;
  stdDev?: number;
}

// Control limit calculation for X-bar R chart
function calculateXbarRLimits(subgroups: Subgroup[]): {
  xbar: ControlLimits;
  range: ControlLimits;
} {
  const n = subgroups[0].values.length; // subgroup size
  const xbarbar = mean(subgroups.map(s => s.mean));
  const rbar = mean(subgroups.map(s => s.range));

  // Constants from control chart tables
  const A2 = getA2(n);
  const D3 = getD3(n);
  const D4 = getD4(n);

  return {
    xbar: {
      ucl: xbarbar + A2 * rbar,
      cl: xbarbar,
      lcl: xbarbar - A2 * rbar
    },
    range: {
      ucl: D4 * rbar,
      cl: rbar,
      lcl: D3 * rbar
    }
  };
}

// Western Electric rules for out-of-control detection
function detectViolations(
  chart: SPCChart,
  rules: string[] = ['rule1', 'rule2', 'rule3', 'rule4']
): Violation[] {
  const violations: Violation[] = [];
  const data = chart.subgroups.map(s => s.mean);
  const { ucl, lcl, cl } = chart.controlLimits;
  const sigma = (ucl - cl) / 3;

  // Rule 1: One point beyond 3 sigma
  if (rules.includes('rule1')) {
    data.forEach((val, i) => {
      if (val > ucl || val < lcl) {
        violations.push({
          rule: 'rule1',
          description: 'Point beyond control limits',
          subgroupIndex: i,
          value: val
        });
      }
    });
  }

  // Rule 2: Nine points in a row on same side of center
  if (rules.includes('rule2')) {
    for (let i = 8; i < data.length; i++) {
      const window = data.slice(i - 8, i + 1);
      if (window.every(v => v > cl) || window.every(v => v < cl)) {
        violations.push({
          rule: 'rule2',
          description: 'Nine points same side of center',
          subgroupIndex: i,
          value: data[i]
        });
      }
    }
  }

  // Rule 3: Six points in a row steadily increasing or decreasing
  if (rules.includes('rule3')) {
    for (let i = 5; i < data.length; i++) {
      const window = data.slice(i - 5, i + 1);
      const increasing = window.every((v, j) => j === 0 || v > window[j - 1]);
      const decreasing = window.every((v, j) => j === 0 || v < window[j - 1]);
      if (increasing || decreasing) {
        violations.push({
          rule: 'rule3',
          description: 'Six points trending',
          subgroupIndex: i,
          value: data[i]
        });
      }
    }
  }

  return violations;
}

// Process capability calculation
function calculateCapability(
  chart: SPCChart
): CapabilityIndices {
  const data = chart.subgroups.flatMap(s => s.values);
  const { usl, lsl, target } = chart.specLimits!;

  const xbar = mean(data);
  const sigma = stdDev(data);

  // Cp - potential capability
  const cp = (usl - lsl) / (6 * sigma);

  // Cpk - actual capability
  const cpu = (usl - xbar) / (3 * sigma);
  const cpl = (xbar - lsl) / (3 * sigma);
  const cpk = Math.min(cpu, cpl);

  // Pp/Ppk - performance indices (using overall std dev)
  const sigmaOverall = stdDevOverall(data);
  const pp = (usl - lsl) / (6 * sigmaOverall);
  const ppk = Math.min(
    (usl - xbar) / (3 * sigmaOverall),
    (xbar - lsl) / (3 * sigmaOverall)
  );

  return { cp, cpk, pp, ppk };
}
```

## Non-Conformance Management Pattern

```typescript
interface NCRService {
  createNCR(report: NCRRequest): Promise<NonConformanceReport>;
  assignDisposition(ncrId: string, disposition: Disposition): Promise<void>;
  initiateCAPA(ncrId: string): Promise<CorrectiveAction>;
  closeNCR(ncrId: string): Promise<void>;
}

interface NonConformanceReport {
  id: string;
  ncrNumber: string;

  // Source
  source: {
    type: 'inspection' | 'production' | 'customer' | 'supplier';
    id: string;
  };

  // Affected items
  affectedItems: {
    type: 'lot' | 'serial' | 'work_order';
    identifier: string;
    quantity: number;
    location?: string;
  }[];

  // Description
  defect: {
    type: string;
    description: string;
    severity: 'critical' | 'major' | 'minor';
    images?: string[];
  };

  // Containment
  containment?: {
    action: string;
    implementedBy: string;
    implementedAt: Date;
  };

  // Disposition
  disposition?: Disposition;

  // CAPA
  capaId?: string;

  // Status
  status: 'open' | 'under_review' | 'dispositioned' | 'closed';

  // Metadata
  createdBy: string;
  createdAt: Date;
}

interface Disposition {
  decision: 'use_as_is' | 'rework' | 'repair' | 'scrap' | 'return' | 'sort';
  justification: string;
  conditions?: string;
  approver: string;
  approvedAt: Date;

  // For rework/repair
  reworkInstructions?: string;
  reinspectionRequired: boolean;
}

// NCR workflow implementation
async function createNCR(request: NCRRequest): Promise<NonConformanceReport> {
  const ncr: NonConformanceReport = {
    id: generateId(),
    ncrNumber: await generateNCRNumber(),
    source: request.source,
    affectedItems: request.affectedItems,
    defect: request.defect,
    status: 'open',
    createdBy: getCurrentUser(),
    createdAt: new Date()
  };

  // Auto-quarantine if critical
  if (request.defect.severity === 'critical') {
    for (const item of request.affectedItems) {
      await quarantineItem(item);
    }

    ncr.containment = {
      action: 'Auto-quarantine due to critical defect',
      implementedBy: 'system',
      implementedAt: new Date()
    };
  }

  // Notify quality team
  await notifyQualityTeam(ncr);

  await saveNCR(ncr);
  return ncr;
}
```

## OEE Calculation Pattern

```typescript
interface OEEService {
  calculateOEE(equipmentId: string, period: DateRange): Promise<OEEResult>;
  getOEETrend(equipmentId: string, periods: number): Promise<OEETrend>;
}

interface OEEResult {
  equipmentId: string;
  period: DateRange;

  // Components
  availability: {
    value: number;
    plannedTime: number;
    actualRunTime: number;
    downtimeMinutes: number;
    downtimeReasons: { reason: string; minutes: number }[];
  };

  performance: {
    value: number;
    idealCycleTime: number;
    actualCycleTime: number;
    totalParts: number;
    speedLoss: number;
  };

  quality: {
    value: number;
    totalParts: number;
    goodParts: number;
    defectParts: number;
    defectReasons: { reason: string; count: number }[];
  };

  // Overall
  oee: number;

  // Losses
  sixBigLosses: {
    breakdowns: number;
    setupAdjustment: number;
    idlingMinorStops: number;
    reducedSpeed: number;
    processDefects: number;
    reducedYield: number;
  };
}

// OEE calculation implementation
async function calculateOEE(
  equipmentId: string,
  period: DateRange
): Promise<OEEResult> {
  const equipment = await getEquipment(equipmentId);
  const production = await getProductionData(equipmentId, period);
  const downtime = await getDowntimeData(equipmentId, period);
  const quality = await getQualityData(equipmentId, period);

  // Availability
  const plannedTime = calculatePlannedTime(period, equipment.calendar);
  const downtimeMinutes = sumDowntime(downtime);
  const actualRunTime = plannedTime - downtimeMinutes;
  const availability = actualRunTime / plannedTime;

  // Performance
  const idealCycleTime = equipment.capacity.cycleTime;
  const totalParts = production.totalQuantity;
  const actualCycleTime = actualRunTime / totalParts;
  const performance = (idealCycleTime * totalParts) / actualRunTime;

  // Quality
  const goodParts = production.goodQuantity;
  const defectParts = quality.defectQuantity;
  const qualityRate = goodParts / totalParts;

  // OEE
  const oee = availability * performance * qualityRate;

  return {
    equipmentId,
    period,
    availability: {
      value: availability,
      plannedTime,
      actualRunTime,
      downtimeMinutes,
      downtimeReasons: groupDowntimeByReason(downtime)
    },
    performance: {
      value: performance,
      idealCycleTime,
      actualCycleTime,
      totalParts,
      speedLoss: actualCycleTime - idealCycleTime
    },
    quality: {
      value: qualityRate,
      totalParts,
      goodParts,
      defectParts,
      defectReasons: groupDefectsByReason(quality.defects)
    },
    oee,
    sixBigLosses: calculateSixBigLosses(downtime, production, quality)
  };
}
```

## CAPA (Corrective and Preventive Action) Pattern

```typescript
interface CAPAService {
  createCAPA(request: CAPARequest): Promise<CorrectiveAction>;
  performRootCause(capaId: string, analysis: RootCauseAnalysis): Promise<void>;
  addAction(capaId: string, action: CAPAAction): Promise<void>;
  verifyEffectiveness(capaId: string, verification: Verification): Promise<void>;
}

interface CorrectiveAction {
  id: string;
  capaNumber: string;
  type: 'corrective' | 'preventive';

  // Source
  sourceNCRs: string[];

  // Problem
  problemStatement: string;
  containmentAction?: string;

  // Root cause
  rootCause?: {
    method: '5why' | 'fishbone' | 'fmea' | 'other';
    analysis: string;
    rootCauses: string[];
  };

  // Actions
  actions: CAPAAction[];

  // Verification
  verification?: {
    method: string;
    results: string;
    effective: boolean;
    verifiedBy: string;
    verifiedAt: Date;
  };

  // Status
  status: 'open' | 'analyzing' | 'implementing' | 'verifying' | 'closed';

  // Dates
  targetDate: Date;
  closedAt?: Date;
}

interface CAPAAction {
  id: string;
  description: string;
  assignee: string;
  dueDate: Date;
  status: 'pending' | 'in_progress' | 'completed';
  completedAt?: Date;
  evidence?: string[];
}

// 5-Why analysis helper
function analyze5Why(
  problem: string,
  whys: string[]
): RootCauseAnalysis {
  return {
    method: '5why',
    analysis: whys.map((why, i) => `Why ${i + 1}: ${why}`).join('\n'),
    rootCauses: [whys[whys.length - 1]]
  };
}
```
