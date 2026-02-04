---
name: input-validation
description: API input validation and sanitization
category: security/api-security
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# API Input Validation

## Overview

Input validation is the first line of defense against malicious data.
All external input must be validated before processing.

## Validation Layers

```
┌─────────────────────────────────────────────────────────────┐
│                   Input Validation Layers                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Transport Layer    → Content-Type, Size limits          │
│  2. Schema Validation  → Type, format, required fields      │
│  3. Business Rules     → Domain-specific validation         │
│  4. Sanitization       → Clean/escape potentially harmful   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Schema Validation with Zod

```typescript
// validation/schemas/user.schema.ts
import { z } from 'zod';

// Base schemas
const emailSchema = z.string()
  .email('Invalid email format')
  .max(255)
  .toLowerCase()
  .trim();

const passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .max(128, 'Password must be less than 128 characters')
  .regex(/[a-z]/, 'Password must contain a lowercase letter')
  .regex(/[A-Z]/, 'Password must contain an uppercase letter')
  .regex(/\d/, 'Password must contain a number')
  .regex(/[^a-zA-Z0-9]/, 'Password must contain a special character');

const nameSchema = z.string()
  .min(1, 'Name is required')
  .max(100)
  .regex(/^[\p{L}\s\-']+$/u, 'Name contains invalid characters')
  .trim();

// User schemas
export const createUserSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
  name: nameSchema,
  phone: z.string()
    .regex(/^\+?[\d\s\-()]+$/, 'Invalid phone format')
    .optional(),
  role: z.enum(['user', 'admin', 'moderator']).default('user'),
  preferences: z.object({
    theme: z.enum(['light', 'dark']).default('light'),
    notifications: z.boolean().default(true),
    language: z.string().length(2).default('en'),
  }).optional(),
});

export const updateUserSchema = createUserSchema.partial().omit({
  password: true,
  role: true, // Can't change own role
});

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required'),
  rememberMe: z.boolean().optional(),
});

// Type inference
export type CreateUserInput = z.infer<typeof createUserSchema>;
export type UpdateUserInput = z.infer<typeof updateUserSchema>;
```

### Complex Validation

```typescript
// validation/schemas/order.schema.ts
export const createOrderSchema = z.object({
  items: z.array(
    z.object({
      productId: z.string().uuid(),
      quantity: z.number().int().positive().max(100),
      options: z.record(z.string()).optional(),
    })
  )
  .min(1, 'Order must have at least one item')
  .max(50, 'Order cannot have more than 50 items'),

  shippingAddress: z.object({
    street: z.string().min(1).max(200),
    city: z.string().min(1).max(100),
    state: z.string().min(1).max(100),
    postalCode: z.string().regex(/^[\w\s\-]+$/),
    country: z.string().length(2), // ISO country code
  }),

  paymentMethod: z.discriminatedUnion('type', [
    z.object({
      type: z.literal('card'),
      cardId: z.string().uuid(),
    }),
    z.object({
      type: z.literal('bank'),
      bankAccountId: z.string().uuid(),
    }),
    z.object({
      type: z.literal('wallet'),
      walletType: z.enum(['apple', 'google', 'paypal']),
    }),
  ]),

  couponCode: z.string()
    .regex(/^[A-Z0-9\-]+$/)
    .max(20)
    .optional(),

  notes: z.string()
    .max(500)
    .optional()
    .transform(val => val?.trim()),
})
.refine(
  data => data.items.length > 0,
  { message: 'Order must have at least one item' }
);
```

## Validation Middleware

```typescript
// middleware/validate.middleware.ts
import { ZodSchema, ZodError } from 'zod';

type ValidationTarget = 'body' | 'query' | 'params';

export function validate(
  schema: ZodSchema,
  target: ValidationTarget = 'body'
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const data = req[target];
      const validated = await schema.parseAsync(data);

      // Replace with validated/transformed data
      req[target] = validated;

      next();
    } catch (error) {
      if (error instanceof ZodError) {
        const errors = error.errors.map(e => ({
          path: e.path.join('.'),
          message: e.message,
          code: e.code,
        }));

        return res.status(400).json({
          error: 'Validation Error',
          details: errors,
        });
      }
      next(error);
    }
  };
}

