# Production Management Patterns

## Work Order State Machine

```typescript
const workOrderStateMachine = {
  initial: 'draft',
  states: {
    draft: {
      on: {
        PLAN: 'planned',
        CANCEL: 'cancelled'
      }
    },
    planned: {
      on: {
        RELEASE: { target: 'released', guard: 'materialsAvailable' },
        CANCEL: 'cancelled'
      }
    },
    released: {
      on: {
        STAGE_MATERIALS: 'material_staged',
        START: 'started',
        HOLD: 'on_hold'
      }
    },
    material_staged: {
      on: {
        START: 'started',
        HOLD: 'on_hold'
      }
    },
    started: {
      on: {
        REPORT_PROGRESS: 'in_progress',
        HOLD: 'on_hold'
      }
    },
    in_progress: {
      on: {
        COMPLETE: { target: 'completed', guard: 'allOperationsComplete' },
        HOLD: 'on_hold'
      }
    },
    on_hold: {
      on: {
        RESUME: 'in_progress',
        CANCEL: 'cancelled'
      }
    },
    completed: {
      on: {
        CLOSE: { target: 'closed', guard: 'qualityApproved' }
      }
    },
    closed: { type: 'final' },
    cancelled: { type: 'final' }
  }
};
```

## BOM Explosion Pattern

```typescript
interface BOMExplosionService {
  explodeBOM(
    productId: string,
    quantity: number,
    options: ExplosionOptions
  ): Promise<MaterialRequirement[]>;

  calculateRequirements(
    workOrder: WorkOrder
  ): Promise<MaterialRequirement[]>;
}

interface ExplosionOptions {
  level: 'single' | 'multi' | 'phantom_only';
  effectiveDate: Date;
  includeScrapFactor: boolean;
  considerInventory: boolean;
}

interface MaterialRequirement {
  materialId: string;
  materialName: string;
  requiredQuantity: number;
  availableQuantity: number;
  shortageQuantity: number;
  unit: string;
  level: number;
  parentId?: string;
}

// Implementation
async function explodeBOM(
  productId: string,
  quantity: number,
  options: ExplosionOptions
): Promise<MaterialRequirement[]> {
  const bom = await getBOM(productId, options.effectiveDate);
  const requirements: MaterialRequirement[] = [];

  for (const component of bom.components) {
    let reqQty = component.quantity * quantity;

    if (options.includeScrapFactor) {
      reqQty *= (1 + component.scrapFactor);
    }

    if (component.isPhantom && options.level !== 'single') {
      // Recurse into phantom
      const subReqs = await explodeBOM(
        component.materialId,
        reqQty,
        options
      );
      requirements.push(...subReqs);
    } else {
      const available = options.considerInventory
        ? await getAvailableInventory(component.materialId)
        : 0;

      requirements.push({
        materialId: component.materialId,
        materialName: component.materialName,
        requiredQuantity: reqQty,
        availableQuantity: available,
        shortageQuantity: Math.max(0, reqQty - available),
        unit: component.unit,
        level: 1,
        parentId: productId
      });
    }
  }

  return requirements;
}
```

## Production Scheduling Pattern

```typescript
interface SchedulingService {
  scheduleWorkOrder(
    workOrder: WorkOrder,
    strategy: SchedulingStrategy
  ): Promise<Schedule>;

  reschedule(
    workOrderIds: string[],
    reason: string
  ): Promise<Schedule[]>;
}

type SchedulingStrategy =
  | 'forward'    // From start date
  | 'backward'   // From due date
  | 'bottleneck' // Around constraints
  | 'priority';  // By priority

interface Schedule {
  workOrderId: string;
  operations: OperationSchedule[];
  totalLeadTime: number;
  criticalPath: number[];
}

interface OperationSchedule {
  operationNumber: number;
  workCenter: string;
  scheduledStart: Date;
  scheduledEnd: Date;
  setupTime: number;
  runTime: number;
  queueTime: number;
  moveTime: number;
}

// Forward scheduling implementation
async function forwardSchedule(
  workOrder: WorkOrder,
  startDate: Date
): Promise<Schedule> {
  const operations: OperationSchedule[] = [];
  let currentTime = startDate;

  for (const op of workOrder.routing) {
    const workCenter = await getWorkCenter(op.workCenter);
    const availability = await getAvailability(workCenter, currentTime);

    // Queue time
    const queueEnd = addTime(currentTime, op.queueTime);

    // Find available slot
    const setupStart = findNextSlot(availability, queueEnd, op.setupTime + op.runTime);

    // Setup
    const setupEnd = addTime(setupStart, op.setupTime);

    // Run
    const runEnd = addTime(setupEnd, op.runTime * workOrder.quantity.ordered);

    // Move time
    const moveEnd = addTime(runEnd, op.moveTime);

    operations.push({
      operationNumber: op.operationNumber,
      workCenter: op.workCenter,
      scheduledStart: setupStart,
      scheduledEnd: runEnd,
      setupTime: op.setupTime,
      runTime: op.runTime * workOrder.quantity.ordered,
      queueTime: op.queueTime,
      moveTime: op.moveTime
    });

    currentTime = moveEnd;
  }

  return {
    workOrderId: workOrder.id,
    operations,
    totalLeadTime: calculateLeadTime(operations),
    criticalPath: findCriticalPath(operations)
  };
}
```

