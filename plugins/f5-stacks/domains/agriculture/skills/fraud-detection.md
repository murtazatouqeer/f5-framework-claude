# Fraud Detection - Livestock Marketplace

Skill hướng dẫn implement hệ thống phát hiện gian lận cho sàn nông sản.

## Overview

Các loại gian lận phổ biến trong sàn giao dịch gia súc/gia cầm:
1. **Shill Bidding** - Đẩy giá ảo trong đấu giá
2. **Weight Fraud** - Khai khống trọng lượng
3. **Quality Misrepresentation** - Mô tả sai chất lượng
4. **Fake Farm/Seller** - Tạo tài khoản giả
5. **Payment Fraud** - Gian lận thanh toán

## Entity References

- `knowledge/business-rules/fraud-prevention-rules.yaml` - Business rules
- `knowledge/entities/quality-check.yaml` - Quality check entity
- `knowledge/entities/dispute.yaml` - Dispute entity

## Detection Patterns

### 1. Shill Bidding Detection

```typescript
interface ShillBiddingDetector {
  // Score factors
  scoreFactors: {
    sameIP: 50,           // Cùng IP address
    sameDevice: 40,       // Cùng device fingerprint
    bidPattern: 30,       // Pattern bid qua lại
    accountAge: 20,       // Tài khoản mới
    bidTiming: 20,        // Bid vào phút cuối
    lowActivity: 15       // Tài khoản ít hoạt động
  };

  threshold: 60;  // Score >= 60 = flag for review
}

async function detectShillBidding(bid: Bid): Promise<FraudAlert | null> {
  let score = 0;
  const alerts: string[] = [];

  // 1. Check IP address overlap
  const ipOverlap = await checkIPOverlap(bid);
  if (ipOverlap.found) {
    score += 50;
    alerts.push(`Cùng IP với ${ipOverlap.accounts.join(', ')}`);
  }

  // 2. Check device fingerprint
  const deviceMatch = await checkDeviceFingerprint(bid);
  if (deviceMatch.found) {
    score += 40;
    alerts.push(`Cùng device với ${deviceMatch.accounts.join(', ')}`);
  }

  // 3. Check ping-pong bidding pattern
  const pingPong = await checkBidPattern(bid);
  if (pingPong.detected) {
    score += 30;
    alerts.push(`Pattern bid qua lại với ${pingPong.otherBidder}`);
  }

  // 4. Check account age
  const bidder = await getUser(bid.bidderId);
  if (daysSince(bidder.createdAt) < 7) {
    score += 20;
    alerts.push('Tài khoản mới < 7 ngày');
  }

  // 5. Check bid timing
  const auction = await getAuction(bid.auctionId);
  const remainingSeconds = (auction.endAt.getTime() - bid.createdAt.getTime()) / 1000;
  if (remainingSeconds < 60) {
    score += 20;
    alerts.push('Bid trong 60 giây cuối');
  }

  // 6. Check account activity
  const activityScore = await getAccountActivityScore(bid.bidderId);
  if (activityScore < 0.3) {
    score += 15;
    alerts.push('Tài khoản ít hoạt động');
  }

  if (score >= 60) {
    return {
      type: 'shill_bidding',
      bidId: bid.id,
      score,
      alerts,
      severity: score >= 80 ? 'high' : 'medium',
      action: score >= 80 ? 'block_and_review' : 'flag_for_review'
    };
  }

  return null;
}

// IP overlap check with cross-listing analysis
async function checkIPOverlap(bid: Bid): Promise<{ found: boolean; accounts: string[] }> {
  const result = await db.query(`
    WITH seller_id AS (
      SELECT f.owner_id
      FROM auctions a
      JOIN listings l ON a.listing_id = l.id
      JOIN farms f ON l.farm_id = f.id
      WHERE a.id = $1
    )
    SELECT DISTINCT b2.bidder_id
    FROM bids b1
    JOIN bids b2 ON b1.ip_address = b2.ip_address
    JOIN auctions a2 ON b2.auction_id = a2.id
    JOIN listings l2 ON a2.listing_id = l2.id
    JOIN farms f2 ON l2.farm_id = f2.id
    WHERE b1.id = $2
      AND b2.bidder_id = f2.owner_id
      AND b2.auction_id != $1
  `, [bid.auctionId, bid.id]);

  return {
    found: result.length > 0,
    accounts: result.map(r => r.bidder_id)
  };
}
```

