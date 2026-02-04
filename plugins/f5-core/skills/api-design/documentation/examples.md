---
name: examples
description: API documentation examples and code samples
category: api-design/documentation
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# API Documentation Examples

## Overview

Well-crafted examples are crucial for API adoption. This guide covers how to
create effective code examples, tutorials, and use case documentation.

## Code Example Guidelines

```
┌─────────────────────────────────────────────────────────────────┐
│                   Code Example Principles                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Complete and Runnable                                       │
│     └── Examples should work when copied                        │
│                                                                  │
│  2. Minimal but Realistic                                       │
│     └── Show only what's needed, use real-world data            │
│                                                                  │
│  3. Well Commented                                              │
│     └── Explain non-obvious parts                               │
│                                                                  │
│  4. Multiple Languages                                          │
│     └── Cover popular languages for your audience               │
│                                                                  │
│  5. Error Handling                                              │
│     └── Show proper error handling patterns                     │
│                                                                  │
│  6. Copy-Paste Ready                                            │
│     └── Include imports, config, everything needed              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Multi-Language Examples

### cURL

```bash
# Create a new user
curl -X POST https://api.example.com/v1/users \
  -H "Authorization: Bearer sk_live_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "SecurePass123!"
  }'

# Get user by ID
curl https://api.example.com/v1/users/usr_abc123 \
  -H "Authorization: Bearer sk_live_xxxxxxxxxxxxx"

# Update user
curl -X PATCH https://api.example.com/v1/users/usr_abc123 \
  -H "Authorization: Bearer sk_live_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith"}'

# Delete user
curl -X DELETE https://api.example.com/v1/users/usr_abc123 \
  -H "Authorization: Bearer sk_live_xxxxxxxxxxxxx"

# List users with pagination and filtering
curl "https://api.example.com/v1/users?status=active&page_size=10&page_token=abc123" \
  -H "Authorization: Bearer sk_live_xxxxxxxxxxxxx"
```

### JavaScript/TypeScript

```typescript
// Using the official SDK
import { ExampleAPI } from '@example/api-client';

// Initialize client
const api = new ExampleAPI({
  apiKey: process.env.EXAMPLE_API_KEY,
  // Optional: custom base URL for testing
  baseUrl: 'https://api.example.com/v1',
});

// Create a user
async function createUser() {
  try {
    const user = await api.users.create({
      name: 'Jane Doe',
      email: 'jane@example.com',
      password: 'SecurePass123!',
      metadata: {
        source: 'website_signup',
      },
    });

    console.log('Created user:', user.id);
    return user;
  } catch (error) {
    if (error.code === 'DUPLICATE_EMAIL') {
      console.error('Email already registered');
    } else {
      console.error('Failed to create user:', error.message);
    }
    throw error;
  }
}

// Get a user
async function getUser(userId: string) {
  try {
    const user = await api.users.get(userId);
    console.log('User:', user.name, user.email);
    return user;
  } catch (error) {
    if (error.code === 'NOT_FOUND') {
      console.error('User not found');
      return null;
    }
    throw error;
  }
}

// Update a user
async function updateUser(userId: string) {
  const user = await api.users.update(userId, {
    name: 'Jane Smith',
    metadata: {
      updated_reason: 'name_change',
    },
  });

  console.log('Updated user:', user.name);
  return user;
}

// List users with pagination
async function listAllUsers() {
  const users: User[] = [];
  let pageToken: string | undefined;

  do {
    const response = await api.users.list({
      pageSize: 100,
      pageToken,
      filter: {
        status: 'active',
      },
    });

    users.push(...response.users);
    pageToken = response.nextPageToken;
  } while (pageToken);

  console.log(`Found ${users.length} users`);
  return users;
}

// Delete a user
async function deleteUser(userId: string) {
  await api.users.delete(userId);
  console.log('User deleted');
}
```

### Python

```python
"""
Example API Python Client

Install: pip install example-api
"""

import os
from example_api import ExampleAPI
from example_api.exceptions import NotFoundError, ValidationError, DuplicateError

