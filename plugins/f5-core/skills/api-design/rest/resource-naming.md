---
name: resource-naming
description: REST API resource naming conventions and URI design
category: api-design/rest
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Resource Naming

## Overview

Consistent resource naming is crucial for intuitive, maintainable APIs.
Good naming conventions make APIs self-documenting and easier to use.

## Naming Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                   Resource Naming Rules                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use Nouns, Not Verbs                                        │
│     ├── Resources represent things, not actions                 │
│     ├── HTTP methods express the action                         │
│     └── ✅ /users  ❌ /getUsers                                 │
│                                                                  │
│  2. Use Plural Nouns                                            │
│     ├── Collections are plural                                  │
│     ├── Consistent with or without ID                           │
│     └── ✅ /users/123  ❌ /user/123                             │
│                                                                  │
│  3. Use Lowercase Letters                                       │
│     ├── URIs are case-sensitive                                 │
│     ├── Lowercase is more consistent                            │
│     └── ✅ /users  ❌ /Users                                    │
│                                                                  │
│  4. Use Hyphens for Readability                                 │
│     ├── Hyphens are URI-safe                                    │
│     ├── More readable than underscores                          │
│     └── ✅ /user-profiles  ❌ /user_profiles                    │
│                                                                  │
│  5. Avoid File Extensions                                       │
│     ├── Use Accept header for content type                      │
│     └── ✅ /reports  ❌ /reports.json                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Resource Hierarchy

### Collection vs Item

```
# Collection (plural noun)
GET /users                  # All users
POST /users                 # Create user

# Item (collection + identifier)
GET /users/123              # Specific user
PUT /users/123              # Replace user
PATCH /users/123            # Update user
DELETE /users/123           # Delete user
```

### Nested Resources

```
# Strong ownership - use nesting
GET /users/123/orders       # User's orders (user owns orders)
POST /users/123/orders      # Create order for user

# Weak association - use query parameters
GET /orders?user_id=123     # Filter orders by user
GET /products?category=electronics

# Too deep - flatten it
❌ /users/123/orders/456/items/789/reviews
✅ /order-items/789/reviews
✅ /reviews?order_item_id=789
```

### Relationship Guidelines

```
┌─────────────────────────────────────────────────────────────────┐
│                 When to Nest Resources                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Nest When:                                                      │
│  ├── Child cannot exist without parent                          │
│  ├── Parent owns the child (composition)                        │
│  ├── Child identity is scoped to parent                         │
│  └── Examples:                                                   │
│      • /users/{id}/preferences                                  │
│      • /orders/{id}/line-items                                  │
│      • /organizations/{id}/members                              │
│                                                                  │
│  Don't Nest When:                                                │
│  ├── Child can exist independently                              │
│  ├── Child has global identity                                  │
│  ├── Nesting would exceed 2 levels                              │
│  └── Examples:                                                   │
│      • /products (not /categories/{id}/products)                │
│      • /reviews (not /users/{id}/orders/{id}/reviews)           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Resource Naming Patterns

### Standard CRUD Resources

```
# Users
GET    /users                # List users
POST   /users                # Create user
GET    /users/{id}           # Get user
PUT    /users/{id}           # Replace user
PATCH  /users/{id}           # Update user
DELETE /users/{id}           # Delete user

# Sub-resources
GET    /users/{id}/orders    # List user's orders
POST   /users/{id}/orders    # Create order for user
GET    /users/{id}/profile   # Get user's profile (singleton)
PUT    /users/{id}/profile   # Update user's profile
```

### Singleton Resources

```
# Resource that exists as single instance per parent
GET    /users/{id}/profile   # Get profile (no collection)
PUT    /users/{id}/profile   # Update profile
DELETE /users/{id}/profile   # Delete profile

# Current user (special case)
GET    /me                   # Current authenticated user
GET    /me/orders            # Current user's orders
PUT    /me/settings          # Update current user's settings
```

### Actions on Resources

```
# When HTTP verbs don't fit, use sub-resource for action
POST /orders/{id}/cancel           # Cancel order
POST /orders/{id}/ship             # Ship order
POST /users/{id}/verify-email      # Verify email
POST /accounts/{id}/transfer       # Transfer funds
POST /documents/{id}/archive       # Archive document

# Alternative: Use query parameter
POST /orders/{id}?action=cancel

# Alternative: Controller resource
POST /order-cancellations          # Create cancellation
{
  "order_id": "ord_123",
  "reason": "Customer request"
}
```

### Search and Filter Resources

```
# Simple search - query parameters
GET /users?status=active&role=admin

# Complex search - dedicated endpoint
POST /users/search
{
  "filters": {
    "status": ["active", "pending"],
    "created_after": "2024-01-01"
  },
  "sort": "-created_at"
}

# Saved searches
POST /saved-searches
{
  "name": "Active Admins",
  "resource": "users",
  "filters": {"status": "active", "role": "admin"}
}

GET /saved-searches/{id}/results
```

## Identifier Design

### Types of Identifiers

```typescript
// Sequential integer (simple, predictable)
GET /users/123

// UUID (globally unique, no information leakage)
GET /users/550e8400-e29b-41d4-a716-446655440000

// Prefixed ID (type-safe, debuggable)
GET /users/usr_2x4y6z8w
GET /orders/ord_1a2b3c4d
GET /products/prod_9k8j7h6g