// Multiple validations
export function validateRequest(schemas: {
  body?: ZodSchema;
  query?: ZodSchema;
  params?: ZodSchema;
}) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const results: Record<string, any> = {};

      for (const [target, schema] of Object.entries(schemas)) {
        if (schema) {
          results[target] = await schema.parseAsync(req[target as ValidationTarget]);
        }
      }

      // Replace with validated data
      Object.assign(req, results);

      next();
    } catch (error) {
      if (error instanceof ZodError) {
        return res.status(400).json({
          error: 'Validation Error',
          details: error.errors,
        });
      }
      next(error);
    }
  };
}

// Usage
router.post(
  '/orders',
  validate(createOrderSchema),
  createOrder
);

router.get(
  '/orders/:id',
  validateRequest({
    params: z.object({ id: z.string().uuid() }),
    query: z.object({ include: z.string().optional() }),
  }),
  getOrder
);
```

## NestJS Validation

```typescript
// dto/create-user.dto.ts
import { IsEmail, IsString, MinLength, MaxLength, IsOptional, Matches, ValidateNested, IsEnum } from 'class-validator';
import { Type, Transform } from 'class-transformer';

export class CreateUserDto {
  @IsEmail()
  @MaxLength(255)
  @Transform(({ value }) => value.toLowerCase().trim())
  email: string;

  @IsString()
  @MinLength(8)
  @MaxLength(128)
  @Matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9])/, {
    message: 'Password too weak',
  })
  password: string;

  @IsString()
  @MinLength(1)
  @MaxLength(100)
  @Transform(({ value }) => value.trim())
  name: string;

  @IsOptional()
  @IsString()
  @Matches(/^\+?[\d\s\-()]+$/)
  phone?: string;

  @IsOptional()
  @ValidateNested()
  @Type(() => UserPreferencesDto)
  preferences?: UserPreferencesDto;
}

export class UserPreferencesDto {
  @IsEnum(['light', 'dark'])
  theme: 'light' | 'dark';

  @IsBoolean()
  notifications: boolean;
}

// main.ts - Enable global validation pipe
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,           // Strip unknown properties
    forbidNonWhitelisted: true, // Throw on unknown properties
    transform: true,           // Auto-transform types
    transformOptions: {
      enableImplicitConversion: true,
    },
  })
);
```

## Input Sanitization

```typescript
// services/sanitizer.service.ts
import DOMPurify from 'dompurify';
import { JSDOM } from 'jsdom';
import validator from 'validator';

const window = new JSDOM('').window;
const purify = DOMPurify(window);

export class SanitizerService {
  // Sanitize HTML to prevent XSS
  sanitizeHtml(input: string, options?: SanitizeOptions): string {
    return purify.sanitize(input, {
      ALLOWED_TAGS: options?.allowedTags || ['b', 'i', 'em', 'strong', 'p', 'br'],
      ALLOWED_ATTR: options?.allowedAttributes || [],
      ALLOW_DATA_ATTR: false,
    });
  }

  // Remove all HTML tags
  stripHtml(input: string): string {
    return purify.sanitize(input, { ALLOWED_TAGS: [] });
  }

  // Sanitize for SQL (defense in depth)
  sanitizeForSql(input: string): string {
    return validator.escape(input);
  }

  // Sanitize filename
  sanitizeFilename(filename: string): string {
    return filename
      .replace(/[^a-zA-Z0-9.\-_]/g, '_')
      .replace(/\.{2,}/g, '.')
      .slice(0, 255);
  }

