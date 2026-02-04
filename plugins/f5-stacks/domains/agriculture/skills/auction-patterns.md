# Auction Patterns - Livestock Marketplace

Skill hướng dẫn implement hệ thống đấu giá gia súc/gia cầm.

## Overview

Hệ thống đấu giá cho sàn giao dịch nông sản hỗ trợ:
- English Auction (đấu giá tăng dần) - phổ biến nhất
- Dutch Auction (đấu giá giảm dần) - cho hàng cần bán nhanh
- Sealed Bid (đấu giá kín) - cho giao dịch B2B

## Entity References

Tham khảo entity files:
- `knowledge/entities/auction.yaml` - Auction entity
- `knowledge/entities/bid.yaml` - Bid entity
- `knowledge/entities/listing.yaml` - Listing với selling_type = 'auction'
- `knowledge/business-rules/auction-rules.yaml` - Business rules

## Core Patterns

### 1. English Auction Pattern

```typescript
// Đấu giá tăng dần - giá tăng theo bước giá
interface EnglishAuction {
  startingPrice: number;      // Giá khởi điểm
  reservePrice?: number;      // Giá tối thiểu (hidden)
  bidIncrement: number;       // Bước giá tối thiểu
  currentPrice: number;       // Giá hiện tại
  autoExtend: boolean;        // Tự động gia hạn
  extensionMinutes: number;   // Số phút gia hạn
  maxExtensions: number;      // Số lần gia hạn tối đa
}

// Validate bid
function validateBid(auction: Auction, bidAmount: number, bidderId: string): ValidationResult {
  // Rule BR-AUC-001: Bid >= current + increment
  if (bidAmount < auction.currentPrice + auction.bidIncrement) {
    return { valid: false, error: 'Giá đặt phải >= giá hiện tại + bước giá' };
  }

  // Rule BR-AUC-002: Không tự bid
  if (bidderId === auction.listing.farm.ownerId) {
    return { valid: false, error: 'Không thể đấu giá listing của chính mình' };
  }

  return { valid: true };
}
```

### 2. Auto Extension Pattern

```typescript
// Rule BR-AUC-003, BR-AUC-004
async function handleBidPlaced(auction: Auction, bid: Bid): Promise<void> {
  const timeRemaining = auction.endAt.getTime() - Date.now();
  const fiveMinutes = 5 * 60 * 1000;

  // Bid trong 5 phút cuối + auto_extend enabled
  if (timeRemaining <= fiveMinutes &&
      auction.autoExtend &&
      auction.extensionCount < auction.maxExtensions) {

    // Gia hạn thêm 5 phút
    auction.endAt = new Date(auction.endAt.getTime() + fiveMinutes);
    auction.extensionCount++;
    auction.status = 'extended';

    // Notify all bidders
    await notifyBidders(auction.id, {
      type: 'auction.extended',
      newEndAt: auction.endAt,
      extensionCount: auction.extensionCount
    });
  }

  // Update current price and winner
  auction.currentPrice = bid.amount;
  auction.currentWinnerId = bid.bidderId;
  auction.bidCount++;

  await saveAuction(auction);
}
```

### 3. End Auction Pattern

```typescript
async function endAuction(auctionId: string): Promise<AuctionResult> {
  const auction = await getAuction(auctionId);

  // Determine winner
  const winningBid = await getHighestBid(auctionId);

  if (!winningBid) {
    // No bids - cancel auction
    auction.status = 'cancelled';
    await notifyAll(auction, 'Phiên đấu giá kết thúc không có người tham gia');
    return { status: 'no_bids' };
  }

  // Check reserve price (BR-AUC-005)
  if (auction.reservePrice && winningBid.amount < auction.reservePrice) {
    auction.reserveMet = false;
    auction.status = 'ended';

    // Seller decides: accept or cancel
    await notifySeller(auction, {
      type: 'reserve_not_met',
      highestBid: winningBid.amount,
      reservePrice: auction.reservePrice,
      deadline: addHours(new Date(), 24)
    });

    return { status: 'reserve_not_met', winningBid };
  }

  // Reserve met or no reserve - proceed to create order
  auction.status = 'ended';
  auction.winningBidId = winningBid.id;
  auction.finalPrice = winningBid.amount;
  auction.reserveMet = true;
  auction.endedAt = new Date();

  // Create order
  const order = await createOrderFromAuction(auction, winningBid);

  // Notify winner
  await notifyWinner(winningBid.bidderId, {
    type: 'auction.won',
    auctionCode: auction.auctionCode,
    finalPrice: auction.finalPrice,
    paymentDeadline: addHours(new Date(), 24) // BR-AUC-006
  });

  return { status: 'completed', order };
}
```

### 4. Shill Bidding Detection Pattern

