---
name: cold-chain-flow
category: agriculture/shared
description: Cold chain logistics flow for livestock marketplace
version: "1.0"
---

# Cold Chain Logistics Flow

## Overview

Cold chain management is critical for livestock marketplace operations. This
document covers live animal transport, post-slaughter cold chain, and IoT
monitoring integration.

## Cold Chain Stages

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COLD CHAIN FLOW                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  LIVE ANIMAL PHASE                    POST-SLAUGHTER PHASE              │
│  ─────────────────                    ────────────────────              │
│                                                                          │
│  ┌─────────┐     ┌─────────┐     ┌──────────┐     ┌─────────┐          │
│  │  FARM   │────▶│TRANSPORT│────▶│   HUB    │────▶│SLAUGHTER│          │
│  │         │     │(Live)   │     │(Holding) │     │  HOUSE  │          │
│  └─────────┘     └─────────┘     └──────────┘     └─────────┘          │
│       │               │               │               │                  │
│       │               │               │               │                  │
│       ▼               ▼               ▼               ▼                  │
│   [Health OK]    [Ventilated]    [Temp Hold]    [0-4°C Start]          │
│   [Documents]    [Welfare OK]    [Inspection]   [Grading]              │
│                                                                          │
│                                        │                                 │
│                                        ▼                                 │
│                                                                          │
│  ┌─────────┐     ┌─────────┐     ┌──────────┐     ┌─────────┐          │
│  │CUSTOMER │◀────│LAST MILE│◀────│COLD STOR.│◀────│TRANSPORT│          │
│  │         │     │(Insul.) │     │(0-4°C)   │     │(0-4°C)  │          │
│  └─────────┘     └─────────┘     └──────────┘     └─────────┘          │
│       │               │               │               │                  │
│       │               │               │               │                  │
│       ▼               ▼               ▼               ▼                  │
│   [Verify OK]    [Time Limit]    [FIFO]       [Monitored]              │
│   [Sign Off]     [< 2 hours]     [Tracking]   [Continuous]             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Temperature Requirements

### By Product Type

| Stage | Live Animals | Fresh Meat | Frozen Meat | Processed |
|-------|-------------|------------|-------------|-----------|
| Transport | Ventilated (ambient) | 0-4°C | -18°C | 0-4°C |
| Storage | N/A | 0-4°C | -18°C to -20°C | 0-4°C |
| Max Duration | 8 hours | 5 days | 12 months | 7 days |
| Critical Alert | > 35°C | > 7°C | > -15°C | > 7°C |

### Temperature Monitoring

```typescript
interface TemperatureConfig {
  productType: ProductType;
  normalRange: { min: number; max: number };
  warningRange: { min: number; max: number };
  criticalThreshold: number;
  samplingInterval: number;  // seconds
  alertCooldown: number;     // seconds between alerts
}

const temperatureConfigs: Record<ProductType, TemperatureConfig> = {
  live_animal: {
    productType: 'live_animal',
    normalRange: { min: 15, max: 30 },
    warningRange: { min: 10, max: 35 },
    criticalThreshold: 38,
    samplingInterval: 60,
    alertCooldown: 300,
  },
  fresh_meat: {
    productType: 'fresh_meat',
    normalRange: { min: 0, max: 4 },
    warningRange: { min: -2, max: 6 },
    criticalThreshold: 7,
    samplingInterval: 30,
    alertCooldown: 180,
  },
  frozen_meat: {
    productType: 'frozen_meat',
    normalRange: { min: -20, max: -16 },
    warningRange: { min: -22, max: -14 },
    criticalThreshold: -12,
    samplingInterval: 60,
    alertCooldown: 300,
  },
};
```

## Live Animal Transport

### Welfare Requirements

