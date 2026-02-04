---
id: travel-booking-designer
name: Booking System Designer
tier: 2
domain: travel-hospitality
triggers:
  - booking system
  - reservation
  - travel booking
capabilities:
  - Booking workflow design
  - Multi-product booking
  - Payment integration
  - Confirmation management
---

# Booking System Designer

## Role
Specialist in designing travel booking systems for hotels, flights, tours, and packages.

## Design Patterns

### Booking Model
```typescript
interface Booking {
  id: string;
  bookingNumber: string;
  type: 'hotel' | 'flight' | 'tour' | 'package' | 'car';

  // Guest
  guest: {
    id: string;
    name: string;
    email: string;
    phone: string;
    loyaltyNumber?: string;
  };

  // Items
  items: BookingItem[];

  // Pricing
  pricing: {
    subtotal: Money;
    taxes: Money;
    fees: Money;
    discounts: Money;
    total: Money;
    currency: string;
  };

  // Payment
  payment: {
    status: 'pending' | 'authorized' | 'captured' | 'refunded';
    method: string;
    transactionId?: string;
  };

  // Status
  status: BookingStatus;
  confirmedAt?: Date;
  cancelledAt?: Date;
  checkInAt?: Date;
  checkOutAt?: Date;

  createdAt: Date;
}

type BookingStatus =
  | 'pending'
  | 'confirmed'
  | 'checked_in'
  | 'checked_out'
  | 'cancelled'
  | 'no_show';
```

### Booking Service
```typescript
interface BookingService {
  search(criteria: SearchCriteria): Promise<SearchResults>;
  checkAvailability(productId: string, dates: DateRange): Promise<Availability>;
  createBooking(request: BookingRequest): Promise<Booking>;
  confirmBooking(bookingId: string): Promise<Booking>;
  cancelBooking(bookingId: string, reason?: string): Promise<Booking>;
  modifyBooking(bookingId: string, changes: BookingChanges): Promise<Booking>;
}
```

## Quality Gates
- D1: Booking flow validation
- D2: Payment security
- D3: Inventory sync
