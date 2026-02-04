---
name: jsdoc-tsdoc
description: JSDoc and TSDoc documentation standards
category: code-quality/documentation
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# JSDoc and TSDoc

## Overview

JSDoc and TSDoc are documentation standards for JavaScript and TypeScript. They provide IDE support, generate documentation, and improve code understanding.

## Basic Syntax

### Function Documentation

```typescript
/**
 * Calculates the total price of an order including tax and discounts.
 *
 * @param order - The order to calculate
 * @param options - Calculation options
 * @returns The final price in cents
 *
 * @example
 * ```typescript
 * const total = calculateTotal(order, { includeTax: true });
 * console.log(total); // 12500 (cents)
 * ```
 */
function calculateTotal(order: Order, options: CalculationOptions): number {
  // implementation
}
```

### Class Documentation

```typescript
/**
 * Service for managing user authentication and sessions.
 *
 * Handles user login, logout, token management, and session validation.
 * Uses JWT for stateless authentication.
 *
 * @example
 * ```typescript
 * const authService = new AuthService(userRepo, tokenService);
 * const session = await authService.login(credentials);
 * ```
 */
class AuthService {
  /**
   * Creates an instance of AuthService.
   *
   * @param userRepository - Repository for user data access
   * @param tokenService - Service for JWT token management
   */
  constructor(
    private userRepository: UserRepository,
    private tokenService: TokenService
  ) {}

  /**
   * Authenticates a user and creates a new session.
   *
   * @param credentials - User login credentials
   * @returns A promise that resolves to the authenticated session
   * @throws {InvalidCredentialsError} When credentials are invalid
   * @throws {AccountLockedError} When account is locked
   */
  async login(credentials: LoginCredentials): Promise<Session> {
    // implementation
  }
}
```

### Interface Documentation

```typescript
/**
 * Configuration options for the API client.
 */
interface ApiClientConfig {
  /**
   * Base URL for API requests.
   * @example "https://api.example.com/v1"
   */
  baseUrl: string;

  /**
   * Request timeout in milliseconds.
   * @default 30000
   */
  timeout?: number;

  /**
   * Number of retry attempts for failed requests.
   * @default 3
   */
  retries?: number;

  /**
   * Custom headers to include in all requests.
   */
  headers?: Record<string, string>;
}
```

## Common Tags

### Parameter and Return Tags

```typescript
/**
 * Searches for users matching the given criteria.
 *
 * @param query - Search query string
 * @param options - Search options
 * @param options.limit - Maximum number of results (default: 10)
 * @param options.offset - Number of results to skip (default: 0)
 * @param options.sort - Sort order for results
 * @returns Array of matching users, empty if none found
 */
function searchUsers(
  query: string,
  options?: {
    limit?: number;
    offset?: number;
    sort?: 'asc' | 'desc';
  }
): User[] {}
```

### Throws Tag

```typescript
/**
 * Parses a JSON string into a typed object.
 *
 * @param json - The JSON string to parse
 * @returns The parsed object
 * @throws {SyntaxError} When JSON is malformed
 * @throws {ValidationError} When parsed data doesn't match expected schema
 */
function parseAndValidate<T>(json: string): T {
  try {
    const data = JSON.parse(json);
    return validate<T>(data);
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw error;
    }
    throw new ValidationError('Invalid data structure');
  }
}
```

### Example Tag

```typescript
/**
 * Formats a date according to the specified format string.
 *
 * @param date - The date to format
 * @param format - Format string using tokens
 * @returns Formatted date string
 *
 * @example
 * Basic usage:
 * ```typescript
 * formatDate(new Date('2024-01-15'), 'YYYY-MM-DD');
 * // Returns: '2024-01-15'
 * ```
 *
 * @example
 * With time:
 * ```typescript
 * formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss');
 * // Returns: '2024-01-15 14:30:00'
 * ```
 *
 * @example
 * Custom separators:
 * ```typescript
 * formatDate(new Date('2024-01-15'), 'DD/MM/YYYY');
 * // Returns: '15/01/2024'
 * ```
 */
function formatDate(date: Date, format: string): string {}
```

### Deprecation Tags

```typescript
/**
 * Fetches user by ID.
 *
 * @deprecated Use {@link UserService.findById} instead.
 * This function will be removed in version 3.0.0.
 *
 * @param id - User ID
 * @returns User object or null
 */
function getUser(id: string): User | null {}

/**
 * @deprecated since version 2.0.0
 * @see {@link newFunction} for the replacement
 */
function oldFunction() {}
```

### Link and See Tags

