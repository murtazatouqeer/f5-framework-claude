---
name: typescript-strict
description: TypeScript strict mode configuration for maximum type safety
category: code-quality/static-analysis
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# TypeScript Strict Mode

## Overview

TypeScript strict mode enables all strict type-checking options, catching more errors at compile time and improving code quality.

## tsconfig.json - Strict Configuration

```json
{
  "compilerOptions": {
    // Strict mode - enables all strict options
    "strict": true,

    // Individual strict options (enabled by strict: true)
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "useUnknownInCatchVariables": true,
    "alwaysStrict": true,

    // Additional strict options (not in strict: true)
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "exactOptionalPropertyTypes": true,

    // Module resolution
    "moduleResolution": "bundler",
    "module": "ESNext",
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],

    // Output
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "./dist",

    // Other
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## What Each Strict Option Does

### noImplicitAny

```typescript
// ❌ Error: Parameter 'x' implicitly has an 'any' type
function add(x, y) {
  return x + y;
}

// ✅ Correct
function add(x: number, y: number): number {
  return x + y;
}
```

### strictNullChecks

```typescript
// ❌ Error: Object is possibly 'undefined'
function getLength(str?: string) {
  return str.length;
}

// ✅ Correct
function getLength(str?: string): number {
  return str?.length ?? 0;
}
```

### strictFunctionTypes

```typescript
interface Animal {
  name: string;
}

interface Dog extends Animal {
  breed: string;
}

// ❌ Error: Type '(animal: Animal) => void' is not assignable
let dogHandler: (dog: Dog) => void;
const animalHandler = (animal: Animal) => {};
dogHandler = animalHandler; // Error in strict mode

// ✅ Correct - Use same or narrower type
const dogSpecificHandler = (dog: Dog) => console.log(dog.breed);
dogHandler = dogSpecificHandler;
```

### strictBindCallApply

```typescript
function greet(name: string, age: number) {
  return `Hello ${name}, you are ${age}`;
}

// ❌ Error: Argument of type 'string' is not assignable to type 'number'
greet.call(undefined, 'Alice', 'twenty');

// ✅ Correct
greet.call(undefined, 'Alice', 25);
```

### strictPropertyInitialization

```typescript
// ❌ Error: Property 'name' has no initializer
class User {
  name: string;
  email: string;
}

// ✅ Correct
class User {
  name: string;
  email: string;

  constructor(name: string, email: string) {
    this.name = name;
    this.email = email;
  }
}

// ✅ Or with definite assignment assertion (use carefully)
class User {
  name!: string; // Will be initialized elsewhere
}
```

### noUncheckedIndexedAccess

```typescript
const array = [1, 2, 3];

// Without noUncheckedIndexedAccess: item is number
// With noUncheckedIndexedAccess: item is number | undefined
const item = array[5];

// ✅ Correct handling
if (item !== undefined) {
  console.log(item.toFixed(2));
}

// ✅ Or use assertion after validation
const items = [1, 2, 3];
const firstItem = items[0]!; // Use ! only when you're certain
```

### exactOptionalPropertyTypes

```typescript
interface Config {
  debug?: boolean;
}

// ❌ Error: Type 'undefined' is not assignable to type 'boolean'
const config: Config = {
  debug: undefined, // Must be boolean or omitted entirely
};

// ✅ Correct
const config1: Config = { debug: true };
const config2: Config = {}; // debug omitted
```

## Practical Patterns

### Type Guards

```typescript
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function processValue(value: unknown) {
  if (isString(value)) {
    // value is now string
    console.log(value.toUpperCase());
  }
}
```

### Non-Null Assertion (Use Sparingly)

```typescript
// Only use when you're certain the value exists
const element = document.getElementById('app')!;

// Better: Explicit check
const element = document.getElementById('app');
if (!element) {
  throw new Error('App element not found');
}
```

### Optional Chaining & Nullish Coalescing

```typescript
interface User {
  profile?: {
    address?: {
      city?: string;
    };
  };
}

function getCity(user: User): string {
  // Safe navigation
  return user.profile?.address?.city ?? 'Unknown';
}
```

### Type Assertions

```typescript
// Prefer type guards over assertions when possible
const data = JSON.parse(response) as User; // Type assertion

// Better: Validate at runtime
function isUser(data: unknown): data is User {
  return (
    typeof data === 'object' &&
    data !== null &&
    'name' in data &&
    'email' in data
  );
}

const data = JSON.parse(response);
if (!isUser(data)) {
  throw new Error('Invalid user data');
}
```

## Migration to Strict Mode

### Gradual Migration

```json
{
  "compilerOptions": {
    // Start with these
    "noImplicitAny": true,
    "strictNullChecks": true,
    
    // Add these next
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    
    // Finally enable full strict
    "strict": true
  }
}
```

### Per-File Opt-Out

```typescript
// @ts-nocheck - Disable all type checking for this file (last resort)

// @ts-ignore - Ignore next line only
// @ts-ignore
const x = somethingUnsafe();

// @ts-expect-error - Better than @ts-ignore, fails if no error
// @ts-expect-error - This is expected to fail
const y = intentionallyWrong();
```

## Common Strict Mode Errors

| Error | Solution |
|-------|----------|
| Object is possibly 'undefined' | Add null check or optional chaining |
| Parameter 'x' implicitly has 'any' type | Add explicit type annotation |
| Property has no initializer | Initialize in constructor or use `!` |
| Type 'undefined' not assignable | Omit property or provide value |
| Argument not assignable to parameter | Check types match exactly |

## IDE Integration

### VS Code Settings

```json
{
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "typescript.preferences.strictNullChecks": true
}
```