### 2. Weight Fraud Detection

```typescript
interface WeightFraudDetector {
  // Variance thresholds
  warningThreshold: 3;     // % - show warning
  alertThreshold: 5;       // % - flag for review
  blockThreshold: 10;      // % - block transaction
}

async function detectWeightFraud(order: Order, shipment: Shipment): Promise<WeightAlert | null> {
  const declaredWeight = order.declaredWeightKg;
  const actualWeight = shipment.pickupWeightKg;

  const variance = Math.abs(actualWeight - declaredWeight) / declaredWeight * 100;

  if (variance >= 10) {
    // Critical - block transaction
    return {
      type: 'weight_fraud',
      severity: 'critical',
      variance,
      declaredWeight,
      actualWeight,
      action: 'block_transaction',
      message: `Chênh lệch ${variance.toFixed(1)}% - Giao dịch bị tạm dừng`
    };
  }

  if (variance >= 5) {
    // Alert - create auto dispute
    return {
      type: 'weight_discrepancy',
      severity: 'high',
      variance,
      action: 'create_dispute',
      message: `Chênh lệch ${variance.toFixed(1)}% - Đang tạo khiếu nại tự động`
    };
  }

  if (variance >= 3) {
    // Warning - notify buyer
    return {
      type: 'weight_warning',
      severity: 'medium',
      variance,
      action: 'notify_buyer',
      message: `Chênh lệch ${variance.toFixed(1)}% - Buyer được thông báo`
    };
  }

  return null;
}

// Historical weight accuracy analysis
async function analyzeSellerWeightAccuracy(farmId: string): Promise<AccuracyReport> {
  const orders = await db.query(`
    SELECT
      o.declared_weight_kg,
      s.pickup_weight_kg,
      ABS(s.pickup_weight_kg - o.declared_weight_kg) / o.declared_weight_kg * 100 as variance
    FROM orders o
    JOIN shipments s ON o.id = s.order_id
    WHERE o.seller_id IN (SELECT owner_id FROM farms WHERE id = $1)
      AND o.status = 'completed'
      AND o.created_at > NOW() - INTERVAL '90 days'
  `, [farmId]);

  const avgVariance = mean(orders.map(o => o.variance));
  const overReportCount = orders.filter(o => o.declared_weight_kg > o.pickup_weight_kg).length;
  const overReportRate = overReportCount / orders.length * 100;

  return {
    totalOrders: orders.length,
    avgVariance,
    overReportRate,
    trustScore: calculateTrustScore(avgVariance, overReportRate),
    recommendation: getRecommendation(avgVariance, overReportRate)
  };
}

function calculateTrustScore(avgVariance: number, overReportRate: number): number {
  // Score từ 0-100
  let score = 100;

  // Trừ điểm theo variance
  score -= avgVariance * 5; // -5 điểm mỗi 1% variance

  // Trừ điểm theo over-report rate
  score -= overReportRate * 0.5; // -0.5 điểm mỗi 1% over-report

  return Math.max(0, Math.min(100, score));
}
```

### 3. Quality Misrepresentation Detection

