# Booking Flow Template

## Booking Journey

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Search    │────▶│   Select    │────▶│   Details   │────▶│   Payment   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Destination         View options        Guest info         Process payment
  Dates               Compare prices      Add-ons            Confirm booking
  Guests              Hold room           Special requests   Send confirmation
```

## Booking States

```typescript
type BookingStatus =
  | 'searching'
  | 'selected'
  | 'hold'
  | 'pending_payment'
  | 'confirmed'
  | 'modified'
  | 'cancelled'
  | 'checked_in'
  | 'checked_out'
  | 'no_show';
```

## Search & Availability

```typescript
interface SearchCriteria {
  destination: string;
  checkIn: Date;
  checkOut: Date;
  rooms: number;
  adults: number;
  children?: number;
  childAges?: number[];
  filters?: SearchFilters;
}

interface SearchResult {
  property: Property;
  roomTypes: RoomAvailability[];
  lowestRate: Money;
  distance?: number;
  rating?: number;
}

interface RoomAvailability {
  roomTypeId: string;
  roomTypeName: string;
  available: number;
  rates: RateOption[];
  images: string[];
  amenities: string[];
}
```

## Booking Request

```typescript
interface BookingRequest {
  propertyId: string;
  roomTypeId: string;
  rateCode: string;
  checkIn: Date;
  checkOut: Date;

  // Guest
  guest: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
  };

  // Rooms
  rooms: {
    adults: number;
    children?: number;
    childAges?: number[];
  }[];

  // Add-ons
  addOns?: {
    id: string;
    quantity: number;
  }[];

  // Special requests
  specialRequests?: string;
  arrivalTime?: string;

  // Payment
  paymentMethod: PaymentMethod;
}
```

## Confirmation

```typescript
interface BookingConfirmation {
  bookingNumber: string;
  status: 'confirmed';

  // Details
  property: PropertySummary;
  roomType: string;
  checkIn: Date;
  checkOut: Date;
  nights: number;

  // Guest
  guestName: string;

  // Pricing
  total: Money;
  paymentStatus: string;

  // Policies
  cancellationPolicy: string;
  checkInTime: string;
  checkOutTime: string;

  // Actions
  manageBookingUrl: string;
  addToCalendarUrl: string;
}
```
