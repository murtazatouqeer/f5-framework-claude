---
id: mfg-quality-designer
name: Quality Management Designer
tier: 2
domain: manufacturing
triggers:
  - quality management
  - quality control
  - inspection
capabilities:
  - Quality inspection workflows
  - Defect tracking
  - Statistical process control
  - Corrective actions
---

# Quality Management Designer

## Role
Specialist in designing quality management systems for manufacturing operations.

## Design Patterns

### Quality Inspection
```typescript
interface QualityInspection {
  id: string;
  inspectionType: 'incoming' | 'in_process' | 'final' | 'audit';

  // Reference
  referenceType: 'work_order' | 'purchase_order' | 'lot';
  referenceId: string;

  // Plan
  inspectionPlan: InspectionPlan;

  // Results
  results: InspectionResult[];

  // Decision
  decision: 'accept' | 'reject' | 'conditional';
  dispositionNotes?: string;

  // Metadata
  inspector: string;
  inspectedAt: Date;
  status: 'pending' | 'in_progress' | 'completed';
}

interface InspectionPlan {
  id: string;
  characteristics: Characteristic[];
  samplingPlan: SamplingPlan;
}

interface Characteristic {
  name: string;
  type: 'visual' | 'dimensional' | 'functional' | 'attribute';
  specification: {
    target?: number;
    lowerLimit?: number;
    upperLimit?: number;
    acceptableValues?: string[];
  };
  critical: boolean;
}

interface InspectionResult {
  characteristicId: string;
  measuredValue: number | string;
  passed: boolean;
  notes?: string;
}
```

### Quality Service
```typescript
interface QualityService {
  createInspection(request: InspectionRequest): Promise<QualityInspection>;
  recordResult(inspectionId: string, result: InspectionResult): Promise<void>;
  makeDisposition(inspectionId: string, decision: string): Promise<void>;
  createNCR(nonConformance: NonConformanceReport): Promise<NCR>;
  initiateCorrective Action(ncrId: string): Promise<CorrectiveAction>;
}
```

## Quality Gates
- D1: Inspection accuracy
- D2: SPC chart calculations
- D3: Audit trail completeness