# Initialize client
api = ExampleAPI(
    api_key=os.environ.get('EXAMPLE_API_KEY'),
    # Optional: custom base URL
    base_url='https://api.example.com/v1'
)


def create_user():
    """Create a new user."""
    try:
        user = api.users.create(
            name='Jane Doe',
            email='jane@example.com',
            password='SecurePass123!',
            metadata={'source': 'website_signup'}
        )
        print(f'Created user: {user.id}')
        return user

    except DuplicateError:
        print('Email already registered')
        raise
    except ValidationError as e:
        print(f'Validation failed: {e.details}')
        raise


def get_user(user_id: str):
    """Get a user by ID."""
    try:
        user = api.users.get(user_id)
        print(f'User: {user.name} ({user.email})')
        return user

    except NotFoundError:
        print(f'User {user_id} not found')
        return None


def update_user(user_id: str):
    """Update a user."""
    user = api.users.update(
        user_id,
        name='Jane Smith',
        metadata={'updated_reason': 'name_change'}
    )
    print(f'Updated user: {user.name}')
    return user


def list_all_users():
    """List all active users with pagination."""
    users = []
    page_token = None

    while True:
        response = api.users.list(
            page_size=100,
            page_token=page_token,
            status='active'
        )

        users.extend(response.users)
        page_token = response.next_page_token

        if not page_token:
            break

    print(f'Found {len(users)} users')
    return users


def delete_user(user_id: str):
    """Delete a user."""
    api.users.delete(user_id)
    print('User deleted')


# Using context manager for batch operations
def batch_operations():
    """Example of batch operations."""
    with api.batch() as batch:
        batch.users.create(name='User 1', email='user1@example.com', password='Pass1!')
        batch.users.create(name='User 2', email='user2@example.com', password='Pass2!')
        batch.users.create(name='User 3', email='user3@example.com', password='Pass3!')

    # Results available after context exits
    for result in batch.results:
        if result.success:
            print(f'Created: {result.data.id}')
        else:
            print(f'Failed: {result.error.message}')


if __name__ == '__main__':
    user = create_user()
    get_user(user.id)
    update_user(user.id)
    list_all_users()
    delete_user(user.id)
```

### Go

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    "github.com/example/api-go"
)

func main() {
    // Initialize client
    client := example.NewClient(os.Getenv("EXAMPLE_API_KEY"))

    // Create a user
    user, err := createUser(client)
    if err != nil {
        log.Fatal(err)
    }

    // Get user
    if err := getUser(client, user.ID); err != nil {
        log.Fatal(err)
    }

    // Update user
    if err := updateUser(client, user.ID); err != nil {
        log.Fatal(err)
    }

    // List users
    if err := listUsers(client); err != nil {
        log.Fatal(err)
    }

    // Delete user
    if err := deleteUser(client, user.ID); err != nil {
        log.Fatal(err)
    }
}

func createUser(client *example.Client) (*example.User, error) {
    ctx := context.Background()

    user, err := client.Users.Create(ctx, &example.CreateUserParams{
        Name:     "Jane Doe",
        Email:    "jane@example.com",
        Password: "SecurePass123!",
        Metadata: map[string]string{
            "source": "website_signup",
        },
    })
    if err != nil {
        var apiErr *example.Error
        if errors.As(err, &apiErr) {
            if apiErr.Code == "DUPLICATE_EMAIL" {
                return nil, fmt.Errorf("email already registered")
            }
        }
        return nil, fmt.Errorf("failed to create user: %w", err)
    }

    fmt.Printf("Created user: %s\n", user.ID)
    return user, nil
}

func getUser(client *example.Client, userID string) error {
    ctx := context.Background()

    user, err := client.Users.Get(ctx, userID)
    if err != nil {
        var apiErr *example.Error
        if errors.As(err, &apiErr) && apiErr.Code == "NOT_FOUND" {
            fmt.Println("User not found")
            return nil
        }
        return err
    }

    fmt.Printf("User: %s (%s)\n", user.Name, user.Email)
    return nil
}

func updateUser(client *example.Client, userID string) error {
    ctx := context.Background()

    user, err := client.Users.Update(ctx, userID, &example.UpdateUserParams{
        Name: example.String("Jane Smith"),
    })
    if err != nil {
        return err
    }

    fmt.Printf("Updated user: %s\n", user.Name)
    return nil
}

func listUsers(client *example.Client) error {
    ctx := context.Background()
    var users []*example.User

    params := &example.ListUsersParams{
        PageSize: 100,
        Status:   "active",
    }

    for {
        resp, err := client.Users.List(ctx, params)
        if err != nil {
            return err
        }

        users = append(users, resp.Users...)

        if resp.NextPageToken == "" {
            break
        }
        params.PageToken = resp.NextPageToken
    }

    fmt.Printf("Found %d users\n", len(users))
    return nil
}

func deleteUser(client *example.Client, userID string) error {
    ctx := context.Background()

    if err := client.Users.Delete(ctx, userID); err != nil {
        return err
    }

    fmt.Println("User deleted")
    return nil
}
```

