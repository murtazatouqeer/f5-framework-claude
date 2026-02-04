# Quality Management Template

## Quality Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Inspect    │────▶│   Record    │────▶│  Disposition│────▶│  Corrective │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Sample plan         Measurements        Accept/Reject       Root cause
  Characteristics     Pass/Fail           Hold material       CAPA
  Instruments         Documentation       Rework/Scrap        Prevention
```

## Inspection Types

```typescript
type InspectionType =
  | 'receiving'      // Incoming materials
  | 'in_process'     // During production
  | 'final'          // Finished goods
  | 'first_article'  // New product/process
  | 'periodic'       // Scheduled audit
  | 'customer';      // Customer requirement
```

## Non-Conformance Report

```typescript
interface NonConformanceReport {
  id: string;
  ncrNumber: string;

  // Reference
  sourceType: 'inspection' | 'production' | 'customer' | 'supplier';
  sourceId: string;

  // Affected items
  affectedItems: {
    type: 'lot' | 'serial' | 'work_order';
    identifier: string;
    quantity: number;
  }[];

  // Description
  description: string;
  defectType: string;
  severity: 'critical' | 'major' | 'minor';

  // Disposition
  disposition?: {
    decision: 'use_as_is' | 'rework' | 'scrap' | 'return' | 'sort';
    justification: string;
    approvedBy: string;
    approvedAt: Date;
  };

  // CAPA
  correctiveActionId?: string;

  status: 'open' | 'under_review' | 'dispositioned' | 'closed';
}
```

## Statistical Process Control

```typescript
interface SPCChart {
  characteristicId: string;
  chartType: 'xbar_r' | 'xbar_s' | 'p' | 'np' | 'c' | 'u';

  // Control limits
  controlLimits: {
    ucl: number;
    lcl: number;
    centerLine: number;
  };

  // Specification limits
  specLimits?: {
    usl: number;
    lsl: number;
    target: number;
  };

  // Data points
  dataPoints: SPCDataPoint[];

  // Capability
  capability?: {
    cp: number;
    cpk: number;
    pp: number;
    ppk: number;
  };
}

interface SPCDataPoint {
  timestamp: Date;
  value: number;
  subgroupId?: string;
  outOfControl: boolean;
  rule Violations?: string[];
}
```