```typescript
// Rule BR-AUC-007
interface ShillBidDetector {
  // Cùng IP bid trên listings của nhau
  async detectCrossIPBidding(bid: Bid): Promise<ShillAlert | null> {
    const suspiciousPattern = await db.query(`
      SELECT b1.bidder_id, b2.bidder_id, b1.ip_address
      FROM bids b1
      JOIN bids b2 ON b1.ip_address = b2.ip_address
      JOIN auctions a1 ON b1.auction_id = a1.id
      JOIN auctions a2 ON b2.auction_id = a2.id
      JOIN listings l1 ON a1.listing_id = l1.id
      JOIN listings l2 ON a2.listing_id = l2.id
      JOIN farms f1 ON l1.farm_id = f1.id
      JOIN farms f2 ON l2.farm_id = f2.id
      WHERE b1.bidder_id = f2.owner_id
        AND b2.bidder_id = f1.owner_id
        AND b1.auction_id != b2.auction_id
    `);

    if (suspiciousPattern.length > 0) {
      return {
        type: 'cross_ip_bidding',
        accounts: suspiciousPattern,
        severity: 'high'
      };
    }

    return null;
  }

  // Bid pattern bất thường
  async detectAbnormalPattern(bid: Bid): Promise<ShillAlert | null> {
    // Kiểm tra: bid liên tục, bid vào phút cuối cùng, bid increment nhỏ
    const recentBids = await getRecentBids(bid.auctionId, 10);

    // Pattern: 2 accounts bid qua lại
    const bidderCounts = countBy(recentBids, 'bidderId');
    if (Object.keys(bidderCounts).length === 2) {
      const [bidder1, bidder2] = Object.keys(bidderCounts);
      if (Math.abs(bidderCounts[bidder1] - bidderCounts[bidder2]) <= 1) {
        return {
          type: 'ping_pong_bidding',
          bidders: [bidder1, bidder2],
          severity: 'medium'
        };
      }
    }

    return null;
  }
}
```

### 5. Scheduled Jobs Pattern

```typescript
// Auction lifecycle scheduler
@Cron('*/1 * * * *') // Mỗi phút
async function processAuctions(): Promise<void> {
  const now = new Date();

  // Start scheduled auctions
  const auctionsToStart = await getAuctionsByStatus('scheduled', {
    startAt: { $lte: now }
  });

  for (const auction of auctionsToStart) {
    auction.status = 'active';
    await notifyWatchers(auction.id, 'auction.started');
    await saveAuction(auction);
  }

  // End active auctions
  const auctionsToEnd = await getAuctionsByStatus(['active', 'extended'], {
    endAt: { $lte: now }
  });

  for (const auction of auctionsToEnd) {
    await endAuction(auction.id);
  }
}

// Payment deadline check (BR-AUC-006)
@Cron('*/5 * * * *')
async function checkPaymentDeadlines(): Promise<void> {
  const expiredOrders = await getOrders({
    status: 'pending_deposit',
    orderSource: 'auction',
    createdAt: { $lt: subHours(new Date(), 24) }
  });

  for (const order of expiredOrders) {
    // Cancel and transfer to second bidder
    await cancelAndTransfer(order);
  }
}
```

## Real-time Implementation

### WebSocket Events

```typescript
// Auction WebSocket namespace
@WebSocketGateway({ namespace: 'auction' })
export class AuctionGateway {
  @SubscribeMessage('join_auction')
  async handleJoinAuction(client: Socket, auctionId: string) {
    await client.join(`auction:${auctionId}`);

    const auction = await getAuction(auctionId);
    client.emit('auction_state', {
      currentPrice: auction.currentPrice,
      bidCount: auction.bidCount,
      endAt: auction.endAt,
      status: auction.status
    });
  }

  // Broadcast bid to all watchers
  async broadcastBid(auctionId: string, bid: Bid) {
    this.server.to(`auction:${auctionId}`).emit('new_bid', {
      amount: bid.amount,
      bidderId: bid.bidderId,
      bidderName: await getBidderName(bid.bidderId),
      timestamp: bid.createdAt,
      currentPrice: bid.amount
    });
  }

  // Countdown sync
  @Cron('* * * * * *') // Every second
  async syncCountdown() {
    const activeAuctions = await getActiveAuctions();
    for (const auction of activeAuctions) {
      const remaining = auction.endAt.getTime() - Date.now();
      this.server.to(`auction:${auction.id}`).emit('countdown', {
        remaining: Math.max(0, remaining),
        extended: auction.status === 'extended'
      });
    }
  }
}
```

## Database Considerations

### Indexes for Auction Queries

```sql
-- Fast auction lookup
CREATE INDEX idx_auction_status ON auctions(status);
CREATE INDEX idx_auction_end_at ON auctions(end_at);
CREATE INDEX idx_auction_listing ON auctions(listing_id);

-- Fast bid queries
CREATE INDEX idx_bid_auction ON bids(auction_id);
CREATE INDEX idx_bid_amount ON bids(auction_id, amount DESC);
CREATE INDEX idx_bid_bidder ON bids(bidder_id);

-- Shill detection
CREATE INDEX idx_bid_ip ON bids(ip_address);
```

### Optimistic Locking for Bids

```typescript
async function placeBid(auctionId: string, amount: number, bidderId: string): Promise<Bid> {
  return await db.transaction(async (tx) => {
    // Lock auction row
    const auction = await tx.query(
      'SELECT * FROM auctions WHERE id = $1 FOR UPDATE',
      [auctionId]
    );

    // Validate
    if (amount <= auction.currentPrice) {
      throw new Error('Bid amount too low - may have been outbid');
    }

    // Create bid
    const bid = await tx.insert('bids', { auctionId, amount, bidderId });

    // Update auction
    await tx.update('auctions', auctionId, {
      currentPrice: amount,
      currentWinnerId: bidderId,
      bidCount: auction.bidCount + 1
    });

    return bid;
  });
}
```

## Testing Checklist

- [ ] Bid validation (increment, self-bid)
- [ ] Auto extension triggers correctly
- [ ] Max extensions respected
- [ ] Reserve price handling
- [ ] Winner notification
- [ ] Payment deadline enforcement
- [ ] Transfer to second bidder
- [ ] Shill bidding detection
- [ ] Real-time updates via WebSocket
- [ ] Concurrent bid handling