### Ruby

```ruby
# Gemfile: gem 'example-api'

require 'example_api'

# Initialize client
ExampleAPI.configure do |config|
  config.api_key = ENV['EXAMPLE_API_KEY']
  # Optional: custom base URL
  config.base_url = 'https://api.example.com/v1'
end

client = ExampleAPI::Client.new

# Create a user
def create_user(client)
  user = client.users.create(
    name: 'Jane Doe',
    email: 'jane@example.com',
    password: 'SecurePass123!',
    metadata: { source: 'website_signup' }
  )
  puts "Created user: #{user.id}"
  user
rescue ExampleAPI::DuplicateError
  puts 'Email already registered'
  raise
rescue ExampleAPI::ValidationError => e
  puts "Validation failed: #{e.details}"
  raise
end

# Get a user
def get_user(client, user_id)
  user = client.users.get(user_id)
  puts "User: #{user.name} (#{user.email})"
  user
rescue ExampleAPI::NotFoundError
  puts "User #{user_id} not found"
  nil
end

# Update a user
def update_user(client, user_id)
  user = client.users.update(user_id, name: 'Jane Smith')
  puts "Updated user: #{user.name}"
  user
end

# List all users with pagination
def list_all_users(client)
  users = []
  page_token = nil

  loop do
    response = client.users.list(
      page_size: 100,
      page_token: page_token,
      status: 'active'
    )

    users.concat(response.users)
    page_token = response.next_page_token

    break if page_token.nil?
  end

  puts "Found #{users.length} users"
  users
end

# Delete a user
def delete_user(client, user_id)
  client.users.delete(user_id)
  puts 'User deleted'
end

# Main execution
user = create_user(client)
get_user(client, user.id)
update_user(client, user.id)
list_all_users(client)
delete_user(client, user.id)
```

## Use Case Examples

### E-commerce Integration

