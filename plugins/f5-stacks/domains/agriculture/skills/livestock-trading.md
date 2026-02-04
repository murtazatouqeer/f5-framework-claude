# Livestock Trading - Complete Implementation Guide

Skill hướng dẫn implement đầy đủ hệ thống mua bán gia súc/gia cầm.

## Overview

Hệ thống trading hỗ trợ 3 hình thức:
1. **Auction** - Đấu giá tăng dần
2. **Fixed Price** - Giá cố định, mua ngay
3. **Negotiable** - Cho phép thương lượng (Offer/Counter-offer)

## Entity References

- `knowledge/entities/listing.yaml` - Listing entity
- `knowledge/entities/livestock.yaml` - Livestock entity
- `knowledge/entities/order.yaml` - Order entity
- `knowledge/entities/offer.yaml` - Offer entity
- `knowledge/business-rules/listing-rules.yaml` - Listing rules
- `knowledge/business-rules/order-rules.yaml` - Order rules

## Core Trading Flows

### 1. Listing Creation Flow

```typescript
// Complete listing creation with validation
async function createListing(input: CreateListingInput): Promise<Listing> {
  // 1. Validate farm
  const farm = await getFarm(input.farmId);
  if (farm.verificationStatus !== 'verified') {
    throw new Error('Trang trại chưa được xác minh');
  }
  if (farm.status !== 'active') {
    throw new Error('Trang trại đang bị tạm ngưng');
  }

  // 2. Check max listings (BR-LST-030)
  const activeCount = await countActiveListings(input.farmId);
  const maxListings = farm.tier === 'premium' ? 20 : 10;
  if (activeCount >= maxListings) {
    throw new Error(`Đã đạt giới hạn ${maxListings} tin đăng active`);
  }

  // 3. Validate livestock
  const livestock = await getLivestock(input.livestockId);
  if (livestock.healthStatus !== 'healthy') {
    throw new Error('Gia súc/gia cầm không đủ điều kiện sức khỏe');
  }
  if (input.quantity > livestock.availableQuantity) {
    throw new Error('Số lượng vượt quá số lượng khả dụng');
  }

  // 4. Validate images (BR-LST-004)
  if (input.images.length < 3) {
    throw new Error('Cần tối thiểu 3 ảnh');
  }

  // 5. Validate pricing based on selling type
  validatePricing(input);

  // 6. Create listing
  const listing = await db.insert('listings', {
    ...input,
    listingCode: generateListingCode(),
    totalWeightKg: input.quantity * input.avgWeightKg,
    status: shouldAutoApprove(farm) ? 'active' : 'pending_approval',
    publishedAt: shouldAutoApprove(farm) ? new Date() : null,
    expiresAt: addDays(new Date(), 30)
  });

  // 7. Reserve livestock quantity
  await reserveLivestockQuantity(livestock.id, input.quantity);

  // 8. Create auction if needed
  if (input.sellingType === 'auction') {
    await createAuction(listing.id, input.auctionConfig);
  }

  // 9. Notify seller
  await notifySeller(farm.ownerId, {
    type: listing.status === 'active' ? 'listing.published' : 'listing.pending',
    listingCode: listing.listingCode
  });

  return listing;
}

function validatePricing(input: CreateListingInput): void {
  switch (input.sellingType) {
    case 'fixed_price':
      if (!input.pricePerKg || input.pricePerKg <= 0) {
        throw new Error('Vui lòng nhập giá/kg hợp lệ');
      }
      break;

    case 'auction':
      if (!input.startingPrice || input.startingPrice <= 0) {
        throw new Error('Vui lòng nhập giá khởi điểm');
      }
      if (!input.bidIncrement || input.bidIncrement <= 0) {
        throw new Error('Vui lòng nhập bước giá');
      }
      // BR-LST-012: Bid increment 1-10% of starting price
      const minIncrement = input.startingPrice * 0.01;
      const maxIncrement = input.startingPrice * 0.10;
      if (input.bidIncrement < minIncrement || input.bidIncrement > maxIncrement) {
        throw new Error('Bước giá phải từ 1-10% giá khởi điểm');
      }
      break;

    case 'negotiable':
      if (!input.pricePerKg || input.pricePerKg <= 0) {
        throw new Error('Vui lòng nhập giá niêm yết');
      }
      if (input.floorPricePerKg && input.floorPricePerKg >= input.pricePerKg) {
        throw new Error('Giá sàn phải thấp hơn giá niêm yết');
      }
      break;
  }
}
```

