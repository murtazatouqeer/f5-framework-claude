# Inventory Management Template

## Room Inventory Structure

```typescript
interface RoomInventory {
  propertyId: string;
  roomTypeId: string;
  date: Date;

  // Physical inventory
  physical: {
    total: number;
    outOfOrder: number;
    outOfService: number;
  };

  // Sellable
  sellable: {
    available: number;
    sold: number;
    blocked: number;
    held: number;
  };

  // Overbooking
  overbooking: {
    enabled: boolean;
    limit: number;
    current: number;
  };

  // By channel
  channelAllocation: {
    [channel: string]: {
      allocated: number;
      sold: number;
    };
  };
}
```

## Rate Management

```typescript
interface RateCalendar {
  propertyId: string;
  roomTypeId: string;
  rateCode: string;

  // Daily rates
  dailyRates: {
    date: Date;
    price: Money;
    restrictions: RateRestrictions;
  }[];
}

interface RateRestrictions {
  minStay?: number;
  maxStay?: number;
  minAdvanceBooking?: number;
  maxAdvanceBooking?: number;
  closedToArrival?: boolean;
  closedToDeparture?: boolean;
  stopSell?: boolean;
}
```

## Channel Management

```typescript
interface ChannelManager {
  syncAvailability(propertyId: string, dates: DateRange): Promise<void>;
  syncRates(propertyId: string, rateChanges: RateChange[]): Promise<void>;
  processBooking(channelBooking: ChannelBooking): Promise<Booking>;
  sendConfirmation(bookingId: string, channel: string): Promise<void>;
}

interface ChannelConnection {
  channel: string; // 'booking.com', 'expedia', 'airbnb'
  propertyId: string;
  channelPropertyId: string;
  roomMappings: RoomMapping[];
  rateMappings: RateMapping[];
  status: 'active' | 'paused' | 'error';
}
```

## Revenue Management

```typescript
interface RevenueManagement {
  // Dynamic pricing
  calculateDynamicRate(
    propertyId: string,
    roomTypeId: string,
    date: Date
  ): Promise<Money>;

  // Forecasting
  getForecast(
    propertyId: string,
    dates: DateRange
  ): Promise<DemandForecast>;

  // Recommendations
  getPricingRecommendations(
    propertyId: string
  ): Promise<PricingRecommendation[]>;
}

interface DemandForecast {
  date: Date;
  predictedOccupancy: number;
  demandLevel: 'low' | 'medium' | 'high' | 'peak';
  recommendedRate: Money;
  confidence: number;
}
```
