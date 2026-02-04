---
id: mfg-production-designer
name: Production Planning Designer
tier: 2
domain: manufacturing
triggers:
  - production planning
  - manufacturing execution
  - shop floor
capabilities:
  - Production scheduling
  - Work order management
  - Shop floor control
  - Capacity planning
---

# Production Planning Designer

## Role
Specialist in designing production planning and manufacturing execution systems.

## Design Patterns

### Work Order Model
```typescript
interface WorkOrder {
  id: string;
  orderNumber: string;

  // Product
  productId: string;
  productName: string;
  quantity: number;
  unit: string;

  // Schedule
  scheduledStart: Date;
  scheduledEnd: Date;
  actualStart?: Date;
  actualEnd?: Date;

  // Routing
  routing: RoutingStep[];
  currentStep: number;

  // Materials
  materials: MaterialRequirement[];

  // Status
  status: WorkOrderStatus;
  priority: number;

  // Tracking
  producedQuantity: number;
  scrapQuantity: number;
  reworkQuantity: number;
}

type WorkOrderStatus =
  | 'planned'
  | 'released'
  | 'started'
  | 'in_progress'
  | 'on_hold'
  | 'completed'
  | 'cancelled';

interface RoutingStep {
  stepNumber: number;
  operation: string;
  workCenter: string;
  setupTime: number;
  runTime: number;
  status: 'pending' | 'in_progress' | 'completed';
}
```

### Production Service
```typescript
interface ProductionService {
  createWorkOrder(request: WorkOrderRequest): Promise<WorkOrder>;
  scheduleWorkOrder(workOrderId: string, schedule: Schedule): Promise<void>;
  startOperation(workOrderId: string, stepNumber: number): Promise<void>;
  reportProduction(report: ProductionReport): Promise<void>;
  completeWorkOrder(workOrderId: string): Promise<void>;
}

interface ProductionReport {
  workOrderId: string;
  stepNumber: number;
  operatorId: string;
  quantityProduced: number;
  quantityScrapped: number;
  startTime: Date;
  endTime: Date;
  machineId?: string;
}
```

## Quality Gates
- D1: Scheduling validation
- D2: Capacity constraints
- D3: Material availability
