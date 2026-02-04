---
name: auction-patterns
category: agriculture/shared
description: Auction and bidding patterns for livestock marketplace
version: "1.0"
---

# Auction Patterns for Livestock Marketplace

## Overview

Auction systems for livestock require special considerations including quality
verification, delivery logistics, and animal welfare. This document covers
implementation patterns for various auction types.

## Auction Types

### 1. English Auction (Ascending Price)

The most common auction type for livestock.

```typescript
interface EnglishAuction {
  id: string;
  listingId: string;
  status: 'scheduled' | 'active' | 'ended' | 'cancelled';

  // Pricing
  startingBid: Money;
  currentBid?: Money;
  reservePrice?: Money;        // Hidden minimum seller accepts
  buyNowPrice?: Money;         // Instant purchase option
  bidIncrement: Money;         // Minimum bid increase

  // Timing
  scheduledStart: Date;
  scheduledEnd: Date;
  actualEnd?: Date;

  // Anti-sniping
  extensionMinutes: number;    // Extend if bid in last N minutes
  maxExtensions: number;       // Maximum extensions allowed
  extensionsUsed: number;

  // Winner
  winningBid?: string;
  winnerId?: string;
}

// Bid placement logic
async function placeBid(
  auction: EnglishAuction,
  bidder: string,
  amount: Money
): Promise<BidResult> {
  // Validate auction is active
  if (auction.status !== 'active') {
    return { success: false, error: 'Auction not active' };
  }

  // Calculate minimum bid
  const minBid = auction.currentBid
    ? auction.currentBid.add(auction.bidIncrement)
    : auction.startingBid;

  if (amount.lessThan(minBid)) {
    return { success: false, error: `Minimum bid is ${minBid}` };
  }

  // Check bidder deposit
  const deposit = await getDeposit(bidder);
  if (deposit.lessThan(amount)) {
    return { success: false, error: 'Insufficient deposit' };
  }

  // Place bid
  const bid = await createBid({
    auctionId: auction.id,
    bidderId: bidder,
    amount,
    timestamp: new Date(),
  });

  // Update auction
  await updateAuction(auction.id, {
    currentBid: amount,
    winningBid: bid.id,
    winnerId: bidder,
  });

  // Check for anti-sniping extension
  await checkAndExtend(auction);

  // Notify outbid bidders
  await notifyOutbid(auction.id, bidder);

  return { success: true, bid };
}
```

### 2. Dutch Auction (Descending Price)

Useful for bulk livestock lots.

```typescript
interface DutchAuction {
  id: string;
  listingId: string;
  status: 'scheduled' | 'active' | 'sold' | 'expired';

  // Pricing
  startingPrice: Money;        // High starting price
  currentPrice: Money;         // Current (decreasing) price
  floorPrice: Money;           // Minimum price
  priceDecrement: Money;       // Amount to decrease
  decrementInterval: number;   // Seconds between decreases

  // Winner
  winner?: string;
  finalPrice?: Money;
}

// Price decrease loop
async function runDutchAuction(auction: DutchAuction): Promise<void> {
  while (auction.status === 'active') {
    // Wait for interval
    await sleep(auction.decrementInterval * 1000);

    // Check if sold during wait
    const current = await getAuction(auction.id);
    if (current.status !== 'active') break;

    // Decrease price
    const newPrice = current.currentPrice.subtract(auction.priceDecrement);

    if (newPrice.lessThanOrEqual(auction.floorPrice)) {
      // Hit floor, mark as expired
      await updateAuction(auction.id, {
        status: 'expired',
        currentPrice: auction.floorPrice
      });
      break;
    }

    await updateAuction(auction.id, { currentPrice: newPrice });
    await broadcastPriceUpdate(auction.id, newPrice);
  }
}

// Accept current price
async function acceptDutchPrice(
  auction: DutchAuction,
  buyer: string
): Promise<BuyResult> {
  // Atomic operation to prevent race conditions
  const result = await atomicUpdate(auction.id, (a) => {
    if (a.status !== 'active') {
      throw new Error('Auction no longer active');
    }
    return {
      status: 'sold',
      winner: buyer,
      finalPrice: a.currentPrice,
    };
  });

  return { success: true, price: result.finalPrice };
}
```

