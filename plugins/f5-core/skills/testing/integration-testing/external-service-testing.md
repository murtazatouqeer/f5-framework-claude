---
name: external-service-testing
description: Testing external service integrations
category: testing/integration-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# External Service Testing

## Overview

Testing code that integrates with external services (APIs, payment
gateways, email providers) requires special strategies to maintain
test reliability and speed.

## Strategies Comparison

| Strategy | Speed | Reliability | Realism | Cost |
|----------|-------|-------------|---------|------|
| Mock | Fast | High | Low | Free |
| Record/Replay | Fast | High | Medium | Free |
| Test Server | Medium | High | Medium | Low |
| Sandbox | Slow | Medium | High | Varies |
| Real Service | Slow | Low | High | High |

## Mock External Services

### Creating Service Mocks

```typescript
// Mock at the adapter level
interface PaymentGateway {
  charge(amount: number, token: string): Promise<PaymentResult>;
  refund(transactionId: string): Promise<RefundResult>;
}

// Test mock implementation
class MockPaymentGateway implements PaymentGateway {
  private transactions: Map<string, { amount: number; status: string }> = new Map();

  async charge(amount: number, token: string): Promise<PaymentResult> {
    // Simulate validation
    if (token === 'invalid_token') {
      throw new PaymentError('Invalid card token');
    }

    if (token === 'insufficient_funds') {
      return {
        success: false,
        error: 'Insufficient funds',
      };
    }

    const transactionId = `txn_${Date.now()}`;
    this.transactions.set(transactionId, { amount, status: 'charged' });

    return {
      success: true,
      transactionId,
      amount,
    };
  }

  async refund(transactionId: string): Promise<RefundResult> {
    const transaction = this.transactions.get(transactionId);

    if (!transaction) {
      throw new PaymentError('Transaction not found');
    }

    transaction.status = 'refunded';

    return {
      success: true,
      refundId: `ref_${Date.now()}`,
    };
  }

  // Test helpers
  getTransaction(id: string) {
    return this.transactions.get(id);
  }

  clear() {
    this.transactions.clear();
  }
}
```

### Using Mocks in Tests

```typescript
describe('PaymentService with Mock Gateway', () => {
  let paymentService: PaymentService;
  let mockGateway: MockPaymentGateway;

  beforeEach(() => {
    mockGateway = new MockPaymentGateway();
    paymentService = new PaymentService(mockGateway);
  });

  afterEach(() => {
    mockGateway.clear();
  });

  it('should process payment successfully', async () => {
    const result = await paymentService.processPayment({
      amount: 100,
      cardToken: 'valid_token',
    });

    expect(result.success).toBe(true);
    expect(result.transactionId).toBeDefined();
  });

  it('should handle insufficient funds', async () => {
    const result = await paymentService.processPayment({
      amount: 100,
      cardToken: 'insufficient_funds',
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('Insufficient funds');
  });

  it('should refund successful charge', async () => {
    const charge = await paymentService.processPayment({
      amount: 100,
      cardToken: 'valid_token',
    });

    const refund = await paymentService.refundPayment(charge.transactionId);

    expect(refund.success).toBe(true);
    expect(mockGateway.getTransaction(charge.transactionId)?.status).toBe('refunded');
  });
});
```

## Record/Replay (VCR Pattern)

### Using Nock for HTTP Recording

```typescript
import nock from 'nock';
import path from 'path';

// Record mode
nock.recorder.rec({
  output_objects: true,
  dont_print: true,
});

// After recording, save fixtures
const recordings = nock.recorder.play();
fs.writeFileSync(
  'fixtures/api-responses.json',
  JSON.stringify(recordings, null, 2)
);

// Replay mode
beforeEach(() => {
  nock.cleanAll();

  const fixtures = require('./fixtures/api-responses.json');
  fixtures.forEach(fixture => {
    nock(fixture.scope)
      .intercept(fixture.path, fixture.method)
      .reply(fixture.status, fixture.response, fixture.headers);
  });
});

afterEach(() => {
  nock.cleanAll();
});
```