```typescript
/**
 * Complete e-commerce integration example
 * Shows order creation with inventory check and payment processing
 */

import { ExampleAPI } from '@example/api-client';

const api = new ExampleAPI({ apiKey: process.env.EXAMPLE_API_KEY });

async function processOrder(cartItems: CartItem[], customerId: string) {
  // Step 1: Validate inventory
  console.log('Checking inventory...');
  const inventoryCheck = await api.inventory.check({
    items: cartItems.map((item) => ({
      productId: item.productId,
      quantity: item.quantity,
    })),
  });

  if (!inventoryCheck.available) {
    const unavailable = inventoryCheck.unavailableItems;
    throw new Error(`Items out of stock: ${unavailable.map((i) => i.productId).join(', ')}`);
  }

  // Step 2: Create order
  console.log('Creating order...');
  const order = await api.orders.create({
    customerId,
    items: cartItems.map((item) => ({
      productId: item.productId,
      quantity: item.quantity,
      unitPrice: item.price,
    })),
    shippingAddress: await api.customers.getDefaultAddress(customerId),
    idempotencyKey: `order_${customerId}_${Date.now()}`,
  });

  console.log(`Order created: ${order.id}`);

  // Step 3: Process payment
  console.log('Processing payment...');
  try {
    const payment = await api.payments.create({
      orderId: order.id,
      amount: order.total,
      currency: 'USD',
      paymentMethodId: await api.customers.getDefaultPaymentMethod(customerId),
    });

    if (payment.status === 'succeeded') {
      // Step 4: Confirm order
      await api.orders.confirm(order.id);
      console.log('Order confirmed!');

      // Step 5: Send confirmation email
      await api.notifications.send({
        type: 'order_confirmation',
        customerId,
        data: { orderId: order.id },
      });

      return order;
    } else {
      throw new Error(`Payment failed: ${payment.failureReason}`);
    }
  } catch (error) {
    // Cancel order if payment fails
    await api.orders.cancel(order.id, {
      reason: 'payment_failed',
    });
    throw error;
  }
}

// Usage
processOrder(
  [
    { productId: 'prod_001', quantity: 2, price: 2999 },
    { productId: 'prod_002', quantity: 1, price: 4999 },
  ],
  'cus_abc123'
);
```

### Webhook Handler

```typescript
/**
 * Webhook handling example with signature verification
 */

import express from 'express';
import { ExampleAPI, verifyWebhookSignature } from '@example/api-client';

const app = express();
const api = new ExampleAPI({ apiKey: process.env.EXAMPLE_API_KEY });

// Raw body needed for signature verification
app.post(
  '/webhooks',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const signature = req.headers['x-webhook-signature'] as string;
    const payload = req.body;

    // Verify signature
    if (
      !verifyWebhookSignature(payload, signature, process.env.WEBHOOK_SECRET!)
    ) {
      console.error('Invalid webhook signature');
      return res.status(401).send('Invalid signature');
    }

    const event = JSON.parse(payload.toString());

    try {
      switch (event.type) {
        case 'order.created':
          await handleOrderCreated(event.data);
          break;

        case 'order.paid':
          await handleOrderPaid(event.data);
          break;

        case 'order.shipped':
          await handleOrderShipped(event.data);
          break;

        case 'customer.created':
          await handleCustomerCreated(event.data);
          break;

        default:
          console.log(`Unhandled event type: ${event.type}`);
      }

      res.status(200).send('OK');
    } catch (error) {
      console.error('Webhook processing error:', error);
      // Return 200 to prevent retries for processing errors
      // Log error for investigation
      res.status(200).send('Processed with errors');
    }
  }
);

async function handleOrderCreated(data: any) {
  console.log(`New order: ${data.order.id}`);

  // Reserve inventory
  await api.inventory.reserve({
    orderId: data.order.id,
    items: data.order.items,
  });
}

async function handleOrderPaid(data: any) {
  console.log(`Order paid: ${data.order.id}`);

  // Trigger fulfillment
  await api.fulfillment.create({
    orderId: data.order.id,
    priority: data.order.shippingMethod === 'express' ? 'high' : 'normal',
  });
}

async function handleOrderShipped(data: any) {
  console.log(`Order shipped: ${data.order.id}`);

  // Send shipping notification
  await api.notifications.send({
    type: 'order_shipped',
    customerId: data.order.customerId,
    data: {
      orderId: data.order.id,
      trackingNumber: data.shipment.trackingNumber,
      carrier: data.shipment.carrier,
    },
  });
}

async function handleCustomerCreated(data: any) {
  console.log(`New customer: ${data.customer.id}`);

  // Send welcome email
  await api.notifications.send({
    type: 'welcome',
    customerId: data.customer.id,
  });

  // Add to CRM
  await syncToCRM(data.customer);
}

app.listen(3000);
```

### Batch Processing