### 3. Sealed Bid Auction

For high-value livestock where transparency is less important.

```typescript
interface SealedBidAuction {
  id: string;
  listingId: string;
  status: 'open' | 'closed' | 'revealed';

  // Timing
  biddingDeadline: Date;
  revealTime: Date;

  // Sealed bids (encrypted until reveal)
  bids: SealedBid[];

  // Winner (populated after reveal)
  winningBid?: string;
  winnerId?: string;
}

interface SealedBid {
  id: string;
  auctionId: string;
  bidderId: string;
  encryptedAmount: string;     // Encrypted bid amount
  depositLocked: Money;        // Deposit must cover max possible bid
  timestamp: Date;
  revealedAmount?: Money;      // Decrypted after deadline
}

// Submit sealed bid
async function submitSealedBid(
  auction: SealedBidAuction,
  bidder: string,
  encryptedAmount: string,
  depositAmount: Money
): Promise<void> {
  if (new Date() > auction.biddingDeadline) {
    throw new Error('Bidding deadline passed');
  }

  // Lock deposit
  await lockDeposit(bidder, depositAmount);

  // Record sealed bid
  await createSealedBid({
    auctionId: auction.id,
    bidderId: bidder,
    encryptedAmount,
    depositLocked: depositAmount,
    timestamp: new Date(),
  });
}

// Reveal all bids and determine winner
async function revealBids(auction: SealedBidAuction): Promise<void> {
  // Decrypt all bids
  const bids = await Promise.all(
    auction.bids.map(async (bid) => ({
      ...bid,
      revealedAmount: await decryptBid(bid.encryptedAmount, bid.bidderId),
    }))
  );

  // Sort by amount (highest first)
  bids.sort((a, b) => b.revealedAmount.compare(a.revealedAmount));

  // Winner is highest bid
  const winner = bids[0];

  await updateAuction(auction.id, {
    status: 'revealed',
    winningBid: winner.id,
    winnerId: winner.bidderId,
  });

  // Release deposits for non-winners
  for (const bid of bids.slice(1)) {
    await releaseDeposit(bid.bidderId, bid.depositLocked);
  }
}
```

### 4. Live Auction (Real-time)

For scheduled auction events with auctioneer.

```typescript
interface LiveAuction {
  id: string;
  listingIds: string[];        // Multiple lots in one session
  status: 'scheduled' | 'live' | 'ended';

  // Timing
  scheduledStart: Date;
  actualStart?: Date;

  // Current lot
  currentLotIndex: number;
  currentLot: AuctionLot;

  // Auctioneer
  auctioneerId: string;

  // Participants
  participants: LiveParticipant[];
}

interface AuctionLot {
  listingId: string;
  status: 'pending' | 'active' | 'sold' | 'passed';
  startingBid: Money;
  currentBid?: Money;
  currentBidder?: string;
  callCount: number;           // "Going once, going twice..."
}

// Auctioneer actions
async function auctioneerAction(
  auction: LiveAuction,
  action: 'start_lot' | 'call' | 'sold' | 'pass' | 'next_lot'
): Promise<void> {
  switch (action) {
    case 'start_lot':
      await broadcastToParticipants(auction.id, {
        type: 'lot_started',
        lot: auction.currentLot,
      });
      break;

    case 'call':
      auction.currentLot.callCount++;
      await broadcastToParticipants(auction.id, {
        type: 'call',
        count: auction.currentLot.callCount,
        message: getCallMessage(auction.currentLot.callCount),
      });
      break;

    case 'sold':
      auction.currentLot.status = 'sold';
      await createOrder(auction.currentLot);
      await broadcastToParticipants(auction.id, {
        type: 'sold',
        winner: auction.currentLot.currentBidder,
        price: auction.currentLot.currentBid,
      });
      break;

    case 'pass':
      auction.currentLot.status = 'passed';
      await broadcastToParticipants(auction.id, {
        type: 'passed',
        message: 'Lot did not meet reserve',
      });
      break;

    case 'next_lot':
      auction.currentLotIndex++;
      if (auction.currentLotIndex < auction.listingIds.length) {
        auction.currentLot = await loadLot(
          auction.listingIds[auction.currentLotIndex]
        );
      } else {
        auction.status = 'ended';
      }
      break;
  }
}

function getCallMessage(count: number): string {
  switch (count) {
    case 1: return 'Going once...';
    case 2: return 'Going twice...';
    case 3: return 'Sold!';
    default: return '';
  }
}
```

