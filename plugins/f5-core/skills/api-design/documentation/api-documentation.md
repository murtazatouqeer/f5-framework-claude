---
name: api-documentation
description: API documentation best practices and structure
category: api-design/documentation
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# API Documentation

## Overview

Good API documentation is essential for developer experience. It should be
accurate, comprehensive, easy to navigate, and include working examples.

## Documentation Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                API Documentation Structure                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Getting Started                                             │
│     ├── Introduction / Overview                                 │
│     ├── Authentication                                          │
│     ├── Quick Start Guide                                       │
│     └── SDKs and Libraries                                      │
│                                                                  │
│  2. API Reference                                               │
│     ├── Endpoints by Resource                                   │
│     ├── Request/Response Formats                                │
│     ├── Status Codes                                            │
│     └── Error Handling                                          │
│                                                                  │
│  3. Guides                                                      │
│     ├── Common Use Cases                                        │
│     ├── Best Practices                                          │
│     ├── Webhooks                                                │
│     └── Rate Limiting                                           │
│                                                                  │
│  4. Resources                                                   │
│     ├── Changelog                                               │
│     ├── Migration Guides                                        │
│     ├── API Status                                              │
│     └── Support                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Getting Started Section

### Introduction

```markdown
# Introduction

The Example API provides programmatic access to Example's platform.
Use it to manage users, process orders, and integrate with your applications.

## Base URL

All API requests should be made to:

```
https://api.example.com/v1
```

## Authentication

The API uses Bearer token authentication. Include your API key in the
Authorization header:

```
Authorization: Bearer your_api_key
```

## Request Format

- All requests must use HTTPS
- Request bodies should be JSON with `Content-Type: application/json`
- All timestamps are in ISO 8601 format (UTC)

## Response Format

All responses are JSON. Successful responses include a `data` field:

```json
{
  "data": {
    "id": "usr_123",
    "name": "John Doe"
  }
}
```

Error responses include an `error` object:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "User not found"
  }
}
```
```

### Quick Start

```markdown
# Quick Start

Get up and running with the Example API in 5 minutes.

## 1. Get Your API Key