## Production Reporting Pattern

```typescript
interface ProductionReportingService {
  reportProduction(report: ProductionReport): Promise<void>;
  backflush(workOrderId: string, quantity: number): Promise<void>;
}

interface ProductionReport {
  workOrderId: string;
  operationNumber: number;

  // Quantities
  quantityGood: number;
  quantityScrapped: number;
  quantityRework: number;

  // Time
  setupTime: number;
  runTime: number;
  downtime: number;

  // Resources
  operatorId: string;
  machineId?: string;

  // Traceability
  lotNumber?: string;
  serialNumbers?: string[];

  // Materials consumed
  materialsUsed?: MaterialUsage[];
}

interface MaterialUsage {
  materialId: string;
  quantity: number;
  lotNumber?: string;
}

// Implementation
async function reportProduction(report: ProductionReport): Promise<void> {
  const workOrder = await getWorkOrder(report.workOrderId);
  const operation = workOrder.routing.find(
    op => op.operationNumber === report.operationNumber
  );

  // Validate
  if (operation.status === 'completed') {
    throw new Error('Operation already completed');
  }

  // Update quantities
  workOrder.quantity.produced += report.quantityGood;
  workOrder.quantity.scrapped += report.quantityScrapped;

  // Record material consumption
  if (report.materialsUsed) {
    for (const usage of report.materialsUsed) {
      await consumeMaterial(usage);
    }
  } else {
    // Backflush based on BOM
    await backflushMaterials(workOrder, report.quantityGood);
  }

  // Update operation status
  if (workOrder.quantity.produced >= workOrder.quantity.ordered) {
    operation.status = 'completed';
  }

  // Record labor and machine time
  await recordTime({
    workOrderId: report.workOrderId,
    operationNumber: report.operationNumber,
    laborHours: report.setupTime + report.runTime,
    machineHours: report.runTime,
    operatorId: report.operatorId,
    machineId: report.machineId
  });

  // Create lot/serial records
  if (report.lotNumber || report.serialNumbers) {
    await createTraceabilityRecords(report);
  }

  await saveWorkOrder(workOrder);

  // Emit event
  await emit('production.reported', report);
}
```

## Capacity Planning Pattern

```typescript
interface CapacityPlanningService {
  calculateLoad(
    workCenter: string,
    dateRange: DateRange
  ): Promise<CapacityLoad>;

  findBottlenecks(
    workOrders: WorkOrder[]
  ): Promise<Bottleneck[]>;
}

interface CapacityLoad {
  workCenter: string;
  periods: LoadPeriod[];
  utilizationPercent: number;
}

interface LoadPeriod {
  date: Date;
  availableHours: number;
  plannedHours: number;
  loadPercent: number;
  workOrders: string[];
}

interface Bottleneck {
  workCenter: string;
  period: Date;
  overloadHours: number;
  affectedWorkOrders: string[];
  suggestions: string[];
}

// Implementation
async function calculateLoad(
  workCenterId: string,
  dateRange: DateRange
): Promise<CapacityLoad> {
  const workCenter = await getWorkCenter(workCenterId);
  const calendar = await getWorkCalendar(workCenter);
  const workOrders = await getScheduledWorkOrders(workCenterId, dateRange);

  const periods: LoadPeriod[] = [];
  let totalAvailable = 0;
  let totalPlanned = 0;

  for (const date of eachDay(dateRange)) {
    const availableHours = calendar.getAvailableHours(date);
    const plannedHours = calculatePlannedHours(workOrders, date);

    periods.push({
      date,
      availableHours,
      plannedHours,
      loadPercent: (plannedHours / availableHours) * 100,
      workOrders: getWorkOrdersForDate(workOrders, date)
    });

    totalAvailable += availableHours;
    totalPlanned += plannedHours;
  }

  return {
    workCenter: workCenterId,
    periods,
    utilizationPercent: (totalPlanned / totalAvailable) * 100
  };
}
```

## Shop Floor Data Collection

```typescript
interface DataCollectionService {
  recordMachineData(data: MachineData): Promise<void>;
  recordOperatorAction(action: OperatorAction): Promise<void>;
}

interface MachineData {
  equipmentId: string;
  timestamp: Date;
  signals: {
    name: string;
    value: number | boolean | string;
    unit?: string;
  }[];
}

interface OperatorAction {
  operatorId: string;
  workOrderId: string;
  action: 'clock_on' | 'clock_off' | 'start_setup' | 'end_setup' | 'report_downtime';
  timestamp: Date;
  details?: Record<string, any>;
}

// Real-time data collection
class MachineDataCollector {
  private buffer: MachineData[] = [];
  private flushInterval = 1000; // 1 second

  async collect(data: MachineData): Promise<void> {
    this.buffer.push(data);

    // Immediate alerts for critical values
    if (this.isCritical(data)) {
      await this.alertMaintenance(data);
    }
  }

  private async flush(): Promise<void> {
    if (this.buffer.length === 0) return;

    const batch = this.buffer.splice(0);
    await this.storeBatch(batch);
    await this.updateOEE(batch);
  }

  private isCritical(data: MachineData): boolean {
    return data.signals.some(s =>
      s.name === 'temperature' && s.value > 100 ||
      s.name === 'vibration' && s.value > 50
    );
  }
}
```
