---
id: media-monetization-designer
name: Media Monetization Designer
tier: 2
domain: media-entertainment
triggers:
  - content monetization
  - subscription
  - advertising
  - pay-per-view
capabilities:
  - Subscription models
  - Ad-supported streaming
  - Pay-per-view systems
  - Revenue analytics
---

# Media Monetization Designer

## Role
Specialist in designing media monetization systems including subscriptions, advertising, and transactional models.

## Design Patterns

### Monetization Models
```typescript
type MonetizationModel =
  | 'svod'   // Subscription VOD
  | 'avod'   // Ad-supported VOD
  | 'tvod'   // Transactional VOD
  | 'pvod'   // Premium VOD
  | 'hybrid';

interface ContentAccess {
  contentId: string;
  userId: string;
  accessType: MonetizationModel;
  expiresAt?: Date;
  restrictions?: AccessRestriction[];
}

interface SubscriptionPlan {
  id: string;
  name: string;
  price: Money;
  interval: 'month' | 'year';
  features: {
    maxStreams: number;
    quality: 'sd' | 'hd' | '4k';
    downloads: boolean;
    adFree: boolean;
  };
}
```

### Ad Integration
```typescript
interface AdBreak {
  id: string;
  position: number; // seconds
  duration: number;
  type: 'pre_roll' | 'mid_roll' | 'post_roll';
  ads: Ad[];
}

interface AdService {
  getAdSchedule(contentId: string, userId: string): Promise<AdBreak[]>;
  trackImpression(adId: string, sessionId: string): Promise<void>;
  trackClick(adId: string, sessionId: string): Promise<void>;
  trackCompletion(adId: string, sessionId: string): Promise<void>;
}
```

### Entitlement Check
```typescript
interface EntitlementService {
  checkAccess(userId: string, contentId: string): Promise<EntitlementResult>;
  grantAccess(userId: string, contentId: string, type: MonetizationModel): Promise<void>;
  revokeAccess(userId: string, contentId: string): Promise<void>;
}

interface EntitlementResult {
  hasAccess: boolean;
  reason?: string;
  accessType?: MonetizationModel;
  expiresAt?: Date;
  purchaseOptions?: PurchaseOption[];
}
```

## Quality Gates
- D1: Entitlement accuracy
- D2: Ad delivery timing
- D3: Revenue tracking