```typescript
interface QualityFraudDetector {
  // Compare claimed vs actual
  async compareQuality(
    listing: Listing,
    qualityCheck: QualityCheck
  ): Promise<QualityAlert | null> {
    const issues: QualityIssue[] = [];

    // 1. Age verification
    const claimedAge = listing.ageDays;
    const estimatedAge = qualityCheck.estimatedAgeDays;
    if (Math.abs(claimedAge - estimatedAge) > 7) {
      issues.push({
        type: 'age_mismatch',
        claimed: claimedAge,
        actual: estimatedAge,
        severity: 'medium'
      });
    }

    // 2. Breed verification
    if (qualityCheck.verifiedBreed !== listing.breed) {
      issues.push({
        type: 'breed_mismatch',
        claimed: listing.breed,
        actual: qualityCheck.verifiedBreed,
        severity: 'high'
      });
    }

    // 3. Health status
    if (qualityCheck.healthIssues.length > 0 && listing.livestock.healthStatus === 'healthy') {
      issues.push({
        type: 'health_misrepresentation',
        claimed: 'healthy',
        actual: qualityCheck.healthIssues,
        severity: 'critical'
      });
    }

    // 4. Feed type verification
    if (!verifyFeedType(qualityCheck.feedAnalysis, listing.feedType)) {
      issues.push({
        type: 'feed_mismatch',
        claimed: listing.feedType,
        actual: qualityCheck.feedAnalysis,
        severity: 'medium'
      });
    }

    if (issues.length > 0) {
      const severity = getMaxSeverity(issues);
      return {
        type: 'quality_misrepresentation',
        issues,
        severity,
        action: severity === 'critical' ? 'block_and_refund' : 'create_dispute'
      };
    }

    return null;
  }
}

// Image verification using ML
async function verifyListingImages(listing: Listing): Promise<ImageVerificationResult> {
  const results: ImageCheck[] = [];

  for (const image of listing.images) {
    // 1. Check for stock photos
    const stockCheck = await checkStockPhoto(image);
    if (stockCheck.isStock) {
      results.push({
        image,
        issue: 'stock_photo',
        confidence: stockCheck.confidence
      });
    }

    // 2. Check for reused images
    const reuseCheck = await checkImageReuse(image, listing.farmId);
    if (reuseCheck.reused) {
      results.push({
        image,
        issue: 'reused_image',
        originalListing: reuseCheck.originalListingId
      });
    }

    // 3. Verify animal type matches
    const animalCheck = await classifyAnimal(image);
    if (animalCheck.type !== listing.animalType) {
      results.push({
        image,
        issue: 'wrong_animal_type',
        claimed: listing.animalType,
        detected: animalCheck.type
      });
    }

    // 4. Check metadata for location/date
    const metadata = await extractImageMetadata(image);
    if (metadata.location && !isNearFarm(metadata.location, listing.farm)) {
      results.push({
        image,
        issue: 'location_mismatch',
        imageLocation: metadata.location,
        farmLocation: listing.farm.address
      });
    }
  }

  return {
    totalImages: listing.images.length,
    issues: results,
    trustScore: (listing.images.length - results.length) / listing.images.length * 100
  };
}
```

### 4. Account Fraud Detection

```typescript
interface AccountFraudDetector {
  // Detect fake/duplicate accounts
  async detectFakeAccount(user: User): Promise<AccountAlert | null> {
    const flags: AccountFlag[] = [];

    // 1. Phone number pattern
    const phoneAnalysis = await analyzePhoneNumber(user.phone);
    if (phoneAnalysis.isVoIP || phoneAnalysis.isDisposable) {
      flags.push({
        type: 'suspicious_phone',
        detail: phoneAnalysis.reason
      });
    }

    // 2. Check for duplicate accounts
    const duplicates = await findDuplicateAccounts(user);
    if (duplicates.length > 0) {
      flags.push({
        type: 'duplicate_account',
        relatedAccounts: duplicates
      });
    }

    // 3. Email domain analysis
    const emailAnalysis = await analyzeEmail(user.email);
    if (emailAnalysis.isDisposable || emailAnalysis.isDomainSuspicious) {
      flags.push({
        type: 'suspicious_email',
        detail: emailAnalysis.reason
      });
    }

    // 4. Registration behavior
    const regBehavior = await analyzeRegistrationBehavior(user);
    if (regBehavior.suspicious) {
      flags.push({
        type: 'suspicious_registration',
        detail: regBehavior.reason
      });
    }

    // 5. Farm verification documents
    if (user.role === 'farmer') {
      const docCheck = await verifyFarmDocuments(user);
      if (!docCheck.valid) {
        flags.push({
          type: 'invalid_documents',
          detail: docCheck.issues
        });
      }
    }

    if (flags.length > 0) {
      return {
        userId: user.id,
        flags,
        riskScore: calculateAccountRiskScore(flags),
        recommendation: getAccountRecommendation(flags)
      };
    }

    return null;
  }
}

// Duplicate detection using similarity
async function findDuplicateAccounts(user: User): Promise<DuplicateAccount[]> {
  const candidates = await db.query(`
    SELECT
      u.*,
      CASE
        WHEN u.phone = $1 THEN 100
        WHEN u.device_fingerprint = $2 THEN 90
        WHEN u.ip_address = $3 THEN 70
        WHEN SIMILARITY(u.name, $4) > 0.8 THEN 50
        ELSE 0
      END as similarity_score
    FROM users u
    WHERE u.id != $5
      AND (
        u.phone = $1
        OR u.device_fingerprint = $2
        OR u.ip_address = $3
        OR SIMILARITY(u.name, $4) > 0.8
      )
    ORDER BY similarity_score DESC
  `, [user.phone, user.deviceFingerprint, user.ipAddress, user.name, user.id]);

  return candidates.map(c => ({
    userId: c.id,
    similarityScore: c.similarity_score,
    matchReason: determineMatchReason(c, user)
  }));
}
```

