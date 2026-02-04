---
id: travel-inventory-designer
name: Inventory Management Designer
tier: 2
domain: travel-hospitality
triggers:
  - inventory management
  - room availability
  - rate management
capabilities:
  - Real-time inventory tracking
  - Overbooking management
  - Rate and availability
  - Channel synchronization
---

# Inventory Management Designer

## Role
Specialist in designing travel inventory systems for managing rooms, seats, and availability.

## Design Patterns

### Inventory Model
```typescript
interface Inventory {
  propertyId: string;
  roomTypeId: string;
  date: Date;

  // Availability
  totalRooms: number;
  soldRooms: number;
  blockedRooms: number;
  availableRooms: number;

  // Overbooking
  overbookingAllowed: boolean;
  overbookingLimit: number;

  // Rates
  rates: RoomRate[];

  // Restrictions
  restrictions: {
    minStay?: number;
    maxStay?: number;
    closedToArrival?: boolean;
    closedToDeparture?: boolean;
  };
}

interface RoomRate {
  rateCode: string;
  rateName: string;
  price: Money;
  mealPlan?: string;
  cancellationPolicy: string;
  prepayment: 'full' | 'deposit' | 'none';
}
```

### Inventory Service
```typescript
interface InventoryService {
  getAvailability(propertyId: string, dates: DateRange): Promise<Inventory[]>;
  updateInventory(propertyId: string, date: Date, changes: InventoryUpdate): Promise<void>;
  reserveRoom(propertyId: string, roomTypeId: string, dates: DateRange): Promise<ReservationHold>;
  releaseHold(holdId: string): Promise<void>;
  syncChannels(propertyId: string): Promise<SyncResult>;
}

// Optimistic locking for concurrent bookings
interface ReservationHold {
  id: string;
  propertyId: string;
  roomTypeId: string;
  dates: DateRange;
  expiresAt: Date;
  status: 'active' | 'converted' | 'expired' | 'released';
}
```

## Quality Gates
- D1: Availability accuracy
- D2: Channel sync reliability
- D3: Overbooking control
