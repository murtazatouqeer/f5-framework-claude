# Warehouse Flow Template

## Receiving Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Arrival   │────▶│  Unloading  │────▶│  Inspection │────▶│   Putaway   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Create ASN         Dock assignment      Quality check      Bin assignment
  Schedule dock      Pallet count         Quantity verify    Location update
                                          Damage check       Inventory +
```

## Picking Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Order Wave  │────▶│   Picking   │────▶│   Packing   │────▶│  Shipping   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Wave planning       Pick task          Pack station       Label print
  Route optimize      Scan verify        QC check           Manifest
  Task assignment     Inventory -        Box selection      Carrier handoff
```

## Picking Strategies

### Wave Picking
```typescript
interface WavePicking {
  waveId: string;
  orders: Order[];
  pickTasks: PickTask[];
  scheduledTime: Date;
  cutoffTime: Date;

  // Group orders by:
  groupBy: 'carrier' | 'zone' | 'priority' | 'ship_date';
}
```

### Batch Picking
```typescript
interface BatchPicking {
  batchId: string;
  items: BatchItem[]; // Grouped by SKU
  picker: string;
  cart: string;

  // Single trip, multiple orders
  consolidateBy: 'sku' | 'location';
}
```

### Zone Picking
```typescript
interface ZonePicking {
  zones: PickZone[];
  handoffPoints: Location[];

  // Order passes through zones
  flow: 'sequential' | 'parallel';
}
```

## Location Structure

```typescript
interface WarehouseLocation {
  // Format: WH-AA-01-02-A
  warehouse: string;  // WH
  aisle: string;      // AA
  rack: string;       // 01
  shelf: string;      // 02
  position: string;   // A

  // Properties
  type: 'rack' | 'shelf' | 'floor' | 'bulk';
  capacity: number;
  restrictions: string[]; // cold, hazmat, fragile
  pickSequence: number;
}
```

## Inventory Transactions

| Transaction | From Status | To Status | Inventory Change |
|-------------|-------------|-----------|------------------|
| Receive | N/A | Available | + |
| Putaway | Available | Available | Location change |
| Pick | Available | Picked | - |
| Pack | Picked | Packed | Status change |
| Ship | Packed | Shipped | Status change |
| Adjust + | N/A | Available | + |
| Adjust - | Available | N/A | - |
| Transfer | Location A | Location B | Location change |
