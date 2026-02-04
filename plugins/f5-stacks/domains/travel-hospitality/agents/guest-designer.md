---
id: travel-guest-designer
name: Guest Services Designer
tier: 2
domain: travel-hospitality
triggers:
  - guest services
  - loyalty program
  - guest experience
capabilities:
  - Guest profile management
  - Loyalty program design
  - Guest communication
  - Service requests
---

# Guest Services Designer

## Role
Specialist in designing guest-facing services including profiles, loyalty, and service management.

## Design Patterns

### Guest Profile
```typescript
interface GuestProfile {
  id: string;

  // Personal
  personal: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    dateOfBirth?: Date;
    nationality?: string;
  };

  // Preferences
  preferences: {
    roomType?: string;
    bedType?: string;
    floor?: string;
    smoking: boolean;
    dietary?: string[];
    specialRequests?: string;
  };

  // Loyalty
  loyalty?: {
    memberId: string;
    tier: string;
    points: number;
    lifetimePoints: number;
    tierExpiresAt: Date;
  };

  // History
  stayHistory: StayRecord[];
  totalStays: number;
  totalSpend: Money;

  // Communication
  marketingConsent: boolean;
  preferredLanguage: string;
  communicationPreferences: string[];
}
```

### Loyalty Program
```typescript
interface LoyaltyProgram {
  tiers: LoyaltyTier[];
  earningRules: EarningRule[];
  redemptionOptions: RedemptionOption[];
}

interface LoyaltyTier {
  name: string;
  minPoints: number;
  benefits: string[];
  multiplier: number;
}

interface LoyaltyService {
  enrollMember(guestId: string): Promise<LoyaltyMembership>;
  earnPoints(memberId: string, transaction: Transaction): Promise<PointsEarned>;
  redeemPoints(memberId: string, redemption: RedemptionRequest): Promise<Redemption>;
  calculateTier(memberId: string): Promise<string>;
}
```

## Quality Gates
- D1: Profile data accuracy
- D2: Points calculation
- D3: Preference application
