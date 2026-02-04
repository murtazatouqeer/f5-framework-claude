# Production Workflow Template

## Production Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Plan      │────▶│   Release   │────▶│   Execute   │────▶│   Complete  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Schedule           Check materials      Track progress      Quality check
  Allocate resources Issue work order    Report production   Close order
  Capacity plan      Reserve capacity    Handle exceptions   Update inventory
```

## Work Order States

```typescript
type WorkOrderStatus =
  | 'draft'
  | 'planned'
  | 'released'
  | 'material_staged'
  | 'started'
  | 'in_progress'
  | 'on_hold'
  | 'completed'
  | 'closed'
  | 'cancelled';
```

## Bill of Materials

```typescript
interface BillOfMaterials {
  productId: string;
  revision: string;
  effectiveDate: Date;

  components: BOMComponent[];
}

interface BOMComponent {
  materialId: string;
  materialName: string;
  quantity: number;
  unit: string;
  scrapFactor: number;
  position: number;
  isPhantom: boolean;
  alternatives?: string[];
}
```

## Routing

```typescript
interface ProductRouting {
  productId: string;
  revision: string;

  operations: Operation[];
}

interface Operation {
  operationNumber: number;
  name: string;
  workCenter: string;

  // Time
  setupTime: number;
  runTimePerUnit: number;
  moveTime: number;
  queueTime: number;

  // Resources
  tooling?: string[];
  skills?: string[];
  instructions?: string;

  // Quality
  inspectionRequired: boolean;
  inspectionPlanId?: string;
}
```

## Production Tracking

```typescript
interface ProductionTransaction {
  id: string;
  workOrderId: string;
  operationNumber: number;

  // Quantity
  quantityProduced: number;
  quantityScrapped: number;
  quantityRework: number;

  // Time
  startTime: Date;
  endTime: Date;
  laborHours: number;
  machineHours: number;

  // Resources
  operatorId: string;
  machineId?: string;

  // Lot/Serial
  lotNumber?: string;
  serialNumbers?: string[];
}
```