### 5. Real-time Fraud Scoring

```typescript
interface FraudScorer {
  // Real-time transaction scoring
  async scoreTransaction(transaction: Transaction): Promise<FraudScore> {
    const factors: ScoringFactor[] = [];

    // 1. User trust score
    const userScore = await getUserTrustScore(transaction.userId);
    factors.push({ name: 'user_trust', score: userScore, weight: 0.25 });

    // 2. Transaction pattern score
    const patternScore = await analyzeTransactionPattern(transaction);
    factors.push({ name: 'transaction_pattern', score: patternScore, weight: 0.20 });

    // 3. Device/IP score
    const deviceScore = await analyzeDeviceIP(transaction);
    factors.push({ name: 'device_ip', score: deviceScore, weight: 0.15 });

    // 4. Velocity score (transaction frequency)
    const velocityScore = await checkVelocity(transaction);
    factors.push({ name: 'velocity', score: velocityScore, weight: 0.15 });

    // 5. Amount anomaly score
    const amountScore = await analyzeAmount(transaction);
    factors.push({ name: 'amount', score: amountScore, weight: 0.15 });

    // 6. Time of day score
    const timeScore = analyzeTransactionTime(transaction);
    factors.push({ name: 'time', score: timeScore, weight: 0.10 });

    // Calculate weighted score
    const totalScore = factors.reduce((sum, f) => sum + f.score * f.weight, 0);

    return {
      score: totalScore,
      factors,
      riskLevel: getRiskLevel(totalScore),
      action: getRecommendedAction(totalScore),
      requiresReview: totalScore < 50
    };
  }
}

function getRiskLevel(score: number): RiskLevel {
  if (score >= 80) return 'low';
  if (score >= 60) return 'medium';
  if (score >= 40) return 'high';
  return 'critical';
}

function getRecommendedAction(score: number): FraudAction {
  if (score >= 80) return 'allow';
  if (score >= 60) return 'allow_with_monitoring';
  if (score >= 40) return 'require_verification';
  return 'block';
}
```

## Reporting Dashboard

```typescript
interface FraudDashboard {
  // Daily fraud summary
  async getDailySummary(date: Date): Promise<FraudSummary> {
    return {
      totalTransactions: await countTransactions(date),
      flaggedTransactions: await countFlagged(date),
      blockedTransactions: await countBlocked(date),
      fraudTypes: await getFraudTypeBreakdown(date),
      topRiskyAccounts: await getTopRiskyAccounts(date, 10),
      falsePositiveRate: await calculateFalsePositiveRate(date)
    };
  }

  // Trend analysis
  async getFraudTrends(days: number): Promise<FraudTrend[]> {
    // Time series of fraud metrics
  }
}
```

## Testing Checklist

- [ ] Shill bidding detection với various patterns
- [ ] Weight variance alerts at correct thresholds
- [ ] Quality mismatch detection
- [ ] Duplicate account detection
- [ ] Real-time scoring performance
- [ ] False positive rate monitoring
- [ ] Admin review workflow
- [ ] Auto-block functionality
