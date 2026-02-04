---
name: contract-testing
description: Contract testing for API compatibility
category: testing/advanced
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Contract Testing

## Overview

Contract testing verifies that two services can communicate correctly
by testing against a shared contract rather than the actual services.

## Why Contract Testing?

```
┌─────────────────────────────────────────────────────────────────┐
│                    Traditional Integration Testing               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Consumer ────────────────────────────▶ Provider               │
│                                                                  │
│   Problems:                                                      │
│   - Provider must be running                                    │
│   - Tests are slow                                              │
│   - Flaky due to network                                        │
│   - Provider changes break consumer tests                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Contract Testing                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Consumer ──────▶ Contract ◀────── Provider                    │
│                      │                                           │
│   Benefits:          ▼                                           │
│   - No provider needed      ┌─────────────────┐                │
│   - Fast tests              │  Shared Contract │                │
│   - Reliable                │  (Pact file)     │                │
│   - Early detection         └─────────────────┘                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Consumer-Driven Contracts

The consumer defines expectations, provider verifies them.

### Consumer Side (Pact.js)

```typescript
// consumer/user-client.pact.spec.ts
import { PactV3, MatchersV3 } from '@pact-foundation/pact';
import { UserClient } from './user-client';

const { like, eachLike, regex, integer, string, uuid } = MatchersV3;

const provider = new PactV3({
  consumer: 'WebApp',
  provider: 'UserService',
  logLevel: 'warn',
});