```
┌─────────────────────────────────────────────────────────────────┐
│                 LIVE ANIMAL TRANSPORT CHECKLIST                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pre-Transport:                                                 │
│  □ Health inspection completed (< 24 hours)                     │
│  □ Animals fit for transport (not sick, not pregnant near term) │
│  □ Fasting period observed (cattle: 12h, pigs: 6h)              │
│  □ Vehicle inspection passed                                    │
│  □ Driver certified for livestock transport                     │
│                                                                  │
│  Vehicle Requirements:                                          │
│  □ Adequate ventilation                                         │
│  □ Non-slip flooring                                            │
│  □ Loading ramp with proper gradient                            │
│  □ Separation barriers for different species/sizes              │
│  □ Water access for journeys > 4 hours                          │
│                                                                  │
│  During Transport:                                              │
│  □ Maximum journey time: 8 hours without rest                   │
│  □ Rest stop every 4 hours for long journeys                    │
│  □ Temperature monitoring                                        │
│  □ No mixing of incompatible animals                            │
│                                                                  │
│  Loading Density (per m²):                                      │
│  ├── Cattle (500kg): 1.3-1.5 m²                                │
│  ├── Pigs (100kg): 0.42-0.55 m²                                │
│  ├── Sheep (40kg): 0.2-0.3 m²                                   │
│  └── Poultry: containers with adequate space                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Transport Workflow

```typescript
interface LiveTransportJob {
  id: string;
  orderId: string;
  status: TransportStatus;

  // Pickup
  pickupFarm: Farm;
  pickupTime: Date;
  loadingInspector?: string;

  // Animals
  animalCount: number;
  animalType: AnimalType;
  totalWeight: number;

  // Vehicle
  vehicleId: string;
  driverId: string;
  capacity: number;

  // Route
  estimatedDuration: number;
  plannedStops: RestStop[];

  // Delivery
  destination: Hub | Slaughterhouse;
  estimatedArrival: Date;
  actualArrival?: Date;

  // Monitoring
  gpsTrackerId: string;
  temperatureDeviceId?: string;
  welfareChecks: WelfareCheck[];
}

type TransportStatus =
  | 'scheduled'
  | 'driver_assigned'
  | 'en_route_to_farm'
  | 'at_farm'
  | 'loading'
  | 'in_transit'
  | 'at_rest_stop'
  | 'arrived'
  | 'unloading'
  | 'completed'
  | 'incident';

interface WelfareCheck {
  timestamp: Date;
  location: GeoPoint;
  animalStatus: 'good' | 'stressed' | 'injured' | 'deceased';
  temperature: number;
  notes?: string;
  photos?: string[];
}
```

## Cold Storage Operations

### Storage Management

```typescript
interface ColdStorageFacility {
  id: string;
  name: string;
  location: Address;

  // Capacity
  zones: StorageZone[];
  totalCapacity: number;
  currentOccupancy: number;

  // Operations
  operatingHours: OperatingHours;
  certifications: string[];
}

interface StorageZone {
  id: string;
  name: string;
  temperatureRange: { min: number; max: number };
  humidity: { min: number; max: number };
  capacity: number;
  productTypes: ProductType[];

  // Monitoring
  sensors: TemperatureSensor[];
  lastReading: SensorReading;
}

// FIFO Inventory Management
interface InventoryItem {
  id: string;
  productId: string;
  zoneId: string;

  // Tracking
  receivedAt: Date;
  expiresAt: Date;
  sourceOrderId: string;

  // Quantity
  quantity: number;
  unit: 'kg' | 'piece' | 'box';

  // FIFO position
  fifoOrder: number;
}

// Pick items using FIFO
async function pickItems(
  productId: string,
  quantity: number
): Promise<InventoryItem[]> {
  const items = await InventoryItem.find({
    productId,
    quantity: { $gt: 0 },
  }).sort({ fifoOrder: 1 });  // Oldest first

  let remaining = quantity;
  const picks: InventoryItem[] = [];

  for (const item of items) {
    if (remaining <= 0) break;

    const pickQty = Math.min(remaining, item.quantity);
    await item.decrement('quantity', pickQty);

    picks.push({ ...item, quantity: pickQty });
    remaining -= pickQty;
  }

  if (remaining > 0) {
    throw new InsufficientInventoryError(productId, quantity);
  }

  return picks;
}
```

## IoT Integration

### Sensor Network

```typescript
interface IoTDevice {
  id: string;
  type: 'temperature' | 'humidity' | 'gps' | 'door';
  status: 'active' | 'offline' | 'low_battery';

  // Assignment
  assignedTo: {
    type: 'vehicle' | 'container' | 'zone';
    id: string;
  };

  // Configuration
  reportingInterval: number;  // seconds
  alertThresholds: Record<string, number>;

  // Last reading
  lastReading: DeviceReading;
  lastSeen: Date;
}

