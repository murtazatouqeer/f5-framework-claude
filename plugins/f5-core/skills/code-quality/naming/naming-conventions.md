---
name: naming-conventions
description: Naming conventions and standards for code
category: code-quality/naming
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Naming Conventions

## Overview

Consistent naming conventions make code readable and maintainable. This guide covers common conventions across languages and project types.

## Case Styles

| Style | Example | Usage |
|-------|---------|-------|
| camelCase | `userName`, `getUserById` | Variables, functions (JS/TS) |
| PascalCase | `UserService`, `OrderStatus` | Classes, interfaces, types |
| snake_case | `user_name`, `get_user_by_id` | Variables, functions (Python) |
| SCREAMING_SNAKE_CASE | `MAX_RETRIES`, `API_URL` | Constants |
| kebab-case | `user-profile`, `api-routes` | File names, URLs, CSS |

## JavaScript/TypeScript Conventions

### Variables and Functions

```typescript
// ✅ camelCase for variables and functions
const userName = 'John';
const isActive = true;
const itemCount = 42;

function getUserById(id: string): User {}
function calculateTotalPrice(items: Item[]): number {}
async function fetchUserOrders(userId: string): Promise<Order[]> {}

// ❌ Avoid
const user_name = 'John';  // snake_case
const UserName = 'John';   // PascalCase
const USERNAME = 'John';   // SCREAMING (not a constant)
```

### Classes and Types

```typescript
// ✅ PascalCase for classes, interfaces, types, enums
class UserService {}
class OrderRepository {}

interface UserProfile {}
interface CreateOrderDTO {}

type UserId = string;
type OrderStatus = 'pending' | 'completed';

enum PaymentMethod {
  CreditCard = 'credit_card',
  BankTransfer = 'bank_transfer',
  PayPal = 'paypal',
}

// ❌ Avoid
class userService {}        // camelCase
interface user_profile {}   // snake_case
type userId = string;       // camelCase
```

### Constants

```typescript
// ✅ SCREAMING_SNAKE_CASE for true constants
const MAX_RETRY_ATTEMPTS = 3;
const API_BASE_URL = 'https://api.example.com';
const DEFAULT_TIMEOUT_MS = 5000;

// Object constants - PascalCase with readonly
const HttpStatus = {
  OK: 200,
  NOT_FOUND: 404,
  INTERNAL_ERROR: 500,
} as const;

// ❌ Avoid treating mutable values as constants
const MAX_ITEMS = getMaxItems(); // Not a compile-time constant
```

### File Names

```typescript
// ✅ kebab-case for file names
// user-service.ts
// order-repository.ts
// create-user.dto.ts
// auth.middleware.ts
// user.controller.ts

// ✅ PascalCase for React components
// UserProfile.tsx
// OrderList.tsx
// CreateOrderForm.tsx

// ❌ Avoid
// UserService.ts (unless class-per-file convention)
// user_service.ts (snake_case)
// userService.ts (camelCase)
```

### File Naming Patterns

```
// Service files
user.service.ts
order.service.ts

// Repository/Data files
user.repository.ts
order.entity.ts

// Controller files
user.controller.ts
auth.controller.ts

// Type/Interface files
user.types.ts
order.dto.ts

// Test files
user.service.test.ts
user.service.spec.ts

// React components
UserProfile.tsx
UserProfile.test.tsx
UserProfile.styles.ts
```

## React Conventions

```tsx
// ✅ PascalCase for components
function UserProfile({ user }: UserProfileProps) {}
function OrderList({ orders }: OrderListProps) {}

// ✅ camelCase for hooks
function useAuth() {}
function useUserProfile(userId: string) {}
function useFetchOrders() {}

// ✅ camelCase for event handlers with 'handle' prefix
function handleClick() {}
function handleSubmit() {}
function handleInputChange() {}

// ✅ Props interfaces with 'Props' suffix
interface UserProfileProps {
  user: User;
  onEdit?: () => void;
}

// ✅ Boolean props with 'is', 'has', 'should' prefix
interface ButtonProps {
  isDisabled?: boolean;
  isLoading?: boolean;
  hasIcon?: boolean;
  shouldAnimate?: boolean;
}
```

## API/Backend Conventions

### HTTP Endpoints