1. Log in to the [Developer Portal](https://developers.example.com)
2. Navigate to **Settings > API Keys**
3. Click **Create New Key**
4. Copy your key (it won't be shown again)

## 2. Make Your First Request

```bash
curl https://api.example.com/v1/users/me \
  -H "Authorization: Bearer your_api_key"
```

Response:
```json
{
  "data": {
    "id": "usr_abc123",
    "name": "Your Name",
    "email": "you@example.com"
  }
}
```

## 3. Create a Resource

```bash
curl -X POST https://api.example.com/v1/orders \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cus_xyz789",
    "items": [
      {"product_id": "prod_001", "quantity": 2}
    ]
  }'
```

## 4. Install an SDK (Optional)

```bash
# Node.js
npm install @example/api-client

# Python
pip install example-api

# Go
go get github.com/example/api-go
```

## Next Steps

- [Authentication Guide](/docs/authentication) - Learn about auth options
- [API Reference](/docs/reference) - Explore all endpoints
- [Webhooks](/docs/webhooks) - Set up real-time notifications
```

## API Reference Format

### Endpoint Documentation

```markdown
# Create User

Creates a new user account.

## Endpoint

```
POST /users
```

## Authentication

Requires `Bearer` token with `write:users` scope.

## Request

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer token |
| Content-Type | Yes | Must be `application/json` |
| Idempotency-Key | No | Unique key for idempotent requests |

### Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | User's full name (2-100 chars) |
| email | string | Yes | Valid email address |
| password | string | Yes | Min 8 chars with complexity |
| role | string | No | `user`, `admin`, `moderator`. Default: `user` |
| metadata | object | No | Custom key-value pairs |

### Example Request

```bash
curl -X POST https://api.example.com/v1/users \
  -H "Authorization: Bearer sk_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "SecurePass123!",
    "role": "user",
    "metadata": {
      "source": "marketing_campaign"
    }
  }'
```

## Response

### Success Response (201 Created)

```json
{
  "data": {
    "id": "usr_abc123",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "role": "user",
    "status": "active",
    "metadata": {
      "source": "marketing_campaign"
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Error Responses

#### 400 Bad Request

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Must be a valid email address"
      }
    ]
  }
}
```

#### 409 Conflict

```json
{
  "error": {
    "code": "DUPLICATE_EMAIL",
    "message": "A user with this email already exists"
  }
}
```

## Rate Limits

This endpoint is limited to 100 requests per minute per API key.

## Related Endpoints

- [Get User](/docs/reference/users/get) - Retrieve a user
- [Update User](/docs/reference/users/update) - Modify a user
- [List Users](/docs/reference/users/list) - List all users
```

## Error Documentation

```markdown
# Errors

The API uses conventional HTTP response codes to indicate success or failure.

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful deletion) |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid auth |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable - Valid JSON but invalid data |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Error - Something went wrong |
| 503 | Service Unavailable - Temporary outage |

## Error Response Format

All errors return a JSON object with an `error` field:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": [...],
    "request_id": "req_abc123"
  }
}
```

## Error Codes

### Authentication Errors

| Code | Description | Resolution |
|------|-------------|------------|
| INVALID_API_KEY | API key is invalid | Check your API key |
| EXPIRED_TOKEN | Token has expired | Refresh your token |
| INSUFFICIENT_SCOPE | Token lacks required scope | Request additional scopes |

### Validation Errors

| Code | Description | Resolution |
|------|-------------|------------|
| MISSING_FIELD | Required field is missing | Include the field |
| INVALID_FORMAT | Field format is invalid | Check field format |
| VALUE_TOO_LONG | Value exceeds max length | Shorten the value |

### Resource Errors

| Code | Description | Resolution |
|------|-------------|------------|
| NOT_FOUND | Resource doesn't exist | Check the ID |
| ALREADY_EXISTS | Resource already exists | Use a different identifier |
| RESOURCE_LOCKED | Resource is locked | Try again later |

## Handling Errors

```javascript
async function makeRequest() {
  try {
    const response = await api.users.create({
      name: 'John',
      email: 'john@example.com'
    });
    return response.data;
  } catch (error) {
    if (error.code === 'DUPLICATE_EMAIL') {
      // Handle duplicate email
      console.log('Email already registered');
    } else if (error.status === 429) {
      // Handle rate limiting
      const retryAfter = error.headers['retry-after'];
      await sleep(retryAfter * 1000);
      return makeRequest();
    } else {
      // Handle other errors
      console.error('API Error:', error.message);
      throw error;
    }
  }
}
```
```

## Authentication Documentation

```markdown
# Authentication

The API supports multiple authentication methods.

## API Keys

API keys are the simplest way to authenticate. Include your key in the
Authorization header:

```
Authorization: Bearer sk_live_xxxxxxxxxxxxx
```

### Key Types

| Type | Prefix | Environment | Use Case |
|------|--------|-------------|----------|
| Live | `sk_live_` | Production | Real transactions |
| Test | `sk_test_` | Sandbox | Development/testing |

### Creating Keys

1. Go to **Dashboard > API Keys**
2. Click **Create Key**
3. Select permissions
4. Copy the key immediately (shown only once)

### Key Security

- Never expose keys in client-side code
- Rotate keys periodically
- Use environment variables
- Restrict key permissions to minimum needed

## OAuth 2.0

For user-authorized actions, use OAuth 2.0.

### Authorization Code Flow

```
1. Redirect user to authorization URL
   GET https://auth.example.com/oauth/authorize
     ?client_id=your_client_id
     &redirect_uri=https://yourapp.com/callback
     &response_type=code
     &scope=read:users write:orders
     &state=random_state

2. User authorizes your app

3. User redirected to your callback with code
   https://yourapp.com/callback?code=auth_code&state=random_state

4. Exchange code for tokens
   POST https://auth.example.com/oauth/token
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code
   &code=auth_code
   &client_id=your_client_id
   &client_secret=your_client_secret
   &redirect_uri=https://yourapp.com/callback

5. Response
   {
     "access_token": "at_xxxxx",
     "token_type": "Bearer",
     "expires_in": 3600,
     "refresh_token": "rt_xxxxx",
     "scope": "read:users write:orders"
   }
