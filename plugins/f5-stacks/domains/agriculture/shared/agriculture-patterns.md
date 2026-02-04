---
name: agriculture-patterns
category: agriculture/shared
description: Common patterns for livestock marketplace implementation
version: "1.0"
---

# Agriculture & Livestock Marketplace Patterns

## Overview

This document defines common architectural and implementation patterns for
livestock marketplace applications, covering auction systems, quality control,
cold chain logistics, and traceability.

## Core Domain Patterns

### 1. Multi-Party Marketplace

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MARKETPLACE ECOSYSTEM                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   SUPPLY SIDE                 PLATFORM                 DEMAND SIDE  │
│   ───────────                 ────────                 ───────────  │
│                                                                      │
│   ┌─────────┐              ┌───────────┐              ┌─────────┐  │
│   │ Farmers │◀────────────▶│ Matching  │◀────────────▶│ Traders │  │
│   └─────────┘              │  Engine   │              └─────────┘  │
│        │                   └───────────┘                    │       │
│        │                        │                           │       │
│   ┌─────────┐              ┌───────────┐              ┌─────────┐  │
│   │  Farms  │              │  Auction  │              │Slaughter│  │
│   └─────────┘              │  Engine   │              │ houses  │  │
│        │                   └───────────┘              └─────────┘  │
│        │                        │                           │       │
│        ▼                        ▼                           ▼       │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    LOGISTICS LAYER                           │  │
│   │    Hubs ◀──────▶ Transport ◀──────▶ Cold Chain              │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Trust & Verification Layers

```typescript
// Trust Score Computation Pattern
interface TrustScore {
  userId: string;
  components: {
    verification: number;      // Document verification (0-25)
    transactions: number;      // Transaction history (0-25)
    ratings: number;           // User ratings (0-25)
    disputes: number;          // Dispute penalty (-25 to 0)
  };
  total: number;              // 0-100
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
}

// Tier Benefits
const tierBenefits = {
  bronze: { maxTransaction: 50_000_000, commission: 0.05 },
  silver: { maxTransaction: 200_000_000, commission: 0.04 },
  gold: { maxTransaction: 500_000_000, commission: 0.03 },
  platinum: { maxTransaction: Infinity, commission: 0.025 },
};
```

### 3. Quality Grading System

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUALITY GRADING FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Farm Self-Assessment                                          │
│         │                                                        │
│         ▼                                                        │
│   ┌───────────┐     ┌───────────┐     ┌───────────┐            │
│   │ Pending   │────▶│ Inspector │────▶│  Graded   │            │
│   │ Inspection│     │  Assigned │     │           │            │
│   └───────────┘     └───────────┘     └───────────┘            │
│                           │                   │                  │
│                           ▼                   ▼                  │
│                     ┌───────────┐     ┌───────────────────┐     │
│                     │ On-Site   │     │ Grade Certificate │     │
│                     │ Inspection│     │ A/B/C/Rejected    │     │
│                     └───────────┘     └───────────────────┘     │
│                                                                  │
│   GRADE CRITERIA:                                               │
│   ┌──────┬──────────────────────────────────────────────────┐  │
│   │ A    │ Premium: VietGAP certified, optimal weight,      │  │
│   │      │ no health issues, proper age                     │  │
│   ├──────┼──────────────────────────────────────────────────┤  │
│   │ B    │ Standard: Meets basic requirements, minor        │  │
│   │      │ deviations from optimal                          │  │
│   ├──────┼──────────────────────────────────────────────────┤  │
│   │ C    │ Acceptable: Below standard but safe,             │  │
│   │      │ price reduction applies                          │  │
│   ├──────┼──────────────────────────────────────────────────┤  │
│   │ REJ  │ Rejected: Health issues, disease indicators,     │  │
│   │      │ not suitable for marketplace                     │  │
│   └──────┴──────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Transaction Patterns

### 4. Escrow Payment Pattern

```typescript
// Escrow State Machine
type EscrowState =
  | 'pending_deposit'    // Waiting for buyer deposit
  | 'deposited'          // Funds received
  | 'in_transit'         // Livestock being delivered
  | 'delivered'          // Awaiting confirmation
  | 'confirmed'          // Buyer confirmed receipt
  | 'released'           // Funds released to seller
  | 'disputed'           // Dispute raised
  | 'refunded';          // Refund processed

interface EscrowTransaction {
  id: string;
  orderId: string;
  amount: Money;
  state: EscrowState;

  buyerDeposit: Money;
  sellerReceivable: Money;
  platformFee: Money;

  releaseConditions: {
    deliveryConfirmed: boolean;
    qualityAccepted: boolean;
    disputeWindow: Date;
  };
}

// Release logic
async function releaseEscrow(escrow: EscrowTransaction): Promise<void> {
  if (escrow.state !== 'confirmed') {
    throw new Error('Cannot release: not confirmed');
  }

  if (new Date() < escrow.releaseConditions.disputeWindow) {
    throw new Error('Dispute window still open');
  }

  await transferFunds(escrow.sellerReceivable, escrow.seller);
  await transferFunds(escrow.platformFee, PLATFORM_ACCOUNT);
  await updateState(escrow, 'released');
}
```