### 2. Fixed Price Purchase Flow

```typescript
async function buyNow(listingId: string, buyerId: string, quantity: number): Promise<Order> {
  return await db.transaction(async (tx) => {
    // 1. Lock listing
    const listing = await tx.query(
      'SELECT * FROM listings WHERE id = $1 FOR UPDATE',
      [listingId]
    );

    // 2. Validate
    if (listing.status !== 'active') {
      throw new Error('Tin đăng không còn khả dụng');
    }
    if (listing.sellingType !== 'fixed_price') {
      throw new Error('Tin đăng này không hỗ trợ mua ngay');
    }
    if (quantity > listing.quantity) {
      throw new Error('Số lượng vượt quá số lượng còn lại');
    }

    // 3. Check buyer != seller
    const farm = await getFarm(listing.farmId);
    if (buyerId === farm.ownerId) {
      throw new Error('Không thể mua hàng của chính mình');
    }

    // 4. Calculate amounts
    const weightKg = quantity * listing.avgWeightKg;
    const subtotal = weightKg * listing.pricePerKg;
    const platformFee = calculatePlatformFee(subtotal, farm.tier);
    const shippingFee = await estimateShipping(listing.pickupLocation, buyerId);
    const totalAmount = subtotal + platformFee + shippingFee;
    const depositAmount = calculateDeposit(totalAmount);

    // 5. Create order
    const order = await tx.insert('orders', {
      orderCode: generateOrderCode(),
      listingId,
      sellerId: farm.ownerId,
      buyerId,
      orderSource: 'fixed_price',
      animalType: listing.animalType,
      breed: listing.breed,
      quantity,
      declaredWeightKg: weightKg,
      pricePerKg: listing.pricePerKg,
      subtotal,
      platformFee,
      shippingFee,
      totalAmount,
      depositAmount,
      status: 'pending_deposit',
      paymentStatus: 'pending'
    });

    // 6. Update listing quantity
    if (quantity === listing.quantity) {
      await tx.update('listings', listingId, { status: 'sold' });
    } else {
      await tx.update('listings', listingId, {
        quantity: listing.quantity - quantity,
        totalWeightKg: (listing.quantity - quantity) * listing.avgWeightKg
      });
    }

    // 7. Notify seller
    await notifySeller(farm.ownerId, {
      type: 'order.created',
      orderCode: order.orderCode,
      quantity,
      totalAmount
    });

    // 8. Schedule deposit reminder
    await scheduleReminder(order.id, 'deposit_reminder', addHours(new Date(), 12));

    // 9. Schedule auto-cancel
    await scheduleJob('cancel_unpaid_order', order.id, addHours(new Date(), 24));

    return order;
  });
}
```

### 3. Offer/Negotiation Flow