## Anti-Fraud Measures

### Shill Bidding Detection

```typescript
interface ShillDetection {
  // Bidder relationship analysis
  checkBidderRelationship(bidder1: string, bidder2: string): Promise<number>;

  // Bidding pattern analysis
  analyzeBiddingPattern(auctionId: string): Promise<PatternAnalysis>;

  // Device fingerprint comparison
  compareDevices(bidder1: string, bidder2: string): Promise<number>;
}

interface PatternAnalysis {
  suspiciousPatterns: {
    pattern: string;
    confidence: number;
    bidders: string[];
  }[];

  riskScore: number;
  recommendation: 'allow' | 'review' | 'block';
}

// Detection patterns
const shillPatterns = [
  {
    name: 'sequential_bidding',
    description: 'Same bidders always bid in sequence',
    weight: 0.3,
  },
  {
    name: 'exact_increment',
    description: 'Always bid exact minimum increment',
    weight: 0.2,
  },
  {
    name: 'timing_correlation',
    description: 'Bids placed at suspiciously regular intervals',
    weight: 0.25,
  },
  {
    name: 'bidder_seller_history',
    description: 'Bidder frequently bids on same seller items',
    weight: 0.35,
  },
  {
    name: 'device_similarity',
    description: 'Multiple bidders from same device/network',
    weight: 0.4,
  },
];

async function detectShillBidding(auctionId: string): Promise<ShillResult> {
  const analysis = await analyzeBiddingPattern(auctionId);

  if (analysis.riskScore > 0.7) {
    // High risk - pause auction
    await pauseAuction(auctionId);
    await notifyAdmins('shill_detection', { auctionId, analysis });
    return { action: 'paused', reason: 'Potential shill bidding detected' };
  }

  if (analysis.riskScore > 0.4) {
    // Medium risk - flag for review
    await flagForReview(auctionId, analysis);
    return { action: 'flagged', reason: 'Suspicious patterns detected' };
  }

  return { action: 'allowed' };
}
```

### Bid Velocity Controls

```typescript
interface BidVelocityControl {
  // Maximum bids per minute per user
  maxBidsPerMinute: number;

  // Minimum time between bids from same user
  minTimeBetweenBids: number;  // seconds

  // Cool-down period after rapid bidding
  cooldownThreshold: number;   // triggers cooldown
  cooldownDuration: number;    // seconds
}

async function checkBidVelocity(
  auctionId: string,
  bidderId: string
): Promise<boolean> {
  const recentBids = await getBidsInLastMinute(auctionId, bidderId);

  if (recentBids.length >= config.maxBidsPerMinute) {
    await applyCooldown(auctionId, bidderId);
    return false;
  }

  const lastBid = recentBids[0];
  if (lastBid) {
    const elapsed = Date.now() - lastBid.timestamp.getTime();
    if (elapsed < config.minTimeBetweenBids * 1000) {
      return false;
    }
  }

  return true;
}
```

## Deposit & Payment

### Deposit Management

