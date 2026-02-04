# Payment Integration Patterns

## Overview
Best practices for payment gateway integration in e-commerce.

## Key Patterns

### Pattern 1: Payment Gateway Abstraction
**When to use:** Supporting multiple payment providers
**Description:** Abstract payment operations behind interface
**Example:**
```typescript
interface PaymentGateway {
  createPaymentIntent(amount: Money, metadata: any): Promise<PaymentIntent>;
  confirmPayment(intentId: string): Promise<PaymentResult>;
  refund(paymentId: string, amount?: Money): Promise<RefundResult>;
  createCustomer(data: CustomerData): Promise<Customer>;
}

class StripeGateway implements PaymentGateway { ... }
class PayPalGateway implements PaymentGateway { ... }
class VNPayGateway implements PaymentGateway { ... }
```

### Pattern 2: Idempotent Payment Processing
**When to use:** Preventing duplicate charges
**Description:** Use idempotency keys for all payment operations
**Example:**
```typescript
const processPayment = async (orderId: string, amount: Money) => {
  const idempotencyKey = `order_${orderId}_${amount.amount}_${amount.currency}`;

  return stripe.paymentIntents.create({
    amount: amount.amount,
    currency: amount.currency,
  }, {
    idempotencyKey
  });
};
```

### Pattern 3: Webhook Handler Pattern
**When to use:** Processing async payment events
**Description:** Reliable webhook processing with retry logic
**Example:**
```typescript
const handleWebhook = async (event: WebhookEvent) => {
  // Verify signature
  const isValid = verifySignature(event);
  if (!isValid) throw new Error('Invalid signature');

  // Check idempotency
  const processed = await isEventProcessed(event.id);
  if (processed) return;

  // Process event
  await processEvent(event);

  // Mark as processed
  await markEventProcessed(event.id);
};
```

### Pattern 4: 3D Secure Flow
**When to use:** SCA compliance (EU) and fraud prevention
**Description:** Handle 3DS authentication flow
**Example:**
```typescript
const handle3DS = async (paymentIntent: PaymentIntent) => {
  if (paymentIntent.status === 'requires_action') {
    // Redirect to 3DS
    return {
      requiresAction: true,
      clientSecret: paymentIntent.client_secret
    };
  }
  return { success: true };
};
```

## Security Best Practices
- Never log full card numbers
- Use tokenization exclusively
- Implement PCI-DSS controls
- Rotate API keys regularly
- Monitor for suspicious activity

## Error Handling
```typescript
const paymentErrors = {
  'card_declined': 'Your card was declined',
  'insufficient_funds': 'Insufficient funds',
  'expired_card': 'Your card has expired',
  'processing_error': 'Please try again'
};
```

## Anti-Patterns to Avoid
- Storing CVV/CVC codes
- Processing payments without verification
- Not handling webhook failures
- Missing idempotency keys
- Ignoring PCI-DSS requirements