```typescript
// Buyer makes an offer
async function makeOffer(
  listingId: string,
  buyerId: string,
  offerPricePerKg: number,
  message?: string
): Promise<Offer> {
  const listing = await getListing(listingId);

  // Validate
  if (listing.sellingType !== 'negotiable') {
    throw new Error('Tin đăng không cho phép thương lượng');
  }
  if (listing.status !== 'active') {
    throw new Error('Tin đăng không còn khả dụng');
  }

  const farm = await getFarm(listing.farmId);
  if (buyerId === farm.ownerId) {
    throw new Error('Không thể đặt offer cho hàng của mình');
  }

  // Check minimum offer (at least floor price if set)
  if (listing.floorPricePerKg && offerPricePerKg < listing.floorPricePerKg) {
    throw new Error('Giá offer quá thấp');
  }

  // Create offer
  const offer = await db.insert('offers', {
    offerCode: generateOfferCode(),
    listingId,
    buyerId,
    offerPricePerKg,
    totalPrice: offerPricePerKg * listing.totalWeightKg,
    status: 'pending',
    message,
    expiresAt: addDays(new Date(), 2) // Offer valid for 2 days
  });

  // Update listing offer count
  await db.increment('listings', listingId, 'offerCount');

  // Notify seller
  await notifySeller(farm.ownerId, {
    type: 'new_offer',
    offerCode: offer.offerCode,
    offerPrice: offerPricePerKg,
    listingTitle: listing.title
  });

  return offer;
}

// Seller responds to offer
async function respondToOffer(
  offerId: string,
  sellerId: string,
  response: 'accept' | 'reject' | 'counter',
  counterPrice?: number
): Promise<Offer | Order> {
  const offer = await getOffer(offerId);
  const listing = await getListing(offer.listingId);
  const farm = await getFarm(listing.farmId);

  // Verify seller owns the listing
  if (farm.ownerId !== sellerId) {
    throw new Error('Không có quyền xử lý offer này');
  }

  switch (response) {
    case 'accept':
      // Accept offer and create order
      offer.status = 'accepted';
      await saveOffer(offer);

      const order = await createOrderFromOffer(listing, offer);
      return order;

    case 'reject':
      offer.status = 'rejected';
      await saveOffer(offer);

      await notifyBuyer(offer.buyerId, {
        type: 'offer.rejected',
        offerCode: offer.offerCode,
        listingTitle: listing.title
      });
      return offer;

    case 'counter':
      if (!counterPrice) {
        throw new Error('Vui lòng nhập giá counter');
      }

      offer.status = 'countered';
      offer.counterPricePerKg = counterPrice;
      offer.counterAt = new Date();
      await saveOffer(offer);

      await notifyBuyer(offer.buyerId, {
        type: 'offer.countered',
        offerCode: offer.offerCode,
        counterPrice,
        listingTitle: listing.title
      });
      return offer;
  }
}

// Buyer responds to counter offer
async function respondToCounter(
  offerId: string,
  buyerId: string,
  accept: boolean
): Promise<Offer | Order> {
  const offer = await getOffer(offerId);

  if (offer.buyerId !== buyerId) {
    throw new Error('Không có quyền xử lý offer này');
  }
  if (offer.status !== 'countered') {
    throw new Error('Offer không ở trạng thái counter');
  }

  if (accept) {
    offer.status = 'accepted';
    offer.offerPricePerKg = offer.counterPricePerKg;
    await saveOffer(offer);

    const listing = await getListing(offer.listingId);
    const order = await createOrderFromOffer(listing, offer);
    return order;
  } else {
    offer.status = 'counter_rejected';
    await saveOffer(offer);
    return offer;
  }
}
```

### 4. Order Fulfillment Flow