```
# ✅ kebab-case for URLs, plural nouns for resources
GET    /api/users
GET    /api/users/:id
POST   /api/users
PUT    /api/users/:id
DELETE /api/users/:id

GET    /api/user-profiles
GET    /api/order-items

# ❌ Avoid
GET    /api/getUser          # verbs in URL
GET    /api/user_profiles    # snake_case
GET    /api/UserProfiles     # PascalCase
```

### Database

```sql
-- ✅ snake_case for tables and columns
CREATE TABLE users (
  id UUID PRIMARY KEY,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  email VARCHAR(255),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE order_items (
  id UUID PRIMARY KEY,
  order_id UUID REFERENCES orders(id),
  product_id UUID REFERENCES products(id),
  quantity INTEGER,
  unit_price DECIMAL(10, 2)
);

-- ❌ Avoid
CREATE TABLE Users (           -- PascalCase
  FirstName VARCHAR(100),      -- PascalCase
  lastName VARCHAR(100),       -- camelCase
);
```

## Environment Variables

```bash
# ✅ SCREAMING_SNAKE_CASE
DATABASE_URL=postgres://localhost:5432/mydb
API_KEY=secret123
NODE_ENV=production
MAX_UPLOAD_SIZE_MB=10

# With prefixes for grouping
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb

AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1
```

## Prefixes and Suffixes

### Common Prefixes

| Prefix | Usage | Example |
|--------|-------|---------|
| `is`, `has`, `should` | Booleans | `isActive`, `hasPermission` |
| `get`, `set` | Accessors | `getName`, `setStatus` |
| `fetch`, `load` | Async data | `fetchUsers`, `loadConfig` |
| `create`, `update`, `delete` | CRUD | `createUser`, `updateOrder` |
| `handle` | Event handlers | `handleClick`, `handleSubmit` |
| `on` | Callbacks/Props | `onClick`, `onSuccess` |
| `use` | React hooks | `useAuth`, `useState` |
| `with` | HOCs | `withAuth`, `withLoading` |

### Common Suffixes

| Suffix | Usage | Example |
|--------|-------|---------|
| `Service` | Business logic | `UserService` |
| `Repository` | Data access | `OrderRepository` |
| `Controller` | HTTP handlers | `AuthController` |
| `DTO` | Data transfer | `CreateUserDTO` |
| `Entity` | Database model | `UserEntity` |
| `Props` | Component props | `ButtonProps` |
| `State` | State types | `AuthState` |
| `Context` | React context | `ThemeContext` |
| `Error` | Custom errors | `ValidationError` |
| `Config` | Configuration | `DatabaseConfig` |

## Language-Specific Guidelines

### TypeScript

```typescript
// Interface vs Type naming
interface User {}        // Prefer for objects with methods
type UserId = string;    // Prefer for aliases and unions

// No I prefix for interfaces (modern convention)
interface User {}        // ✅
interface IUser {}       // ❌ Avoid Hungarian notation

// Generic type parameters
function identity<T>(value: T): T {}           // Single generic
function map<TInput, TOutput>(): void {}       // Multiple generics
type Container<TItem> = { item: TItem };       // Descriptive
```

### CSS/SCSS

```scss
// ✅ kebab-case for classes
.user-profile {}
.order-list {}
.btn-primary {}

// ✅ BEM naming
.card {}
.card__header {}
.card__body {}
.card--highlighted {}

// ✅ CSS custom properties
:root {
  --color-primary: #007bff;
  --spacing-md: 16px;
  --font-size-lg: 18px;
}
```

## Project Configuration

### ESLint Naming Convention Rules

```javascript
// eslint.config.js
{
  rules: {
    '@typescript-eslint/naming-convention': [
      'error',
      // Variables and functions
      {
        selector: 'variableLike',
        format: ['camelCase'],
      },
      // Constants
      {
        selector: 'variable',
        modifiers: ['const'],
        format: ['camelCase', 'UPPER_CASE'],
      },
      // Types and classes
      {
        selector: 'typeLike',
        format: ['PascalCase'],
      },
      // Interfaces without I prefix
      {
        selector: 'interface',
        format: ['PascalCase'],
        custom: {
          regex: '^I[A-Z]',
          match: false,
        },
      },
      // Enum members
      {
        selector: 'enumMember',
        format: ['PascalCase'],
      },
    ],
  },
}
```