interface DeviceReading {
  deviceId: string;
  timestamp: Date;
  values: {
    temperature?: number;
    humidity?: number;
    location?: GeoPoint;
    doorOpen?: boolean;
    batteryLevel?: number;
  };
}

// Real-time monitoring
class ColdChainMonitor {
  private alerts: Map<string, Alert> = new Map();

  async processReading(reading: DeviceReading): Promise<void> {
    const device = await getDevice(reading.deviceId);
    const config = getConfigForDevice(device);

    // Check temperature
    if (reading.values.temperature !== undefined) {
      await this.checkTemperature(
        reading.deviceId,
        reading.values.temperature,
        config.temperatureConfig
      );
    }

    // Check for door open too long
    if (reading.values.doorOpen) {
      await this.checkDoorStatus(reading.deviceId, device);
    }

    // Store reading
    await storeReading(reading);

    // Broadcast to dashboard
    await broadcastReading(reading);
  }

  private async checkTemperature(
    deviceId: string,
    temp: number,
    config: TemperatureConfig
  ): Promise<void> {
    let severity: 'normal' | 'warning' | 'critical';

    if (temp >= config.normalRange.min && temp <= config.normalRange.max) {
      severity = 'normal';
    } else if (temp >= config.warningRange.min && temp <= config.warningRange.max) {
      severity = 'warning';
    } else {
      severity = 'critical';
    }

    if (severity !== 'normal') {
      await this.raiseAlert(deviceId, 'temperature', severity, {
        current: temp,
        expected: config.normalRange,
      });
    }
  }

  private async raiseAlert(
    deviceId: string,
    type: string,
    severity: string,
    details: any
  ): Promise<void> {
    const alertKey = `${deviceId}-${type}`;
    const existingAlert = this.alerts.get(alertKey);

    // Respect cooldown
    if (existingAlert) {
      const elapsed = Date.now() - existingAlert.createdAt.getTime();
      if (elapsed < existingAlert.cooldown * 1000) {
        return;  // Still in cooldown
      }
    }

    const alert = await createAlert({
      deviceId,
      type,
      severity,
      details,
    });

    this.alerts.set(alertKey, alert);

    // Notify stakeholders
    await notifyAlertRecipients(alert);
  }
}
```

### Dashboard Integration

```typescript
interface ColdChainDashboard {
  // Real-time shipment tracking
  activeShipments: ShipmentStatus[];

  // Temperature monitoring
  temperatureReadings: {
    shipmentId: string;
    current: number;
    history: TemperatureReading[];
    alerts: Alert[];
  }[];

  // Hub status
  hubStatus: {
    hubId: string;
    occupancy: number;
    capacity: number;
    zoneTemperatures: Record<string, number>;
  }[];

  // Alerts summary
  alertsSummary: {
    critical: number;
    warning: number;
    resolved: number;
  };
}

// WebSocket events
interface DashboardEvents {
  // Shipment updates
  'shipment:location': { shipmentId: string; location: GeoPoint };
  'shipment:status': { shipmentId: string; status: string };

  // Temperature updates
  'temperature:reading': { deviceId: string; temperature: number };
  'temperature:alert': Alert;