### Custom VCR Implementation

```typescript
// test/helpers/vcr.ts
import fs from 'fs';
import path from 'path';
import nock from 'nock';

interface CassetteOptions {
  name: string;
  mode?: 'record' | 'replay' | 'none';
}

export function useCassette(options: CassetteOptions) {
  const cassettePath = path.join(__dirname, '../fixtures', `${options.name}.json`);
  const mode = options.mode || (process.env.VCR_MODE as any) || 'replay';

  beforeEach(() => {
    if (mode === 'replay' && fs.existsSync(cassettePath)) {
      const recordings = JSON.parse(fs.readFileSync(cassettePath, 'utf8'));
      recordings.forEach(rec => {
        nock(rec.scope)
          .intercept(rec.path, rec.method)
          .reply(rec.status, rec.response);
      });
    } else if (mode === 'record') {
      nock.recorder.rec({ output_objects: true, dont_print: true });
    }
  });

  afterEach(() => {
    if (mode === 'record') {
      const recordings = nock.recorder.play();
      fs.writeFileSync(cassettePath, JSON.stringify(recordings, null, 2));
      nock.recorder.clear();
    }
    nock.cleanAll();
  });
}

// Usage
describe('GitHub API Integration', () => {
  useCassette({ name: 'github-repos' });

  it('should fetch user repositories', async () => {
    const repos = await githubClient.getRepos('octocat');
    expect(repos).toBeInstanceOf(Array);
  });
});
```

## Test Servers (WireMock/MockServer)

### Using MSW (Mock Service Worker)

```typescript
import { setupServer } from 'msw/node';
import { rest } from 'msw';

const server = setupServer(
  // Mock external API endpoints
  rest.get('https://api.stripe.com/v1/charges', (req, res, ctx) => {
    return res(
      ctx.json({
        data: [
          { id: 'ch_1', amount: 1000, status: 'succeeded' },
        ],
      })
    );
  }),

  rest.post('https://api.stripe.com/v1/charges', (req, res, ctx) => {
    const body = req.body as any;

    if (body.amount > 100000) {
      return res(
        ctx.status(400),
        ctx.json({ error: { message: 'Amount too large' } })
      );
    }

    return res(
      ctx.json({
        id: 'ch_' + Date.now(),
        amount: body.amount,
        status: 'succeeded',
      })
    );
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Stripe Integration', () => {
  it('should create charge', async () => {
    const stripeClient = new StripeClient(process.env.STRIPE_KEY);

    const charge = await stripeClient.createCharge({
      amount: 1000,
      currency: 'usd',
    });

    expect(charge.status).toBe('succeeded');
  });

  it('should handle large amount error', async () => {
    const stripeClient = new StripeClient(process.env.STRIPE_KEY);

    await expect(
      stripeClient.createCharge({ amount: 200000, currency: 'usd' })
    ).rejects.toThrow('Amount too large');
  });
});
```

## Sandbox/Test Environment

### Using Provider Sandboxes

```typescript
// test/config/external-services.ts
export const externalServicesConfig = {
  stripe: {
    // Use Stripe test mode
    apiKey: process.env.STRIPE_TEST_KEY,
    webhookSecret: process.env.STRIPE_TEST_WEBHOOK_SECRET,
  },
  sendgrid: {
    // Use SendGrid sandbox
    apiKey: process.env.SENDGRID_TEST_KEY,
    sandboxMode: true,
  },
  twilio: {
    // Use Twilio test credentials
    accountSid: process.env.TWILIO_TEST_SID,
    authToken: process.env.TWILIO_TEST_TOKEN,
    testPhoneNumber: '+15005550006', // Magic test number
  },
};

// Test with real sandbox
describe('Stripe Sandbox Integration', () => {
  const stripe = new Stripe(externalServicesConfig.stripe.apiKey);

  it('should create test charge with test card', async () => {
    const paymentMethod = await stripe.paymentMethods.create({
      type: 'card',
      card: {
        number: '4242424242424242', // Test card
        exp_month: 12,
        exp_year: 2025,
        cvc: '123',
      },
    });

    const paymentIntent = await stripe.paymentIntents.create({
      amount: 1000,
      currency: 'usd',
      payment_method: paymentMethod.id,
      confirm: true,
    });

    expect(paymentIntent.status).toBe('succeeded');
  });

  it('should handle declined card', async () => {
    const paymentMethod = await stripe.paymentMethods.create({
      type: 'card',
      card: {
        number: '4000000000000002', // Card that declines
        exp_month: 12,
        exp_year: 2025,
        cvc: '123',
      },
    });

    await expect(
      stripe.paymentIntents.create({
        amount: 1000,
        currency: 'usd',
        payment_method: paymentMethod.id,
        confirm: true,
      })
    ).rejects.toThrow(/declined/i);
  });
});
```