```python
"""
Batch processing example - importing users from CSV
"""

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from example_api import ExampleAPI
from example_api.exceptions import DuplicateError, ValidationError

api = ExampleAPI(api_key=os.environ['EXAMPLE_API_KEY'])


def import_users_from_csv(filename: str, batch_size: int = 100):
    """
    Import users from a CSV file with batch processing.

    CSV format: name,email,role
    """
    results = {
        'success': 0,
        'duplicates': 0,
        'errors': []
    }

    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    print(f'Importing {len(rows)} users...')

    # Process in batches
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]

        # Use thread pool for parallel requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(create_user, row): row
                for row in batch
            }

            for future in as_completed(futures):
                row = futures[future]
                try:
                    result = future.result()
                    results['success'] += 1
                except DuplicateError:
                    results['duplicates'] += 1
                except ValidationError as e:
                    results['errors'].append({
                        'email': row['email'],
                        'error': str(e)
                    })

        # Progress update
        processed = min(i + batch_size, len(rows))
        print(f'Processed {processed}/{len(rows)}')

    print(f'''
Import complete:
  Success: {results['success']}
  Duplicates: {results['duplicates']}
  Errors: {len(results['errors'])}
    ''')

    return results


def create_user(row: dict):
    """Create a single user from CSV row."""
    return api.users.create(
        name=row['name'],
        email=row['email'],
        password=generate_temp_password(),
        role=row.get('role', 'user'),
        metadata={'source': 'csv_import'}
    )


def generate_temp_password() -> str:
    """Generate a temporary password."""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + '!@#$%'
    return ''.join(secrets.choice(alphabet) for _ in range(16))


if __name__ == '__main__':
    import_users_from_csv('users.csv')
```

## Interactive Examples

### API Explorer Code

```html
<!DOCTYPE html>
<html>
  <head>
    <title>API Explorer</title>
    <style>
      .code-block {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 16px;
        border-radius: 4px;
        font-family: monospace;
      }
      .response {
        margin-top: 16px;
      }
      .try-button {
        background: #0066cc;
        color: white;
        border: none;
        padding: 8px 16px;
        cursor: pointer;
      }
    </style>
  </head>
  <body>
    <h2>Try It Out: Get User</h2>

    <div class="code-block" id="request">
      <pre>GET /v1/users/{userId}</pre>
    </div>

    <form id="tryForm">
      <label>
        User ID:
        <input type="text" id="userId" value="usr_abc123" />
      </label>
      <button type="submit" class="try-button">Try It</button>
    </form>

    <div class="response" id="response"></div>

    <script>
      document.getElementById('tryForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const userId = document.getElementById('userId').value;

        try {
          const response = await fetch(`/api/v1/users/${userId}`, {
            headers: {
              'Authorization': `Bearer ${getApiKey()}`,
            },
          });

          const data = await response.json();
          document.getElementById('response').innerHTML = `
            <div class="code-block">
              <pre>Status: ${response.status}

${JSON.stringify(data, null, 2)}</pre>
            </div>
          `;
        } catch (error) {
          document.getElementById('response').innerHTML = `
            <div class="code-block" style="color: red;">
              Error: ${error.message}
            </div>
          `;
        }
      });
    </script>
  </body>
</html>
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                 Example Best Practices                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Test Every Example                                          │
│     └── Run examples in CI to catch breaks                      │
│                                                                  │
│  2. Use Realistic Data                                          │
│     └── "Jane Doe" not "test123"                                │
│                                                                  │
│  3. Show Error Handling                                         │
│     └── Don't just show happy path                              │
│                                                                  │
│  4. Include All Dependencies                                    │
│     └── Import statements, package versions                     │
│                                                                  │
│  5. Explain Non-Obvious Code                                    │
│     └── Comments for complex logic                              │
│                                                                  │
│  6. Update When API Changes                                     │
│     └── Part of release process                                 │
│                                                                  │
│  7. Link to SDK Documentation                                   │
│     └── Cross-reference related resources                       │
│                                                                  │
│  8. Provide Runnable Samples                                    │
│     └── GitHub repos, CodeSandbox, Replit                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
