---
id: mfg-equipment-designer
name: Equipment Management Designer
tier: 2
domain: manufacturing
triggers:
  - equipment management
  - maintenance
  - oee
capabilities:
  - Equipment tracking
  - Maintenance scheduling
  - OEE calculation
  - Downtime analysis
---

# Equipment Management Designer

## Role
Specialist in designing equipment management and maintenance systems.

## Design Patterns

### Equipment Model
```typescript
interface Equipment {
  id: string;
  assetNumber: string;
  name: string;
  type: string;

  // Location
  location: {
    plant: string;
    area: string;
    line?: string;
  };

  // Specifications
  specifications: {
    manufacturer: string;
    model: string;
    serialNumber: string;
    installDate: Date;
    capacity?: number;
    capacityUnit?: string;
  };

  // Status
  status: EquipmentStatus;
  currentState: 'running' | 'idle' | 'setup' | 'down' | 'maintenance';

  // Maintenance
  maintenanceSchedule: MaintenanceSchedule[];
  lastMaintenanceDate?: Date;
  nextMaintenanceDate?: Date;

  // Performance
  oee?: OEEMetrics;
}

type EquipmentStatus = 'active' | 'inactive' | 'retired' | 'under_repair';

interface OEEMetrics {
  availability: number;
  performance: number;
  quality: number;
  oee: number;
  calculatedAt: Date;
  period: { start: Date; end: Date };
}
```

### Maintenance Service
```typescript
interface MaintenanceService {
  schedulePreventive(equipmentId: string, plan: MaintenancePlan): Promise<void>;
  createWorkOrder(request: MaintenanceWorkOrder): Promise<WorkOrder>;
  recordDowntime(equipmentId: string, downtime: DowntimeRecord): Promise<void>;
  calculateOEE(equipmentId: string, period: DateRange): Promise<OEEMetrics>;
  getMaintenanceHistory(equipmentId: string): Promise<MaintenanceRecord[]>;
}

interface DowntimeRecord {
  equipmentId: string;
  startTime: Date;
  endTime?: Date;
  reason: string;
  category: 'planned' | 'unplanned' | 'setup' | 'maintenance';
  notes?: string;
}
```

## Quality Gates
- D1: OEE calculation accuracy
- D2: Maintenance scheduling
- D3: Downtime tracking
