# Booking Patterns

## Overview
Design patterns cho travel booking systems.

## Key Patterns

### Pattern 1: Inventory Hold
```typescript
class InventoryHoldService {
  async createHold(request: HoldRequest): Promise<Hold> {
    const available = await this.checkAvailability(request);
    if (!available) throw new Error('Not available');

    const hold = await this.holdRepository.create({
      ...request,
      expiresAt: new Date(Date.now() + 15 * 60 * 1000) // 15 minutes
    });

    await this.decrementAvailability(request);
    return hold;
  }

  async convertToBooking(holdId: string): Promise<Booking> {
    const hold = await this.holdRepository.findById(holdId);
    if (hold.status !== 'active' || hold.expiresAt < new Date()) {
      throw new Error('Hold expired');
    }

    const booking = await this.bookingService.create(hold);
    await this.holdRepository.update(holdId, { status: 'converted' });
    return booking;
  }

  async releaseExpiredHolds(): Promise<void> {
    const expired = await this.holdRepository.findExpired();
    for (const hold of expired) {
      await this.incrementAvailability(hold);
      await this.holdRepository.update(hold.id, { status: 'expired' });
    }
  }
}
```

### Pattern 2: Rate Shopping
```typescript
interface RateShoppingService {
  getBestRate(criteria: SearchCriteria): Promise<RateOption>;
  compareRates(propertyId: string, dates: DateRange): Promise<RateComparison[]>;
  applyPromoCode(rateId: string, promoCode: string): Promise<DiscountedRate>;
}

class RateEngine {
  async calculateRate(
    propertyId: string,
    roomTypeId: string,
    dates: DateRange,
    occupancy: Occupancy
  ): Promise<RateBreakdown> {
    const dailyRates = await this.getDailyRates(propertyId, roomTypeId, dates);
    const taxes = await this.calculateTaxes(dailyRates);
    const fees = await this.calculateFees(propertyId, dates);

    return {
      roomRate: this.sumRates(dailyRates),
      taxes,
      fees,
      total: this.sumAll(dailyRates, taxes, fees)
    };
  }
}
```

### Pattern 3: Booking Modification
```typescript
class BookingModificationService {
  async modifyDates(
    bookingId: string,
    newDates: DateRange
  ): Promise<ModificationResult> {
    const booking = await this.bookingRepository.findById(bookingId);

    // Check availability for new dates
    const available = await this.checkAvailability(booking, newDates);
    if (!available) throw new Error('New dates not available');

    // Calculate price difference
    const newRate = await this.rateEngine.calculateRate(booking, newDates);
    const priceDiff = newRate.total - booking.pricing.total;

    // Apply modification
    await this.bookingRepository.update(bookingId, { dates: newDates, pricing: newRate });

    // Handle payment adjustment
    if (priceDiff > 0) {
      await this.chargeAdditional(bookingId, priceDiff);
    } else if (priceDiff < 0) {
      await this.issueRefund(bookingId, Math.abs(priceDiff));
    }

    return { booking, priceDiff };
  }
}
```

## Best Practices
- Use optimistic locking for inventory
- Implement hold timeouts
- Cache availability data
- Handle partial cancellations