```typescript
interface DepositAccount {
  userId: string;
  balance: Money;
  holds: DepositHold[];

  // Available = balance - sum(holds)
  available: Money;
}

interface DepositHold {
  id: string;
  auctionId: string;
  amount: Money;
  reason: 'bid' | 'buy_now' | 'penalty';
  createdAt: Date;
  expiresAt?: Date;
}

// Hold deposit for bid
async function holdForBid(
  userId: string,
  auctionId: string,
  amount: Money
): Promise<DepositHold> {
  const account = await getDepositAccount(userId);

  if (account.available.lessThan(amount)) {
    throw new InsufficientDepositError(account.available, amount);
  }

  const hold = await createHold({
    userId,
    auctionId,
    amount,
    reason: 'bid',
  });

  // Previous hold on same auction? Release it
  const previousHold = account.holds.find(h => h.auctionId === auctionId);
  if (previousHold) {
    await releaseHold(previousHold.id);
  }

  return hold;
}

// Convert hold to payment on win
async function convertHoldToPayment(
  hold: DepositHold,
  orderId: string
): Promise<Payment> {
  // Create payment from held funds
  const payment = await createPayment({
    orderId,
    amount: hold.amount,
    source: 'deposit',
    holdId: hold.id,
  });

  // Deduct from balance
  await deductBalance(hold.userId, hold.amount);

  // Remove hold
  await deleteHold(hold.id);

  return payment;
}
```

## Notification System

```typescript
interface AuctionNotifications {
  // Bidder notifications
  bidPlaced: (bid: Bid) => Promise<void>;
  outbid: (auction: Auction, bidder: string, newBid: Bid) => Promise<void>;
  auctionWon: (auction: Auction, winner: string) => Promise<void>;
  auctionLost: (auction: Auction, bidder: string) => Promise<void>;

  // Seller notifications
  newBid: (auction: Auction, bid: Bid) => Promise<void>;
  auctionEnded: (auction: Auction) => Promise<void>;
  reserveMet: (auction: Auction) => Promise<void>;

  // System notifications
  auctionStarting: (auction: Auction, minutesBefore: number) => Promise<void>;
  auctionEnding: (auction: Auction, minutesBefore: number) => Promise<void>;
}

// Notification delivery
async function sendAuctionNotification(
  type: keyof AuctionNotifications,
  userId: string,
  data: any
): Promise<void> {
  const user = await getUser(userId);
  const preferences = await getNotificationPreferences(userId);

  // Send via enabled channels
  const promises = [];

  if (preferences.push) {
    promises.push(sendPush(user.deviceTokens, formatPush(type, data)));
  }

  if (preferences.sms && isHighPriority(type)) {
    promises.push(sendSMS(user.phone, formatSMS(type, data)));
  }

  if (preferences.email) {
    promises.push(sendEmail(user.email, formatEmail(type, data)));
  }

  await Promise.all(promises);
}

function isHighPriority(type: string): boolean {
  return ['auctionWon', 'outbid', 'auctionEnding'].includes(type);
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  AUCTION BEST PRACTICES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Fairness:                                                      │
│  □ Anti-sniping extension for all timed auctions                │
│  □ Clear bid increment rules                                    │
│  □ Transparent reserve price indicators (met/not met)           │
│  □ Equal access to auction information                          │
│                                                                  │
│  Security:                                                      │
│  □ Require verified accounts for bidding                        │
│  □ Deposit requirement based on bid amount                      │
│  □ Shill bidding detection and prevention                       │
│  □ Audit trail for all bids                                     │
│                                                                  │
│  User Experience:                                               │
│  □ Real-time bid updates (WebSocket)                            │
│  □ Clear countdown timers                                       │
│  □ Mobile-friendly bidding interface                            │
│  □ Immediate outbid notifications                               │
│                                                                  │
│  Reliability:                                                   │
│  □ Atomic bid operations                                        │
│  □ Server-side timestamp validation                             │
│  □ Graceful handling of network issues                          │
│  □ Auction state recovery                                       │
│                                                                  │
│  Livestock-Specific:                                            │
│  □ Quality inspection before auction close                      │
│  □ Weight verification at delivery                              │
│  □ Health certificate requirements                              │
│  □ Transport arrangement window after winning                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