```typescript
/**
 * Creates a new order from cart items.
 *
 * @see {@link CartService.getItems} for retrieving cart items
 * @see {@link PaymentService.process} for processing payment
 * @link https://docs.example.com/orders
 *
 * Related methods:
 * - {@link OrderService.cancel}
 * - {@link OrderService.refund}
 */
function createOrderFromCart(cartId: string): Order {}
```

## TypeScript-Specific Tags

### Type Parameters

```typescript
/**
 * A generic repository for data access operations.
 *
 * @typeParam T - The entity type managed by this repository
 * @typeParam ID - The type of the entity's identifier
 *
 * @example
 * ```typescript
 * class UserRepository extends Repository<User, string> {
 *   // User-specific methods
 * }
 * ```
 */
abstract class Repository<T extends Entity, ID = string> {
  /**
   * Finds an entity by its identifier.
   *
   * @param id - The entity identifier
   * @returns The entity or undefined if not found
   */
  abstract findById(id: ID): T | undefined;
}
```

### Template Tags (for generics)

```typescript
/**
 * Wraps a value in a Result type for error handling.
 *
 * @template T - The success value type
 * @template E - The error type
 * @param value - The value to wrap
 * @returns A successful Result containing the value
 */
function success<T, E = Error>(value: T): Result<T, E> {
  return { success: true, value };
}
```

## Documentation Best Practices

### Be Concise but Complete

```typescript
// ❌ Too verbose
/**
 * This function is used to validate an email address. It takes a string
 * parameter that represents the email address that needs to be validated.
 * The function will return true if the email address is valid according
 * to the standard email format, and false if it is not valid.
 */
function validateEmail(email: string): boolean {}

// ✅ Concise and complete
/**
 * Validates an email address format.
 *
 * @param email - Email address to validate
 * @returns `true` if valid, `false` otherwise
 */
function validateEmail(email: string): boolean {}
```

### Document Edge Cases

```typescript
/**
 * Divides two numbers.
 *
 * @param dividend - The number to be divided
 * @param divisor - The number to divide by
 * @returns The quotient
 * @throws {DivisionByZeroError} When divisor is zero
 *
 * @remarks
 * - Returns `Infinity` when dividend is non-zero and divisor approaches zero
 * - Returns `NaN` when both dividend and divisor are zero
 */
function divide(dividend: number, divisor: number): number {}
```

### Use Remarks for Additional Context

```typescript
/**
 * Sends a notification to the user.
 *
 * @param userId - Target user ID
 * @param message - Notification content
 *
 * @remarks
 * This method queues notifications for batch processing.
 * Actual delivery may be delayed up to 5 minutes.
 *
 * Rate limits apply:
 * - 100 notifications per user per hour
 * - 1000 notifications per app per minute
 *
 * @see {@link NotificationQueue} for queue implementation details
 */
async function sendNotification(userId: string, message: string): Promise<void> {}
```

## Generating Documentation

### TypeDoc Configuration

```json
// typedoc.json
{
  "entryPoints": ["src/index.ts"],
  "out": "docs",
  "theme": "default",
  "excludePrivate": true,
  "excludeProtected": false,
  "includeVersion": true,
  "readme": "README.md",
  "plugin": ["typedoc-plugin-markdown"]
}
```

### Package Scripts

```json
{
  "scripts": {
    "docs": "typedoc",
    "docs:watch": "typedoc --watch",
    "docs:serve": "typedoc && npx serve docs"
  }
}
```

## IDE Integration

### VS Code Settings

```json
{
  "editor.quickSuggestions": {
    "comments": true
  },
  "typescript.suggest.completeJSDocs": true
}
```

### Auto-completion

```typescript
// Type /** and press Enter to auto-generate JSDoc skeleton
/**
 * |
 */
function myFunction(param1: string, param2: number): boolean {}

// VS Code generates:
/**
 *
 * @param param1
 * @param param2
 * @returns
 */
function myFunction(param1: string, param2: number): boolean {}
```

## Quick Reference

| Tag | Purpose | Example |
|-----|---------|---------|
| `@param` | Document parameter | `@param name - User's name` |
| `@returns` | Document return value | `@returns The user object` |
| `@throws` | Document exceptions | `@throws {Error} When invalid` |
| `@example` | Provide usage example | `@example \`\`\`ts ... \`\`\`` |
| `@deprecated` | Mark as deprecated | `@deprecated Use X instead` |
| `@see` | Reference related docs | `@see {@link OtherClass}` |
| `@since` | Version introduced | `@since 2.0.0` |
| `@template` | Generic type parameter | `@template T - Item type` |
| `@remarks` | Additional information | `@remarks Implementation notes` |
| `@default` | Default value | `@default 100` |
| `@internal` | Internal API | `@internal` |
| `@public` | Public API | `@public` |
| `@private` | Private member | `@private` |
| `@readonly` | Read-only property | `@readonly` |