// Slug (human-readable, SEO-friendly)
GET /products/blue-widget-deluxe
GET /articles/how-to-build-apis

// Composite (when single ID not unique)
GET /organizations/acme/members/john-doe
```

### Prefixed IDs Pattern

```typescript
// ID generation with type prefix
const prefixes = {
  user: 'usr',
  order: 'ord',
  product: 'prod',
  payment: 'pay',
  subscription: 'sub'
};

function generateId(type: keyof typeof prefixes): string {
  const prefix = prefixes[type];
  const random = crypto.randomBytes(12).toString('base64url');
  return `${prefix}_${random}`;
}

// Examples
generateId('user');    // usr_x7k9m2p4q1w3
generateId('order');   // ord_a1b2c3d4e5f6
generateId('product'); // prod_9z8y7x6w5v4u

// Benefits:
// - Easy to identify resource type in logs
// - Prevents accidentally using wrong ID type
// - URL-safe characters
```

## URL Structure Examples

### E-commerce API

```
# Products
GET    /products
GET    /products/{id}
GET    /products/{id}/variants
GET    /products/{id}/reviews

# Categories
GET    /categories
GET    /categories/{id}
GET    /categories/{id}/products

# Cart (singleton per user)
GET    /cart
POST   /cart/items
PUT    /cart/items/{id}
DELETE /cart/items/{id}
DELETE /cart                        # Clear cart

# Orders
POST   /orders                      # Create from cart
GET    /orders
GET    /orders/{id}
GET    /orders/{id}/items
POST   /orders/{id}/cancel

# Users
GET    /me
GET    /me/orders
GET    /me/addresses
POST   /me/addresses
```

### Social Platform API

```
# Users
GET    /users/{id}
GET    /users/{id}/posts
GET    /users/{id}/followers
GET    /users/{id}/following

# Posts
GET    /posts
GET    /posts/{id}
GET    /posts/{id}/comments
POST   /posts/{id}/comments
GET    /posts/{id}/likes
POST   /posts/{id}/like
DELETE /posts/{id}/like

# Feed
GET    /feed                        # Authenticated user's feed
GET    /feed/trending               # Trending posts

# Relationships
POST   /users/{id}/follow
DELETE /users/{id}/follow
```

### Multi-tenant SaaS API

```
# Organizations
GET    /organizations
POST   /organizations
GET    /organizations/{org_id}

# Organization-scoped resources
GET    /organizations/{org_id}/members
GET    /organizations/{org_id}/projects
GET    /organizations/{org_id}/projects/{project_id}
GET    /organizations/{org_id}/projects/{project_id}/tasks

# Alternative: Use subdomain
# https://acme.api.example.com/projects
# https://acme.api.example.com/projects/{id}/tasks

# Alternative: Header-based tenant
# GET /projects
# X-Tenant-ID: org_123
```

## Naming Conventions

### Good Names

```
✅ /users                    # Clear, plural, noun
✅ /user-profiles            # Hyphenated compound
✅ /line-items               # Hyphenated compound
✅ /api-keys                 # Hyphenated compound
✅ /oauth-tokens             # Hyphenated compound
✅ /health-check             # Hyphenated action resource
```

### Names to Avoid

```
❌ /getUsers                 # Verb in URL
❌ /user_profiles            # Underscore
❌ /userProfiles             # CamelCase
❌ /UserProfiles             # PascalCase
❌ /USERS                    # All caps
❌ /user/123                 # Singular
❌ /users.json               # File extension
❌ /api/v1/users/list        # Redundant action
```

## Query Parameters

### Standard Parameters

```
# Pagination
?page=1&limit=20
?offset=0&limit=20
?cursor=eyJpZCI6MTIzfQ

# Sorting
?sort=created_at              # Ascending
?sort=-created_at             # Descending
?sort=status,-created_at      # Multiple fields

# Filtering
?status=active
?status=active,pending        # Multiple values
?created_after=2024-01-01
?price_min=10&price_max=100

# Field selection
?fields=id,name,email
?include=orders,profile

# Search
?q=john                       # Simple search
?search=john+doe              # Full-text search
```

### Parameter Naming

```
# Use snake_case for parameters
✅ ?user_id=123
✅ ?created_at=2024-01-01
✅ ?sort_by=name

❌ ?userId=123                # camelCase
❌ ?CreatedAt=2024-01-01      # PascalCase

# Use consistent prefixes
?filter[status]=active        # JSON:API style
?filter_status=active         # Flat style
```

## Best Practices Summary

```
┌─────────────────────────────────────────────────────────────────┐
│               Resource Naming Checklist                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✓ Use plural nouns for collections                             │
│  ✓ Use lowercase letters only                                   │
│  ✓ Use hyphens for multi-word resources                         │
│  ✓ Keep nesting to 2 levels maximum                             │
│  ✓ Use query parameters for filtering                           │
│  ✓ Use consistent ID formats                                    │
│  ✓ Document naming conventions                                  │
│  ✓ Be consistent across the entire API                          │
│                                                                  │
│  ✗ Don't use verbs in URLs                                      │
│  ✗ Don't use file extensions                                    │
│  ✗ Don't expose implementation details                          │
│  ✗ Don't use abbreviations without documentation                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
