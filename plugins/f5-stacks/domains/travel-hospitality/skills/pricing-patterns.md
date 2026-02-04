# Pricing Patterns

## Overview
Design patterns for dynamic pricing and revenue management in travel.

## Key Patterns

### Pattern 1: Dynamic Pricing
```typescript
class DynamicPricingEngine {
  async calculatePrice(
    propertyId: string,
    roomTypeId: string,
    date: Date
  ): Promise<Money> {
    const baseRate = await this.getBaseRate(propertyId, roomTypeId, date);
    const factors = await this.getPricingFactors(propertyId, date);

    let adjustedRate = baseRate;

    // Occupancy factor
    adjustedRate *= factors.occupancyMultiplier;

    // Day of week factor
    adjustedRate *= factors.dayOfWeekMultiplier;

    // Seasonality factor
    adjustedRate *= factors.seasonalityMultiplier;

    // Competitor factor
    adjustedRate *= factors.competitorMultiplier;

    // Event factor
    adjustedRate *= factors.eventMultiplier;

    // Apply min/max bounds
    return this.applyBounds(adjustedRate, propertyId, roomTypeId);
  }
}
```

### Pattern 2: Length of Stay Pricing
```typescript
interface LOSPricing {
  baseRate: Money;
  discounts: {
    minNights: number;
    discountPercent: number;
  }[];
}

const calculateLOSRate = (losPricing: LOSPricing, nights: number): Money => {
  const applicable = losPricing.discounts
    .filter(d => nights >= d.minNights)
    .sort((a, b) => b.minNights - a.minNights)[0];

  if (applicable) {
    return {
      amount: losPricing.baseRate.amount * (1 - applicable.discountPercent / 100),
      currency: losPricing.baseRate.currency
    };
  }

  return losPricing.baseRate;
};
```

### Pattern 3: Yield Management
```typescript
interface YieldManagement {
  getRecommendedRate(
    propertyId: string,
    date: Date,
    currentOccupancy: number
  ): Promise<RateRecommendation>;
}

class YieldManager implements YieldManagement {
  async getRecommendedRate(
    propertyId: string,
    date: Date,
    currentOccupancy: number
  ): Promise<RateRecommendation> {
    const forecast = await this.demandForecast.predict(propertyId, date);
    const compset = await this.compsetAnalysis.getRates(propertyId, date);

    // Calculate optimal rate based on demand and competition
    const optimalRate = this.optimizationModel.calculate({
      demandForecast: forecast,
      competitorRates: compset,
      currentOccupancy,
      targetOccupancy: 0.85
    });

    return {
      recommendedRate: optimalRate,
      confidence: forecast.confidence,
      reasoning: this.generateReasoning(forecast, compset, optimalRate)
    };
  }
}
```

## Best Practices
- Implement rate parity monitoring
- Use demand forecasting
- Cache competitor rates
- A/B test pricing strategies