## Contract Testing

### Using Pact

```typescript
import { PactV3, MatchersV3 } from '@pact-foundation/pact';

const provider = new PactV3({
  consumer: 'OrderService',
  provider: 'PaymentService',
});

describe('Payment Service Contract', () => {
  it('should process payment', async () => {
    await provider
      .given('a valid payment request')
      .uponReceiving('a request to process payment')
      .withRequest({
        method: 'POST',
        path: '/payments',
        headers: { 'Content-Type': 'application/json' },
        body: {
          amount: MatchersV3.integer(100),
          currency: MatchersV3.string('USD'),
          cardToken: MatchersV3.string('tok_visa'),
        },
      })
      .willRespondWith({
        status: 201,
        headers: { 'Content-Type': 'application/json' },
        body: {
          id: MatchersV3.uuid(),
          status: MatchersV3.string('succeeded'),
          amount: MatchersV3.integer(),
        },
      });

    await provider.executeTest(async (mockServer) => {
      const client = new PaymentClient(mockServer.url);

      const result = await client.processPayment({
        amount: 100,
        currency: 'USD',
        cardToken: 'tok_visa',
      });

      expect(result.status).toBe('succeeded');
    });
  });
});
```

## Testing Webhooks

```typescript
describe('Stripe Webhooks', () => {
  const webhookSecret = 'whsec_test_secret';

  function generateWebhookSignature(payload: string, secret: string): string {
    const timestamp = Math.floor(Date.now() / 1000);
    const signedPayload = `${timestamp}.${payload}`;
    const signature = crypto
      .createHmac('sha256', secret)
      .update(signedPayload)
      .digest('hex');
    return `t=${timestamp},v1=${signature}`;
  }

  it('should handle payment_intent.succeeded webhook', async () => {
    const payload = JSON.stringify({
      type: 'payment_intent.succeeded',
      data: {
        object: {
          id: 'pi_123',
          amount: 1000,
          status: 'succeeded',
        },
      },
    });

    const signature = generateWebhookSignature(payload, webhookSecret);

    const response = await request(app.getHttpServer())
      .post('/webhooks/stripe')
      .set('Stripe-Signature', signature)
      .send(payload)
      .expect(200);

    // Verify order was updated
    const order = await findOrderByPaymentIntent('pi_123');
    expect(order?.status).toBe('paid');
  });

  it('should reject invalid signature', async () => {
    const payload = JSON.stringify({ type: 'test' });

    await request(app.getHttpServer())
      .post('/webhooks/stripe')
      .set('Stripe-Signature', 'invalid_signature')
      .send(payload)
      .expect(400);
  });
});
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Wrap external clients | Don't mock libraries directly |
| Use sandbox environments | For critical integrations |
| Record real responses | Keep fixtures up to date |
| Test failure scenarios | Timeouts, errors, rate limits |
| Contract tests | Ensure API compatibility |
| Webhook testing | Verify signature validation |

## Related Topics

- [Integration Test Basics](./integration-test-basics.md)
- [Contract Testing](../advanced/contract-testing.md)
- [Mocking Strategies](../unit-testing/mocking-strategies.md)