### 5. Price Discovery Pattern

```typescript
// Multiple pricing mechanisms
interface PricingMechanism {
  type: 'fixed' | 'auction' | 'negotiation' | 'market_rate';

  // Fixed price
  fixedPrice?: Money;

  // Auction
  auction?: {
    startingBid: Money;
    reservePrice?: Money;
    buyNowPrice?: Money;
    bidIncrement: Money;
    duration: Duration;
  };

  // Negotiation
  negotiation?: {
    askingPrice: Money;
    minAcceptable: Money;
    maxRounds: number;
  };

  // Market rate
  marketRate?: {
    baseIndex: 'vn_livestock_index' | 'regional_price';
    adjustment: number; // percentage
  };
}
```

## Logistics Patterns

### 6. Hub-and-Spoke Distribution

```
┌─────────────────────────────────────────────────────────────────┐
│                    HUB-AND-SPOKE MODEL                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   FARMS                REGIONAL HUBS            DESTINATIONS    │
│   ─────                ────────────            ────────────     │
│                                                                  │
│   [Farm 1]──────┐                        ┌──────[Slaughterhouse]│
│                 │     ┌───────────┐      │                      │
│   [Farm 2]──────┼────▶│  Hub A    │◀─────┼──────[Slaughterhouse]│
│                 │     │ (Sorting) │      │                      │
│   [Farm 3]──────┘     └───────────┘      └──────[Market]        │
│                             │                                    │
│                             ▼                                    │
│                       ┌───────────┐                             │
│                       │ Central   │                             │
│                       │ Hub       │                             │
│                       │(Auction)  │                             │
│                       └───────────┘                             │
│                             │                                    │
│   [Farm 4]──────┐           │           ┌──────[Retailer]       │
│                 │     ┌───────────┐     │                       │
│   [Farm 5]──────┼────▶│  Hub B    │─────┼──────[Restaurant]     │
│                 │     │(Cold Stor)│     │                       │
│   [Farm 6]──────┘     └───────────┘     └──────[Export]         │
│                                                                  │
│   HUB TYPES:                                                    │
│   • Collection Hub: Aggregate from farms                        │
│   • Auction Hub: Live marketplace                               │
│   • Processing Hub: Slaughter & packaging                       │
│   • Distribution Hub: Last-mile dispatch                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7. Cold Chain Monitoring

```typescript
// IoT Temperature Monitoring
interface TemperatureReading {
  deviceId: string;
  shipmentId: string;
  timestamp: Date;
  temperature: number;
  humidity: number;
  location: GeoPoint;
  alert: 'normal' | 'warning' | 'critical';
}

// Alert thresholds by product type
const thresholds = {
  live_animal: { min: 15, max: 35, unit: 'celsius' },
  fresh_meat: { min: 0, max: 4, unit: 'celsius' },
  frozen_meat: { min: -20, max: -16, unit: 'celsius' },
};

