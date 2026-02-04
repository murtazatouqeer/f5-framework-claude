# Manufacturing SRS Template

## 1. System Overview

### 1.1 Purpose
Manufacturing Execution System (MES) for production planning, quality control, and equipment management.

### 1.2 Core Capabilities
- Production planning and scheduling
- Work order management
- Quality inspection and SPC
- Equipment maintenance (TPM)
- Inventory and material tracking
- OEE calculation and reporting

## 2. Functional Requirements

### 2.1 Production Management

```typescript
interface ProductionRequirements {
  workOrderManagement: {
    creation: 'manual' | 'mrp_generated' | 'sales_order';
    scheduling: 'finite' | 'infinite' | 'constraint_based';
    tracking: 'operation' | 'work_center' | 'machine';
    completion: 'backflush' | 'detailed_reporting';
  };

  billOfMaterials: {
    structure: 'single_level' | 'multi_level' | 'phantom';
    versioning: boolean;
    effectivityDates: boolean;
    alternativeMaterials: boolean;
  };

  routing: {
    operationSequencing: boolean;
    parallelOperations: boolean;
    alternativeRouting: boolean;
    subcontracting: boolean;
  };
}
```

### 2.2 Quality Management

```typescript
interface QualityRequirements {
  inspection: {
    types: ('receiving' | 'in_process' | 'final' | 'audit')[];
    sampling: 'aql' | 'skip_lot' | '100_percent';
    characteristics: 'variable' | 'attribute' | 'both';
  };

  spc: {
    chartTypes: ('xbar_r' | 'xbar_s' | 'p' | 'np' | 'c' | 'u')[];
    controlRules: 'western_electric' | 'nelson' | 'custom';
    capability: boolean;
  };

  nonConformance: {
    tracking: boolean;
    disposition: ('use_as_is' | 'rework' | 'scrap' | 'return')[];
    capa: boolean;
  };
}
```

### 2.3 Equipment Management

```typescript
interface EquipmentRequirements {
  maintenance: {
    types: ('preventive' | 'predictive' | 'corrective')[];
    scheduling: 'calendar' | 'meter_based' | 'condition_based';
    workOrders: boolean;
    sparePartsTracking: boolean;
  };

  downtime: {
    tracking: boolean;
    categories: ('planned' | 'unplanned' | 'setup' | 'changeover')[];
    rootCauseAnalysis: boolean;
  };

  oee: {
    calculation: 'real_time' | 'batch' | 'both';
    components: ['availability', 'performance', 'quality'];
    benchmarking: boolean;
  };
}
```

## 3. Data Models

### 3.1 Work Order

```typescript
interface WorkOrder {
  id: string;
  orderNumber: string;
  type: 'production' | 'rework' | 'prototype';

  // Product
  product: {
    id: string;
    name: string;
    revision: string;
  };

  // Quantity
  quantity: {
    ordered: number;
    produced: number;
    scrapped: number;
    unit: string;
  };

  // Schedule
  schedule: {
    plannedStart: Date;
    plannedEnd: Date;
    actualStart?: Date;
    actualEnd?: Date;
  };

  // Routing
  routing: WorkOrderOperation[];
  currentOperation: number;

  // Materials
  materials: MaterialAllocation[];
  materialStatus: 'not_issued' | 'partial' | 'complete';

  // Status
  status: WorkOrderStatus;
  priority: number;

  // Traceability
  lotNumber?: string;
  serialNumbers?: string[];

  // Metadata
  createdBy: string;
  createdAt: Date;
}

type WorkOrderStatus =
  | 'draft'
  | 'planned'
  | 'released'
  | 'started'
  | 'in_progress'
  | 'on_hold'
  | 'completed'
  | 'closed'
  | 'cancelled';
```

### 3.2 Equipment

```typescript
interface Equipment {
  id: string;
  assetNumber: string;
  name: string;
  type: string;
  category: 'machine' | 'tool' | 'fixture' | 'gauge';

  // Location
  location: {
    plant: string;
    area: string;
    line?: string;
    workCenter?: string;
  };

  // Specifications
  specs: {
    manufacturer: string;
    model: string;
    serialNumber: string;
    purchaseDate: Date;
    installDate: Date;
    warrantyExpiry?: Date;
  };

  // Capacity
  capacity?: {
    value: number;
    unit: string;
    cycleTime?: number;
  };

  // Status
  status: 'active' | 'inactive' | 'maintenance' | 'retired';
  currentState: 'running' | 'idle' | 'setup' | 'down';

  // Maintenance
  maintenance: {
    schedules: MaintenanceSchedule[];
    lastPM?: Date;
    nextPM?: Date;
    meterReading?: number;
  };

  // Performance
  oee?: OEEMetrics;
}
```

## 4. Integration Requirements

### 4.1 ERP Integration

```typescript
interface ERPIntegration {
  inbound: {
    salesOrders: boolean;
    productionOrders: boolean;
    inventory: boolean;
    bom: boolean;
  };

  outbound: {
    productionConfirmation: boolean;
    materialConsumption: boolean;
    qualityResults: boolean;
    inventoryMovements: boolean;
  };

  protocol: 'rest' | 'idoc' | 'rfc' | 'odata';
  frequency: 'real_time' | 'batch';
}
```

### 4.2 Machine Integration

```typescript
interface MachineIntegration {
  protocols: ('opc_ua' | 'mqtt' | 'modbus' | 'profinet')[];
  dataCollection: {
    automatic: boolean;
    frequency: number; // milliseconds
    signals: string[];
  };
  plcIntegration: boolean;
}
```

## 5. Compliance Requirements

### 5.1 Industry Standards
- ISO 9001 Quality Management
- ISO 14001 Environmental
- IATF 16949 Automotive
- AS9100 Aerospace
- FDA 21 CFR Part 11 Pharma

### 5.2 Traceability

```typescript
interface TraceabilityRequirements {
  lotTracking: boolean;
  serialTracking: boolean;
  genealogy: boolean;

  retention: {
    productionRecords: number; // years
    qualityRecords: number;
    maintenanceRecords: number;
  };

  electronicSignatures: boolean;
  auditTrail: boolean;
}
```

## 6. Reporting Requirements

### 6.1 Production Reports
- Work order status
- Production output
- Schedule adherence
- Yield analysis

### 6.2 Quality Reports
- First pass yield
- Defect Pareto
- SPC charts
- Capability studies
- NCR summary

### 6.3 Equipment Reports
- OEE dashboards
- Downtime analysis
- Maintenance compliance
- MTBF/MTTR

## 7. Non-Functional Requirements

### 7.1 Performance
- Real-time data collection: <100ms latency
- Report generation: <5 seconds
- Concurrent users: 500+
- Data retention: 10+ years

### 7.2 Availability
- Uptime: 99.9%
- Failover: <30 seconds
- Offline capability for shop floor

### 7.3 Security
- Role-based access control
- Electronic signatures
- Audit trail
- Data encryption
