---
name: nestjs-dto-validation
description: DTO validation with class-validator in NestJS
applies_to: nestjs
category: validation
---

# NestJS DTO Validation

## Setup

```bash
npm install class-validator class-transformer
```

```typescript
// main.ts
import { ValidationPipe } from '@nestjs/common';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,           // Strip non-decorated properties
      forbidNonWhitelisted: true, // Throw error for extra properties
      transform: true,            // Transform payloads to DTO instances
      transformOptions: {
        enableImplicitConversion: true, // Convert types automatically
      },
    }),
  );

  await app.listen(3000);
}
```

## Common Validation Decorators

### String Validation

```typescript
import {
  IsString,
  IsNotEmpty,
  MinLength,
  MaxLength,
  IsEmail,
  IsUrl,
  IsUUID,
  Matches,
  IsAlpha,
  IsAlphanumeric,
} from 'class-validator';

export class CreateUserDto {
  @IsString()
  @IsNotEmpty()
  @MinLength(2)
  @MaxLength(100)
  name: string;

  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  @MaxLength(100)
  @Matches(/^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/, {
    message: 'Password must contain uppercase, lowercase, number, and special character',
  })
  password: string;

  @IsUrl()
  @IsOptional()
  website?: string;

  @IsUUID()
  organizationId: string;

  @IsAlpha()
  countryCode: string;

  @IsAlphanumeric()
  username: string;
}
```

### Number Validation

```typescript
import {
  IsNumber,
  IsInt,
  IsPositive,
  IsNegative,
  Min,
  Max,
  IsDivisibleBy,
} from 'class-validator';

export class CreateProductDto {
  @IsNumber()
  @IsPositive()
  @Max(999999.99)
  price: number;

  @IsInt()
  @Min(0)
  stock: number;

  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0)
  @Max(100)
  discountPercent: number;

  @IsInt()
  @IsDivisibleBy(10)
  bulkQuantity: number;
}
```

### Array Validation

```typescript
import {
  IsArray,
  ArrayMinSize,
  ArrayMaxSize,
  ArrayUnique,
  ValidateNested,
} from 'class-validator';
import { Type } from 'class-transformer';

export class CreateOrderDto {
  @IsArray()
  @ArrayMinSize(1)
  @ArrayMaxSize(100)
  @ValidateNested({ each: true })
  @Type(() => OrderItemDto)
  items: OrderItemDto[];

  @IsArray()
  @IsString({ each: true })
  @ArrayUnique()
  tags: string[];
}

export class OrderItemDto {
  @IsUUID()
  productId: string;

  @IsInt()
  @Min(1)
  quantity: number;
}
```

### Object Validation

```typescript
import { ValidateNested, IsObject } from 'class-validator';
import { Type } from 'class-transformer';

export class AddressDto {
  @IsString()
  @IsNotEmpty()
  street: string;

  @IsString()
  @IsNotEmpty()
  city: string;

  @IsString()
  @Length(5, 10)
  postalCode: string;

  @IsString()
  @Length(2, 2)
  countryCode: string;
}

export class CreateOrderDto {
  @ValidateNested()
  @Type(() => AddressDto)
  shippingAddress: AddressDto;

  @ValidateNested()
  @Type(() => AddressDto)
  @IsOptional()
  billingAddress?: AddressDto;
}
```

### Enum Validation

```typescript
import { IsEnum, IsIn } from 'class-validator';

export enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  SHIPPED = 'shipped',
}

export class UpdateOrderDto {
  @IsEnum(OrderStatus)
  status: OrderStatus;

  // Or using IsIn for simple values
  @IsIn(['asc', 'desc'])
  sortOrder: 'asc' | 'desc';
}
```

### Date Validation

```typescript
import { IsDate, MinDate, MaxDate, IsDateString } from 'class-validator';
import { Type } from 'class-transformer';

export class CreateEventDto {
  @IsDateString()
  startDate: string;

  @IsDate()
  @Type(() => Date)
  @MinDate(new Date())
  scheduledDate: Date;

  @IsDate()
  @Type(() => Date)
  @MaxDate(new Date('2030-12-31'))
  endDate: Date;
}
```

### Conditional Validation

```typescript
import { ValidateIf, IsNotEmpty, IsString, Equals } from 'class-validator';

export class PaymentDto {
  @IsIn(['credit_card', 'bank_transfer', 'paypal'])
  paymentMethod: string;

  // Only validate if payment method is credit_card
  @ValidateIf((o) => o.paymentMethod === 'credit_card')
  @IsNotEmpty()
  @Matches(/^\d{16}$/)
  cardNumber: string;

  // Only validate if payment method is bank_transfer
  @ValidateIf((o) => o.paymentMethod === 'bank_transfer')
  @IsNotEmpty()
  @IsString()
  bankAccount: string;

  // Only validate if payment method is paypal
  @ValidateIf((o) => o.paymentMethod === 'paypal')
  @IsEmail()
  paypalEmail: string;
}
```