describe('UserClient Contract', () => {
  describe('GET /users/:id', () => {
    it('should return user when exists', async () => {
      // Define the expected interaction
      await provider
        .given('user with id 123 exists')
        .uponReceiving('a request for user 123')
        .withRequest({
          method: 'GET',
          path: '/users/123',
          headers: {
            Accept: 'application/json',
          },
        })
        .willRespondWith({
          status: 200,
          headers: {
            'Content-Type': 'application/json',
          },
          body: {
            id: like('123'),
            name: string('John Doe'),
            email: regex(/.*@.*/, 'john@example.com'),
            createdAt: like('2024-01-01T00:00:00Z'),
          },
        });

      // Execute test
      await provider.executeTest(async (mockServer) => {
        const client = new UserClient(mockServer.url);
        const user = await client.getUser('123');

        expect(user.id).toBe('123');
        expect(user.name).toBeDefined();
        expect(user.email).toMatch(/@/);
      });
    });

    it('should return 404 when user not found', async () => {
      await provider
        .given('user with id 999 does not exist')
        .uponReceiving('a request for non-existent user')
        .withRequest({
          method: 'GET',
          path: '/users/999',
        })
        .willRespondWith({
          status: 404,
          body: {
            error: string('User not found'),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const client = new UserClient(mockServer.url);

        await expect(client.getUser('999')).rejects.toThrow('User not found');
      });
    });
  });

  describe('POST /users', () => {
    it('should create user', async () => {
      await provider
        .given('no user exists')
        .uponReceiving('a request to create a user')
        .withRequest({
          method: 'POST',
          path: '/users',
          headers: {
            'Content-Type': 'application/json',
          },
          body: {
            name: string('Jane Doe'),
            email: regex(/.*@.*/, 'jane@example.com'),
          },
        })
        .willRespondWith({
          status: 201,
          body: {
            id: uuid(),
            name: like('Jane Doe'),
            email: like('jane@example.com'),
            createdAt: like('2024-01-01T00:00:00Z'),
          },
        });

      await provider.executeTest(async (mockServer) => {
        const client = new UserClient(mockServer.url);
        const user = await client.createUser({
          name: 'Jane Doe',
          email: 'jane@example.com',
        });

        expect(user.id).toBeDefined();
        expect(user.name).toBe('Jane Doe');
      });
    });
  });
});
```

### Provider Side (Verification)

```typescript
// provider/user-service.pact.spec.ts
import { Verifier } from '@pact-foundation/pact';
import { app } from './app';

describe('UserService Contract Verification', () => {
  let server: any;

  beforeAll(async () => {
    server = app.listen(3001);
  });

  afterAll(async () => {
    server.close();
  });

  it('should validate contracts', async () => {
    const verifier = new Verifier({
      provider: 'UserService',
      providerBaseUrl: 'http://localhost:3001',

      // Contract source
      pactUrls: ['./pacts/webapp-userservice.json'],
      // Or from Pact Broker
      // pactBrokerUrl: 'https://your-pact-broker.com',
      // pactBrokerUsername: process.env.PACT_BROKER_USERNAME,
      // pactBrokerPassword: process.env.PACT_BROKER_PASSWORD,

      // State handlers
      stateHandlers: {
        'user with id 123 exists': async () => {
          await seedUser({ id: '123', name: 'John Doe', email: 'john@example.com' });
        },
        'user with id 999 does not exist': async () => {
          await clearUsers();
        },
        'no user exists': async () => {
          await clearUsers();
        },
      },

      // Request filtering (for auth headers etc)
      requestFilter: (req, res, next) => {
        req.headers['Authorization'] = 'Bearer test-token';
        next();
      },
    });

    await verifier.verifyProvider();
  });
});
```

## Pact Matchers

### Type Matchers

```typescript
import { MatchersV3 } from '@pact-foundation/pact';

const {
  like,           // Matches type, not value
  eachLike,       // Array with matching elements
  atLeastOneLike, // Array with at least one element
  atLeastLike,    // Array with minimum elements
  atMostLike,     // Array with maximum elements
  integer,        // Integer type
  decimal,        // Decimal type
  boolean,        // Boolean type
  string,         // String type
  regex,          // Matches regex pattern
  datetime,       // Date/time format
  uuid,           // UUID format
  nullValue,      // Null
  includes,       // Contains substring
} = MatchersV3;

// Complex matching example
const userMatcher = {
  id: uuid(),
  name: string('John'),
  age: integer(25),
  score: decimal(98.5),
  active: boolean(true),
  email: regex(/^[\w-]+@[\w-]+\.\w+$/, 'test@example.com'),
  createdAt: datetime("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", '2024-01-01T00:00:00.000Z'),
  tags: eachLike('tag1'),
  address: like({
    street: string('123 Main St'),
    city: string('New York'),
    zip: regex(/^\d{5}$/, '12345'),
  }),
  orders: atLeastOneLike({
    id: uuid(),
    total: decimal(99.99),
  }),
};
```

## Pact Broker Integration

```typescript
// CI configuration
const verifier = new Verifier({
  provider: 'UserService',
  providerVersion: process.env.GIT_SHA,
  providerVersionBranch: process.env.GIT_BRANCH,

  // Pact Broker settings
  pactBrokerUrl: 'https://your-broker.pactflow.io',
  pactBrokerToken: process.env.PACT_BROKER_TOKEN,

  // Consumer version selectors
  consumerVersionSelectors: [
    { mainBranch: true },      // Main branch consumers
    { deployedOrReleased: true }, // Deployed consumers
  ],

  // Enable pending pacts
  enablePending: true,

  // Include WIP pacts
  includeWipPactsSince: '2024-01-01',

  // Publish results
  publishVerificationResult: true,
});
```

## Can-I-Deploy

```bash
# Check if safe to deploy consumer
pact-broker can-i-deploy \
  --pacticipant WebApp \
  --version $(git rev-parse HEAD) \
  --to-environment production

# Check if safe to deploy provider
pact-broker can-i-deploy \
  --pacticipant UserService \
  --version $(git rev-parse HEAD) \
  --to-environment production
```

## GraphQL Contract Testing

```typescript
import { PactV3 } from '@pact-foundation/pact';

const provider = new PactV3({
  consumer: 'WebApp',
  provider: 'GraphQLService',
});

describe('GraphQL Contract', () => {
  it('should query user', async () => {
    const graphqlQuery = `
      query GetUser($id: ID!) {
        user(id: $id) {
          id
          name
          email
        }
      }
    `;

    await provider
      .given('user exists')
      .uponReceiving('a GraphQL query for user')
      .withRequest({
        method: 'POST',
        path: '/graphql',
        headers: { 'Content-Type': 'application/json' },
        body: {
          query: graphqlQuery,
          variables: { id: '123' },
        },
      })
      .willRespondWith({
        status: 200,
        body: {
          data: {
            user: {
              id: like('123'),
              name: string('John'),
              email: string('john@example.com'),
            },
          },
        },
      });

    await provider.executeTest(async (mockServer) => {
      // Test GraphQL client
    });
  });
});
```

## Message Contract Testing

```typescript
import { MessageConsumerPact } from '@pact-foundation/pact';

describe('Message Contract', () => {
  const messagePact = new MessageConsumerPact({
    consumer: 'OrderProcessor',
    provider: 'OrderService',
  });

  describe('order created message', () => {
    it('should handle order created event', async () => {
      await messagePact
        .given('order was created')
        .expectsToReceive('an order created event')
        .withContent({
          type: 'ORDER_CREATED',
          payload: {
            orderId: uuid(),
            userId: uuid(),
            total: decimal(99.99),
            items: eachLike({
              productId: uuid(),
              quantity: integer(1),
            }),
            createdAt: datetime("yyyy-MM-dd'T'HH:mm:ss'Z'"),
          },
        })
        .verify(async (message) => {
          const handler = new OrderMessageHandler();
          await handler.handle(message);
          // Verify handling was successful
        });
    });
  });
});
```

## Best Practices

| Do | Don't |
|----|-------|
| Test consumer expectations | Test provider implementation |
| Use flexible matchers | Hard-code values |
| Setup provider states | Assume data exists |
| Run on CI/CD | Only run locally |
| Use Pact Broker | Store pacts in repo |
| Version contracts | Break without warning |

## Workflow

```
1. Consumer writes expectations → Generates pact file
2. Pact file uploaded to Broker
3. Provider verifies pact
4. Both publish verification results
5. can-i-deploy checks compatibility
6. Deploy if compatible
```

## Related Topics

- [API Testing](../integration-testing/api-testing.md)
- [External Service Testing](../integration-testing/external-service-testing.md)
- [Test Automation](../ci-cd/test-automation.md)