```typescript
async function processOrderFulfillment(orderId: string): Promise<void> {
  const order = await getOrder(orderId);

  // State machine transitions
  switch (order.status) {
    case 'pending_deposit':
      await handleDepositPayment(order);
      break;

    case 'deposit_paid':
      await handleSellerConfirmation(order);
      break;

    case 'confirmed':
      await handleProcessing(order);
      break;

    case 'processing':
      await handleReadyForPickup(order);
      break;

    case 'ready_for_pickup':
      await handlePickup(order);
      break;

    case 'in_transit':
      await handleTransit(order);
      break;

    case 'delivered':
      await handleDeliveryConfirmation(order);
      break;
  }
}

// Deposit payment handling
async function handleDepositPayment(order: Order): Promise<void> {
  const payment = await createPayment({
    orderId: order.id,
    payerId: order.buyerId,
    paymentType: 'deposit',
    amount: order.depositAmount,
    expiresAt: addHours(order.createdAt, 24)
  });

  // After successful payment callback
  // This is called by payment gateway webhook
}

async function onDepositPaid(paymentId: string): Promise<void> {
  const payment = await getPayment(paymentId);
  const order = await getOrder(payment.orderId);

  await db.transaction(async (tx) => {
    // Update payment
    await tx.update('payments', paymentId, {
      status: 'captured',
      escrow: true
    });

    // Update order
    await tx.update('orders', order.id, {
      status: 'deposit_paid',
      depositStatus: 'paid',
      depositPaidAt: new Date()
    });
  });

  // Notify seller
  await notifySeller(order.sellerId, {
    type: 'order.deposit_paid',
    orderCode: order.orderCode,
    depositAmount: order.depositAmount,
    deadline: addHours(new Date(), 24) // 24h to confirm
  });

  // Schedule seller confirmation reminder
  await scheduleReminder(order.id, 'seller_confirm_reminder', addHours(new Date(), 12));

  // Schedule escalation if no confirmation
  await scheduleJob('escalate_unconfirmed_order', order.id, addHours(new Date(), 24));
}

// Pickup and weight verification
async function handlePickup(order: Order): Promise<void> {
  // Create shipment
  const shipment = await createShipment({
    orderId: order.id,
    shipmentType: 'live_animal', // or 'processed_meat'
    declaredWeightKg: order.declaredWeightKg,
    pickupAddress: order.pickupAddress,
    deliveryAddress: order.deliveryAddress,
    scheduledPickupAt: order.pickupDate
  });

  // At actual pickup - driver records weight
  async function recordPickupWeight(
    shipmentId: string,
    actualWeightKg: number,
    photos: string[]
  ): Promise<void> {
    const shipment = await getShipment(shipmentId);
    const order = await getOrder(shipment.orderId);

    // Calculate variance (BR-ORD-030)
    const variance = Math.abs(actualWeightKg - order.declaredWeightKg) / order.declaredWeightKg * 100;

    if (variance > 5) {
      // Create auto dispute
      await createDispute({
        orderId: order.id,
        disputeType: 'weight_discrepancy',
        declaredWeightKg: order.declaredWeightKg,
        actualWeightKg,
        weightVariancePercent: variance
      });

      await notifyBoth(order, {
        type: 'weight_discrepancy',
        variance,
        declaredWeight: order.declaredWeightKg,
        actualWeight: actualWeightKg
      });
    }

    // Update order with actual weight
    await db.update('orders', order.id, {
      actualWeightKg,
      weightVariancePercent: variance,
      finalAmount: actualWeightKg * order.pricePerKg + order.shippingFee - order.depositAmount
    });

    // Update shipment
    await db.update('shipments', shipmentId, {
      pickupWeightKg: actualWeightKg,
      pickupPhotos: photos,
      actualPickupAt: new Date(),
      status: 'in_transit'
    });

    // Update order status
    await db.update('orders', order.id, {
      status: 'in_transit'
    });
  }
}

// Delivery and completion
async function handleDeliveryConfirmation(order: Order): Promise<void> {
  // Auto-complete after 48h if no dispute (BR-ORD-041)
  const deliveredAt = order.shipment.actualDeliveryAt;
  const hoursSinceDelivery = (Date.now() - deliveredAt.getTime()) / (1000 * 60 * 60);

  if (hoursSinceDelivery >= 48) {
    const hasOpenDispute = await checkOpenDispute(order.id);
    if (!hasOpenDispute) {
      await completeOrder(order.id);
    }
  }
}

async function completeOrder(orderId: string): Promise<void> {
  const order = await getOrder(orderId);

  await db.transaction(async (tx) => {
    // Update order
    await tx.update('orders', orderId, {
      status: 'completed',
      completedAt: new Date()
    });

    // Release escrow to seller (BR-ORD-060)
    const payment = await getEscrowPayment(orderId);
    const releaseAmount = order.finalAmount - order.platformFee;

    await tx.update('payments', payment.id, {
      escrowReleased: true,
      escrowReleasedAt: new Date(),
      escrowReleaseTo: order.sellerId
    });

    // Create payout to seller
    await createPayout(order.sellerId, releaseAmount);

    // Update farm stats
    await tx.increment('farms', order.listing.farmId, 'totalOrders');
  });

  // Notify both parties
  await notifyBoth(order, {
    type: 'order.completed',
    orderCode: order.orderCode,
    finalAmount: order.finalAmount
  });

  // Request reviews
  await scheduleJob('request_review', order.id, addHours(new Date(), 24));
}
```