  // Hub updates
  'hub:occupancy': { hubId: string; occupancy: number };
  'hub:zone-temp': { hubId: string; zoneId: string; temperature: number };
}
```

## Quality Checkpoints

### Checkpoint Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUALITY CHECKPOINTS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CP1: FARM GATE                                                 │
│  ────────────────                                               │
│  □ Health certificate valid                                     │
│  □ Animal count matches order                                   │
│  □ Weight within tolerance (±5%)                                │
│  □ Visual health inspection pass                                │
│  □ Documentation complete                                       │
│  → RESULT: Green/Yellow/Red flag                                │
│                                                                  │
│  CP2: HUB ARRIVAL                                               │
│  ───────────────                                                │
│  □ Transport duration within limit                              │
│  □ Animal condition on arrival                                  │
│  □ Count verification                                           │
│  □ Re-weigh (if applicable)                                     │
│  → RESULT: Accept/Hold/Reject                                   │
│                                                                  │
│  CP3: PRE-SLAUGHTER                                             │
│  ─────────────────                                              │
│  □ Rest period completed (if required)                          │
│  □ Veterinary inspection                                        │
│  □ Fitness for slaughter                                        │
│  □ Final weight record                                          │
│  → RESULT: Approved/Deferred/Condemned                          │
│                                                                  │
│  CP4: POST-SLAUGHTER                                            │
│  ──────────────────                                             │
│  □ Carcass inspection                                           │
│  □ Disease indicators                                           │
│  □ Quality grading (A/B/C)                                      │
│  □ Yield calculation                                            │
│  → RESULT: Grade assigned, traceability updated                 │
│                                                                  │
│  CP5: COLD STORAGE ENTRY                                        │
│  ───────────────────────                                        │
│  □ Temperature verification                                     │
│  □ Packaging integrity                                          │
│  □ Labeling complete                                            │
│  □ FIFO assignment                                              │
│  → RESULT: Accepted into inventory                              │
│                                                                  │
│  CP6: DISPATCH                                                  │
│  ────────────                                                   │
│  □ Order verification                                           │
│  □ Temperature log reviewed                                     │
│  □ Best-before date valid                                       │
│  □ Vehicle pre-cooled                                           │
│  → RESULT: Cleared for dispatch                                 │
│                                                                  │
│  CP7: CUSTOMER DELIVERY                                         │
│  ─────────────────────                                          │
│  □ Temperature on arrival                                       │
│  □ Visual inspection                                            │
│  □ Quantity match                                               │
│  □ Customer acceptance                                          │
│  → RESULT: Delivery confirmed                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Checkpoint Implementation

```typescript
interface QualityCheckpoint {
  id: string;
  orderId: string;
  checkpoint: CheckpointType;
  timestamp: Date;

  // Inspector
  inspectorId: string;
  inspectorName: string;

  // Results
  checks: CheckResult[];
  overallResult: 'pass' | 'conditional' | 'fail';

  // Evidence
  photos: string[];
  notes: string;

  // Actions
  followUpRequired: boolean;
  followUpActions?: string[];
}

interface CheckResult {
  checkId: string;
  checkName: string;
  passed: boolean;
  value?: any;           // Measured value
  expectedValue?: any;   // Expected value
  deviation?: number;    // Percentage deviation
  notes?: string;
}

// Perform checkpoint
async function performCheckpoint(
  orderId: string,
  checkpoint: CheckpointType,
  inspectorId: string,
  results: CheckResult[],
  evidence: { photos: string[]; notes: string }
): Promise<QualityCheckpoint> {
  // Determine overall result
  const failedCritical = results.some(r =>
    !r.passed && isCriticalCheck(r.checkId)
  );
  const failedNonCritical = results.some(r =>
    !r.passed && !isCriticalCheck(r.checkId)
  );

  let overallResult: 'pass' | 'conditional' | 'fail';
  if (failedCritical) {
    overallResult = 'fail';
  } else if (failedNonCritical) {
    overallResult = 'conditional';
  } else {
    overallResult = 'pass';
  }

  const record = await createCheckpoint({
    orderId,
    checkpoint,
    inspectorId,
    checks: results,
    overallResult,
    photos: evidence.photos,
    notes: evidence.notes,
    followUpRequired: overallResult !== 'pass',
  });

  // Trigger workflow
  if (overallResult === 'fail') {
    await handleCheckpointFailure(record);
  }

  return record;
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│               COLD CHAIN BEST PRACTICES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Temperature Management:                                        │
│  □ Continuous monitoring with IoT sensors                       │
│  □ Immediate alerts for temperature breaches                    │
│  □ Pre-cool vehicles before loading                             │
│  □ Document temperature at every handoff                        │
│                                                                  │
│  Traceability:                                                  │
│  □ Unique ID for each animal/batch                              │
│  □ QR codes for quick scanning                                  │
│  □ Complete chain of custody                                    │
│  □ Timestamped photo evidence                                   │
│                                                                  │
│  Animal Welfare:                                                │
│  □ Certified transport vehicles                                 │
│  □ Maximum journey time enforcement                             │
│  □ Rest stops for long journeys                                 │
│  □ Proper loading/unloading facilities                          │
│                                                                  │
│  Quality Control:                                               │
│  □ Checkpoint at every stage                                    │
│  □ Clear pass/fail criteria                                     │
│  □ Qualified inspectors                                         │
│  □ Photo documentation                                          │
│                                                                  │
│  Compliance:                                                    │
│  □ HACCP standards                                              │
│  □ Vietnam food safety regulations                              │
│  □ Animal transport regulations                                 │
│  □ Complete audit trail                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