// Breach detection
async function checkTemperatureBreach(
  reading: TemperatureReading,
  productType: string
): Promise<void> {
  const threshold = thresholds[productType];

  if (reading.temperature < threshold.min ||
      reading.temperature > threshold.max) {
    await createAlert({
      type: 'temperature_breach',
      severity: 'critical',
      shipmentId: reading.shipmentId,
      reading,
      threshold,
    });

    await notifyStakeholders(reading.shipmentId, 'temperature_breach');
  }
}
```

## Traceability Patterns

### 8. Farm-to-Fork Traceability

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRACEABILITY CHAIN                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. BIRTH/ORIGIN                                               │
│   ┌──────────────────────────────────────────────┐              │
│   │ Farm ID: VN-HN-001                           │              │
│   │ Animal ID: VN-HN-001-2024-0001              │              │
│   │ Birth Date: 2024-01-15                       │              │
│   │ Breed: Brahman Cross                         │              │
│   │ Parent IDs: [....]                           │              │
│   └──────────────────────────────────────────────┘              │
│                          │                                       │
│                          ▼                                       │
│   2. GROWTH & FEEDING                                           │
│   ┌──────────────────────────────────────────────┐              │
│   │ Feed Type: VietGAP certified grass           │              │
│   │ Growth Records: [weight history]             │              │
│   │ Health Events: [vaccinations, treatments]    │              │
│   │ Certifications: VietGAP, Organic             │              │
│   └──────────────────────────────────────────────┘              │
│                          │                                       │
│                          ▼                                       │
│   3. SALE & TRANSPORT                                           │
│   ┌──────────────────────────────────────────────┐              │
│   │ Sale Date: 2024-06-20                        │              │
│   │ Buyer: Slaughterhouse ABC                    │              │
│   │ Transport: Vehicle VN-123, Driver: Nguyen   │              │
│   │ Pickup Time: 06:00, Delivery: 10:00         │              │
│   └──────────────────────────────────────────────┘              │
│                          │                                       │
│                          ▼                                       │
│   4. PROCESSING                                                 │
│   ┌──────────────────────────────────────────────┐              │
│   │ Slaughter Date: 2024-06-20 12:00             │              │
│   │ Facility: Slaughterhouse ABC, ID: SH-001    │              │
│   │ Inspector: VET-123                           │              │
│   │ Carcass Weight: 280kg                        │              │
│   │ Quality Grade: A                             │              │
│   └──────────────────────────────────────────────┘              │
│                          │                                       │
│                          ▼                                       │
│   5. DISTRIBUTION                                               │
│   ┌──────────────────────────────────────────────┐              │
│   │ Package IDs: [PKG-001, PKG-002, ...]        │              │
│   │ Cold Chain: Maintained 0-4°C                 │              │
│   │ Retail Location: Market XYZ                  │              │
│   │ Best Before: 2024-06-25                      │              │
│   └──────────────────────────────────────────────┘              │
│                                                                  │
│   QR CODE → Scan for full traceability chain                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Anti-Fraud Patterns

### 9. Fraud Detection

```typescript
// Fraud indicators
interface FraudIndicators {
  // Photo manipulation
  imageAnalysis: {
    duplicateCheck: boolean;      // Same image on multiple listings
    metadataCheck: boolean;       // EXIF data manipulation
    reverseImageSearch: boolean;  // Stock photos
  };

  // Behavioral patterns
  behavior: {
    rapidListing: boolean;        // Many listings in short time
    priceAnomaly: boolean;        // Significantly below market
    newAccountHighValue: boolean; // New account, high value items
  };

  // Transaction patterns
  transactions: {
    shillBidding: boolean;        // Fake bids from related accounts
    deliveryFailures: boolean;    // Pattern of non-delivery
    disputeRatio: number;         // High dispute rate
  };
}

// Risk scoring
function calculateFraudRisk(indicators: FraudIndicators): number {
  let risk = 0;

  if (indicators.imageAnalysis.duplicateCheck) risk += 30;
  if (indicators.behavior.priceAnomaly) risk += 20;
  if (indicators.behavior.newAccountHighValue) risk += 25;
  if (indicators.transactions.shillBidding) risk += 40;
  if (indicators.transactions.disputeRatio > 0.1) risk += 25;

  return Math.min(risk, 100);
}
```

## Integration Patterns

### 10. External System Integration

```typescript
// Integration adapters
interface IntegrationAdapters {
  // Payment gateways
  payment: {
    vnpay: VNPayAdapter;
    momo: MoMoAdapter;
    bankTransfer: BankTransferAdapter;
  };

  // Government systems
  government: {
    traceability: VietnameTraceabilityAdapter;  // Bộ NN&PTNT
    veterinary: VeterinarySystemAdapter;        // Cục Thú y
  };

  // Logistics
  logistics: {
    gps: GPSTrackingAdapter;
    temperature: IoTSensorAdapter;
    routing: RouteOptimizationAdapter;
  };

  // Communication
  communication: {
    sms: SMSAdapter;          // OTP, notifications
    push: PushNotificationAdapter;
    zalo: ZaloOAAdapter;      // Vietnam messaging
  };
}
```

## Best Practices Summary

```
┌─────────────────────────────────────────────────────────────────┐
│              LIVESTOCK MARKETPLACE BEST PRACTICES                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Trust & Safety:                                                │
│  □ Verify all participants (KYC/KYB)                            │
│  □ Implement escrow for all transactions                        │
│  □ Real-time fraud detection                                    │
│  □ Clear dispute resolution process                             │
│                                                                  │
│  Quality Control:                                               │
│  □ Third-party quality inspections                              │
│  □ Standardized grading system                                  │
│  □ Photo/video verification                                     │
│  □ Weight verification at delivery                              │
│                                                                  │
│  Logistics:                                                     │
│  □ Cold chain monitoring (IoT)                                  │
│  □ Real-time GPS tracking                                       │
│  □ Hub network optimization                                     │
│  □ Animal welfare compliance                                    │
│                                                                  │
│  Traceability:                                                  │
│  □ Complete farm-to-fork tracking                               │
│  □ QR code for consumer scanning                                │
│  □ Blockchain for immutability (optional)                       │
│  □ Government system integration                                │
│                                                                  │
│  User Experience:                                               │
│  □ Mobile-first design (farmers in field)                       │
│  □ Offline capability                                           │
│  □ Vietnamese language primary                                  │
│  □ SMS fallback for notifications                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