### Optional Fields

```typescript
import { IsOptional, IsString, ValidateIf } from 'class-validator';

export class UpdateUserDto {
  @IsOptional()
  @IsString()
  @MinLength(2)
  name?: string;

  // Different from IsOptional - validates if provided but allows undefined
  @ValidateIf((o) => o.bio !== undefined)
  @IsString()
  @MaxLength(500)
  bio?: string;
}
```

## Transformation

```typescript
import { Transform, Type, Expose, Exclude } from 'class-transformer';

export class QueryDto {
  // Transform query param to number
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page: number = 1;

  // Transform and constrain
  @Transform(({ value }) => Math.min(100, Math.max(1, parseInt(value) || 10)))
  @IsInt()
  limit: number = 10;

  // Trim and lowercase
  @Transform(({ value }) => value?.trim().toLowerCase())
  @IsString()
  @IsOptional()
  search?: string;

  // Parse boolean from string
  @Transform(({ value }) => value === 'true' || value === true)
  @IsBoolean()
  @IsOptional()
  active?: boolean;

  // Parse array from comma-separated string
  @Transform(({ value }) => (typeof value === 'string' ? value.split(',') : value))
  @IsArray()
  @IsOptional()
  ids?: string[];
}
```

## Response DTOs

```typescript
import { Expose, Exclude, Type, Transform } from 'class-transformer';

@Exclude() // Exclude all by default
export class UserResponseDto {
  @Expose()
  id: string;

  @Expose()
  email: string;

  @Expose()
  name: string;

  @Expose()
  @Transform(({ value }) => value.toISOString())
  createdAt: Date;

  // Not exposed - sensitive data
  passwordHash: string;

  @Expose()
  @Type(() => OrderResponseDto)
  orders: OrderResponseDto[];

  constructor(partial: Partial<UserResponseDto>) {
    Object.assign(this, partial);
  }
}

// Usage in controller
@Get(':id')
async findOne(@Param('id') id: string): Promise<UserResponseDto> {
  const user = await this.usersService.findById(id);
  return plainToInstance(UserResponseDto, user, {
    excludeExtraneousValues: true,
  });
}
```

## DTO Composition

```typescript
import { PartialType, PickType, OmitType, IntersectionType } from '@nestjs/swagger';

// Base DTO
export class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  name: string;

  @IsString()
  password: string;

  @IsEnum(Role)
  role: Role;
}

// All fields optional
export class UpdateUserDto extends PartialType(CreateUserDto) {}

// Only specific fields
export class UpdateEmailDto extends PickType(CreateUserDto, ['email'] as const) {}

// All except some fields
export class CreateUserByAdminDto extends OmitType(CreateUserDto, ['role'] as const) {}

// Combine DTOs
export class CreateUserWithProfileDto extends IntersectionType(
  CreateUserDto,
  CreateProfileDto,
) {}
```

## Validation Groups

```typescript
export class CreateUserDto {
  @IsEmail({ groups: ['create', 'update'] })
  email: string;

  @IsString({ groups: ['create'] })
  @MinLength(8, { groups: ['create'] })
  password: string;

  @IsString({ groups: ['create', 'update'] })
  name: string;
}

// In controller
@Post()
async create(@Body(new ValidationPipe({ groups: ['create'] })) dto: CreateUserDto) {}

@Patch(':id')
async update(@Body(new ValidationPipe({ groups: ['update'] })) dto: CreateUserDto) {}
```

## Custom Validation Messages

```typescript
export class CreateUserDto {
  @IsEmail({}, { message: 'Please provide a valid email address' })
  email: string;

  @IsString({ message: 'Name must be a string' })
  @MinLength(2, { message: 'Name must be at least 2 characters long' })
  @MaxLength(100, { message: 'Name cannot exceed 100 characters' })
  name: string;

  @Matches(/^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)/, {
    message: 'Password must contain at least one uppercase, lowercase, and number',
  })
  password: string;
}
```

## Best Practices

1. **Validate at boundaries**: DTOs at controller level
2. **Whitelist properties**: Strip unknown properties
3. **Transform inputs**: Sanitize and normalize data
4. **Use composition**: Extend/pick from base DTOs
5. **Group validations**: Different rules for create/update
6. **Clear messages**: User-friendly validation errors
7. **Test validations**: Unit test DTO validation

## Checklist

- [ ] ValidationPipe configured globally
- [ ] DTOs for all request payloads
- [ ] Proper validation decorators
- [ ] Transformation where needed
- [ ] Response DTOs for output
- [ ] Clear validation messages
- [ ] Validation groups if needed