```

### Scopes

| Scope | Description |
|-------|-------------|
| read:users | Read user profiles |
| write:users | Create and update users |
| read:orders | View orders |
| write:orders | Create and modify orders |
| admin | Full administrative access |

### Refreshing Tokens

```
POST https://auth.example.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token=rt_xxxxx
&client_id=your_client_id
&client_secret=your_client_secret
```

## Webhooks

Webhooks use signature verification for security.

### Verifying Signatures

```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(`sha256=${expected}`)
  );
}

app.post('/webhooks', (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  const payload = JSON.stringify(req.body);

  if (!verifyWebhook(payload, signature, WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }

  // Process webhook
  handleWebhook(req.body);
  res.status(200).send('OK');
});
```
```

## Rate Limiting Documentation

```markdown
# Rate Limits

The API implements rate limiting to ensure fair usage and stability.

## Default Limits

| Plan | Requests/min | Requests/day |
|------|--------------|--------------|
| Free | 60 | 1,000 |
| Starter | 100 | 10,000 |
| Pro | 1,000 | 100,000 |
| Enterprise | Custom | Custom |

## Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
```

| Header | Description |
|--------|-------------|
| X-RateLimit-Limit | Max requests per window |
| X-RateLimit-Remaining | Requests remaining |
| X-RateLimit-Reset | Unix timestamp when limit resets |

## Handling Rate Limits

When rate limited, you'll receive a `429 Too Many Requests` response:

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Please retry after 60 seconds.",
    "retry_after": 60
  }
}
```

### Best Practices

```javascript
async function makeRequestWithRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429) {
        const retryAfter = error.headers['retry-after'] || 60;
        console.log(`Rate limited. Retrying in ${retryAfter}s...`);
        await sleep(retryAfter * 1000);
      } else {
        throw error;
      }
    }
  }
  throw new Error('Max retries exceeded');
}

// Implement exponential backoff
async function exponentialBackoff(fn, maxRetries = 5) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429 || error.status >= 500) {
        const delay = Math.min(1000 * Math.pow(2, i), 30000);
        await sleep(delay);
      } else {
        throw error;
      }
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Burst Limits

Some endpoints have additional burst limits:

| Endpoint | Burst Limit |
|----------|-------------|
| POST /users | 10/sec |
| POST /orders | 5/sec |
| POST /emails | 2/sec |
```

## Changelog Documentation

```markdown
# Changelog

All notable changes to the API are documented here.

## 2024-01-15 (v2.3.0)

### Added
- New `metadata` field on User object
- Bulk create endpoint: `POST /users/bulk`
- Webhook event: `user.verified`

### Changed
- Increased default page size from 20 to 25
- Improved error messages for validation errors

### Deprecated
- `GET /users/search` - Use `GET /users?q=` instead
- `status` query parameter on orders - Use `statuses[]` for multiple

### Fixed
- Fixed pagination cursor encoding for special characters
- Fixed rate limit headers not being sent on cached responses

## 2024-01-01 (v2.2.0)

### Added
- OAuth 2.0 support with PKCE
- New scopes: `read:analytics`, `write:webhooks`

### Security
- All API keys now require TLS 1.2 minimum
- Added IP allowlist feature for API keys

---

## Versioning Policy

We use semantic versioning:
- **Major**: Breaking changes (rare, with migration period)
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

## Deprecation Policy

1. Deprecated features announced 6 months in advance
2. Deprecation warnings added to responses
3. Documentation updated with alternatives
4. Feature removed after deprecation period
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Documentation Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Keep It Current                                             │
│     └── Update docs with every API change                       │
│                                                                  │
│  2. Provide Working Examples                                    │
│     └── Test all code samples, multiple languages               │
│                                                                  │
│  3. Document All Errors                                         │
│     └── Include every possible error with resolution            │
│                                                                  │
│  4. Be Consistent                                               │
│     └── Use same terminology and format throughout              │
│                                                                  │
│  5. Include Use Cases                                           │
│     └── Show real-world scenarios, not just reference           │
│                                                                  │
│  6. Make It Searchable                                          │
│     └── Good navigation, search, and cross-references           │
│                                                                  │
│  7. Version Your Docs                                           │
│     └── Match docs to API versions                              │
│                                                                  │
│  8. Get Feedback                                                │
│     └── Allow comments, track what developers ask               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