  // Sanitize URL
  sanitizeUrl(url: string): string | null {
    try {
      const parsed = new URL(url);
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        return null;
      }
      return parsed.href;
    } catch {
      return null;
    }
  }

  // Generic object sanitization
  sanitizeObject<T extends object>(
    obj: T,
    rules: SanitizationRules<T>
  ): T {
    const result = { ...obj };

    for (const [key, rule] of Object.entries(rules)) {
      if (key in result && result[key] != null) {
        switch (rule) {
          case 'html':
            result[key] = this.sanitizeHtml(result[key]);
            break;
          case 'stripHtml':
            result[key] = this.stripHtml(result[key]);
            break;
          case 'escape':
            result[key] = validator.escape(result[key]);
            break;
          case 'trim':
            result[key] = String(result[key]).trim();
            break;
          case 'lowercase':
            result[key] = String(result[key]).toLowerCase();
            break;
          case 'url':
            result[key] = this.sanitizeUrl(result[key]);
            break;
        }
      }
    }

    return result;
  }
}
```

## Request Size Limits

```typescript
// middleware/size-limit.middleware.ts
import express from 'express';

// JSON body size limit
app.use(express.json({
  limit: '100kb',
  strict: true, // Only accept arrays and objects
}));

// URL-encoded body size limit
app.use(express.urlencoded({
  limit: '100kb',
  extended: false,
  parameterLimit: 100, // Max number of parameters
}));

// File upload limits
import multer from 'multer';

const upload = multer({
  limits: {
    fileSize: 5 * 1024 * 1024, // 5MB
    files: 5, // Max 5 files
    fields: 10, // Max 10 non-file fields
  },
  fileFilter: (req, file, cb) => {
    const allowedMimes = ['image/jpeg', 'image/png', 'application/pdf'];
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type'));
    }
  },
});

// Custom size limit per endpoint
export function jsonSizeLimit(limit: string) {
  return express.json({ limit });
}

router.post('/api/bulk-import', jsonSizeLimit('10mb'), bulkImport);
```

## Query Parameter Validation

```typescript
// validation/query.validation.ts
export const paginationSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),
});

export const filterSchema = z.object({
  search: z.string().max(100).optional(),
  status: z.enum(['active', 'inactive', 'pending']).optional(),
  dateFrom: z.coerce.date().optional(),
  dateTo: z.coerce.date().optional(),
  tags: z.string()
    .transform(val => val.split(',').map(t => t.trim()))
    .optional(),
}).refine(
  data => {
    if (data.dateFrom && data.dateTo) {
      return data.dateFrom <= data.dateTo;
    }
    return true;
  },
  { message: 'dateFrom must be before dateTo' }
);

// Combined schema
export const listQuerySchema = paginationSchema.merge(filterSchema);
```

## Custom Validators

```typescript
// validation/custom.validators.ts
import { z } from 'zod';

// Credit card (Luhn algorithm)
export const creditCardSchema = z.string().refine(
  (val) => {
    const digits = val.replace(/\D/g, '');
    if (digits.length < 13 || digits.length > 19) return false;

    let sum = 0;
    let isEven = false;

    for (let i = digits.length - 1; i >= 0; i--) {
      let digit = parseInt(digits[i], 10);

      if (isEven) {
        digit *= 2;
        if (digit > 9) digit -= 9;
      }

      sum += digit;
      isEven = !isEven;
    }

    return sum % 10 === 0;
  },
  { message: 'Invalid credit card number' }
);

// Phone number (E.164 format)
export const phoneE164Schema = z.string().regex(
  /^\+[1-9]\d{1,14}$/,
  'Phone must be in E.164 format (+1234567890)'
);

// URL with specific domains
export const trustedUrlSchema = z.string().url().refine(
  (val) => {
    const url = new URL(val);
    const trustedDomains = ['example.com', 'trusted.org'];
    return trustedDomains.some(d => url.hostname.endsWith(d));
  },
  { message: 'URL must be from a trusted domain' }
);

// UUID v4
export const uuidV4Schema = z.string().uuid();

// ISO date string
export const isoDateSchema = z.string().datetime();
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Validate early | Validate at API boundary |
| Whitelist | Allow known good, reject unknown |
| Type coercion | Convert types explicitly |
| Sanitize output | Context-appropriate escaping |
| Size limits | Limit request body and file sizes |
| Error messages | Clear but not revealing |