## Search and Discovery

```typescript
// Listing search with filters
interface ListingSearchParams {
  animalType?: AnimalType[];
  province?: string;
  district?: string;
  minPrice?: number;
  maxPrice?: number;
  sellingType?: SellingType[];
  certifications?: string[];
  breed?: string;
  minWeight?: number;
  maxWeight?: number;
  sortBy?: 'price' | 'created_at' | 'ending_soon' | 'popular';
  page?: number;
  limit?: number;
}

async function searchListings(params: ListingSearchParams): Promise<SearchResult> {
  const query = db.query('listings')
    .where('status', 'active')
    .join('farms', 'listings.farm_id', 'farms.id')
    .join('livestock', 'listings.livestock_id', 'livestock.id');

  // Apply filters
  if (params.animalType?.length) {
    query.whereIn('listings.animal_type', params.animalType);
  }

  if (params.province) {
    query.whereJsonPath('listings.pickup_location', '$.province', params.province);
  }

  if (params.minPrice) {
    query.where('listings.price_per_kg', '>=', params.minPrice);
  }

  if (params.maxPrice) {
    query.where('listings.price_per_kg', '<=', params.maxPrice);
  }

  if (params.sellingType?.length) {
    query.whereIn('listings.selling_type', params.sellingType);
  }

  if (params.certifications?.length) {
    query.whereJsonOverlaps('farms.certifications', params.certifications);
  }

  // Sorting
  switch (params.sortBy) {
    case 'price':
      query.orderBy('listings.price_per_kg', 'asc');
      break;
    case 'ending_soon':
      query.where('listings.selling_type', 'auction')
           .orderBy('listings.auction_end_at', 'asc');
      break;
    case 'popular':
      query.orderBy('listings.view_count', 'desc');
      break;
    default:
      query.orderBy('listings.created_at', 'desc');
  }

  // Pagination
  const offset = ((params.page || 1) - 1) * (params.limit || 20);
  query.limit(params.limit || 20).offset(offset);

  // Execute
  const [listings, total] = await Promise.all([
    query.execute(),
    query.count()
  ]);

  return {
    items: listings,
    total,
    page: params.page || 1,
    limit: params.limit || 20,
    totalPages: Math.ceil(total / (params.limit || 20))
  };
}
```

## Price Calculation Utilities

```typescript
// Platform fee calculation
function calculatePlatformFee(amount: number, farmTier: FarmTier): number {
  const feeRates = {
    premium: 0.02,  // 2%
    gold: 0.03,     // 3%
    standard: 0.05  // 5%
  };

  return Math.round(amount * feeRates[farmTier]);
}

// Deposit calculation (BR-ORD-010)
function calculateDeposit(totalAmount: number): number {
  if (totalAmount < 10000000) {
    return Math.round(totalAmount * 0.20); // 20% for < 10M
  }
  if (totalAmount < 50000000) {
    return Math.round(totalAmount * 0.15); // 15% for 10-50M
  }
  return Math.round(totalAmount * 0.10);   // 10% for > 50M
}

// Shipping estimate
async function estimateShipping(
  pickup: Location,
  buyerId: string
): Promise<number> {
  const delivery = await getBuyerDefaultAddress(buyerId);
  const distance = calculateDistance(pickup, delivery);

  // Base rate + per km rate
  const baseRate = 500000; // 500k base
  const perKmRate = 5000;  // 5k per km

  return baseRate + (distance * perKmRate);
}
```

## Testing Checklist

- [ ] Listing creation với all selling types
- [ ] Fixed price purchase flow
- [ ] Auction flow (covered in auction-patterns.md)
- [ ] Offer/counter-offer negotiation
- [ ] Order state transitions
- [ ] Deposit payment and deadline
- [ ] Weight verification at pickup
- [ ] Auto-complete after delivery
- [ ] Escrow release to seller
- [ ] Search and filtering
- [ ] Price calculations
