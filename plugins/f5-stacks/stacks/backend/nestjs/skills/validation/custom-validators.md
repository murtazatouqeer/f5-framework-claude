---
name: nestjs-custom-validators
description: Custom validation decorators in NestJS
applies_to: nestjs
category: validation
---

# Custom Validators in NestJS

## Basic Custom Decorator

```typescript
// common/validators/is-strong-password.validator.ts
import {
  registerDecorator,
  ValidationOptions,
  ValidationArguments,
} from 'class-validator';

export function IsStrongPassword(validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'isStrongPassword',
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      validator: {
        validate(value: any, args: ValidationArguments) {
          if (typeof value !== 'string') return false;

          const hasUpperCase = /[A-Z]/.test(value);
          const hasLowerCase = /[a-z]/.test(value);
          const hasNumber = /\d/.test(value);
          const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(value);
          const isLongEnough = value.length >= 8;

          return hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar && isLongEnough;
        },
        defaultMessage(args: ValidationArguments) {
          return `${args.property} must contain at least 8 characters with uppercase, lowercase, number, and special character`;
        },
      },
    });
  };
}

// Usage
export class RegisterDto {
  @IsStrongPassword()
  password: string;
}
```

## Validator with Options

```typescript
// common/validators/is-unique.validator.ts
import {
  registerDecorator,
  ValidationOptions,
  ValidationArguments,
  ValidatorConstraint,
  ValidatorConstraintInterface,
} from 'class-validator';
import { Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';

export interface IsUniqueOptions {
  entity: Function;
  column: string;
  excludeId?: string; // For updates - exclude current record
}

@Injectable()
@ValidatorConstraint({ name: 'isUnique', async: true })
export class IsUniqueConstraint implements ValidatorConstraintInterface {
  constructor(private dataSource: DataSource) {}

  async validate(value: any, args: ValidationArguments): Promise<boolean> {
    const [options] = args.constraints as [IsUniqueOptions];
    const { entity, column, excludeId } = options;

    const repository = this.dataSource.getRepository(entity);

    const queryBuilder = repository
      .createQueryBuilder('entity')
      .where(`entity.${column} = :value`, { value });

    // Exclude current record for updates
    if (excludeId) {
      const request = (args.object as any).__request__;
      const id = request?.params?.[excludeId];
      if (id) {
        queryBuilder.andWhere('entity.id != :id', { id });
      }
    }

    const count = await queryBuilder.getCount();
    return count === 0;
  }

  defaultMessage(args: ValidationArguments): string {
    const [options] = args.constraints as [IsUniqueOptions];
    return `${options.column} already exists`;
  }
}

export function IsUnique(
  options: IsUniqueOptions,
  validationOptions?: ValidationOptions,
) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      constraints: [options],
      validator: IsUniqueConstraint,
    });
  };
}

// Usage
export class CreateUserDto {
  @IsUnique({ entity: User, column: 'email' })
  email: string;
}

export class UpdateUserDto {
  @IsUnique({ entity: User, column: 'email', excludeId: 'id' })
  email: string;
}
```

## Async Validator with Service Injection

```typescript
// common/validators/user-exists.validator.ts
import {
  ValidatorConstraint,
  ValidatorConstraintInterface,
  ValidationArguments,
  registerDecorator,
  ValidationOptions,
} from 'class-validator';
import { Injectable } from '@nestjs/common';
import { UsersService } from '../../modules/users/users.service';

@Injectable()
@ValidatorConstraint({ name: 'userExists', async: true })
export class UserExistsConstraint implements ValidatorConstraintInterface {
  constructor(private usersService: UsersService) {}

  async validate(userId: string, args: ValidationArguments): Promise<boolean> {
    const user = await this.usersService.findById(userId);
    return !!user;
  }

  defaultMessage(args: ValidationArguments): string {
    return `User with ID ${args.value} does not exist`;
  }
}

export function UserExists(validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      validator: UserExistsConstraint,
    });
  };
}

// Register constraint in module
@Module({
  providers: [UserExistsConstraint],
})
export class ValidationModule {}

// Usage
export class CreateOrderDto {
  @UserExists()
  customerId: string;
}
```

## Cross-Field Validation

```typescript
// common/validators/match.validator.ts
import {
  registerDecorator,
  ValidationOptions,
  ValidationArguments,
} from 'class-validator';

export function Match(property: string, validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'match',
      target: object.constructor,
      propertyName: propertyName,
      constraints: [property],
      options: validationOptions,
      validator: {
        validate(value: any, args: ValidationArguments) {
          const [relatedPropertyName] = args.constraints;
          const relatedValue = (args.object as any)[relatedPropertyName];
          return value === relatedValue;
        },
        defaultMessage(args: ValidationArguments) {
          const [relatedPropertyName] = args.constraints;
          return `${args.property} must match ${relatedPropertyName}`;
        },
      },
    });
  };
}

// Usage
export class ChangePasswordDto {
  @IsString()
  @MinLength(8)
  password: string;

  @Match('password', { message: 'Passwords do not match' })
  confirmPassword: string;
}
```

## Comparison Validators

```typescript
// common/validators/is-greater-than.validator.ts
export function IsGreaterThan(
  property: string,
  validationOptions?: ValidationOptions,
) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'isGreaterThan',
      target: object.constructor,
      propertyName: propertyName,
      constraints: [property],
      options: validationOptions,
      validator: {
        validate(value: any, args: ValidationArguments) {
          const [relatedPropertyName] = args.constraints;
          const relatedValue = (args.object as any)[relatedPropertyName];
          return value > relatedValue;
        },
        defaultMessage(args: ValidationArguments) {
          const [relatedPropertyName] = args.constraints;
          return `${args.property} must be greater than ${relatedPropertyName}`;
        },
      },
    });
  };
}

// Usage
export class DateRangeDto {
  @IsDate()
  @Type(() => Date)
  startDate: Date;

  @IsDate()
  @Type(() => Date)
  @IsGreaterThan('startDate')
  endDate: Date;
}
```

## Business Rule Validators

```typescript
// common/validators/is-business-hours.validator.ts
export function IsBusinessHours(validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'isBusinessHours',
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      validator: {
        validate(value: any, args: ValidationArguments) {
          if (!(value instanceof Date)) return false;

          const hours = value.getHours();
          const day = value.getDay();

          const isWeekday = day >= 1 && day <= 5;
          const isBusinessHour = hours >= 9 && hours < 17;

          return isWeekday && isBusinessHour;
        },
        defaultMessage(args: ValidationArguments) {
          return `${args.property} must be during business hours (Mon-Fri, 9AM-5PM)`;
        },
      },
    });
  };
}

// common/validators/is-valid-credit-card.validator.ts
export function IsValidCreditCard(validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'isValidCreditCard',
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      validator: {
        validate(value: any, args: ValidationArguments) {
          if (typeof value !== 'string') return false;

          // Remove spaces and dashes
          const cardNumber = value.replace(/[\s-]/g, '');

          // Check if all digits
          if (!/^\d+$/.test(cardNumber)) return false;

          // Luhn algorithm
          let sum = 0;
          let isEven = false;

          for (let i = cardNumber.length - 1; i >= 0; i--) {
            let digit = parseInt(cardNumber[i], 10);

            if (isEven) {
              digit *= 2;
              if (digit > 9) {
                digit -= 9;
              }
            }

            sum += digit;
            isEven = !isEven;
          }

          return sum % 10 === 0;
        },
        defaultMessage(args: ValidationArguments) {
          return `${args.property} is not a valid credit card number`;
        },
      },
    });
  };
}
```

## File Validation

```typescript
// common/validators/is-valid-file.validator.ts
export interface FileValidationOptions {
  maxSize?: number; // in bytes
  mimeTypes?: string[];
}

export function IsValidFile(
  options: FileValidationOptions = {},
  validationOptions?: ValidationOptions,
) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'isValidFile',
      target: object.constructor,
      propertyName: propertyName,
      constraints: [options],
      options: validationOptions,
      validator: {
        validate(file: Express.Multer.File, args: ValidationArguments) {
          if (!file) return false;

          const [opts] = args.constraints as [FileValidationOptions];

          // Check file size
          if (opts.maxSize && file.size > opts.maxSize) {
            return false;
          }

          // Check mime type
          if (opts.mimeTypes && !opts.mimeTypes.includes(file.mimetype)) {
            return false;
          }

          return true;
        },
        defaultMessage(args: ValidationArguments) {
          const [opts] = args.constraints as [FileValidationOptions];
          const messages: string[] = [];

          if (opts.maxSize) {
            messages.push(`Max size: ${opts.maxSize / 1024 / 1024}MB`);
          }
          if (opts.mimeTypes) {
            messages.push(`Allowed types: ${opts.mimeTypes.join(', ')}`);
          }

          return `Invalid file. ${messages.join('. ')}`;
        },
      },
    });
  };
}

// Usage
export class UploadDto {
  @IsValidFile({
    maxSize: 5 * 1024 * 1024, // 5MB
    mimeTypes: ['image/jpeg', 'image/png', 'application/pdf'],
  })
  file: Express.Multer.File;
}
```

## Array Item Validation

```typescript
// common/validators/array-distinct.validator.ts
export function ArrayDistinct(
  property?: string,
  validationOptions?: ValidationOptions,
) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'arrayDistinct',
      target: object.constructor,
      propertyName: propertyName,
      constraints: [property],
      options: validationOptions,
      validator: {
        validate(value: any[], args: ValidationArguments) {
          if (!Array.isArray(value)) return false;

          const [prop] = args.constraints;

          const values = prop
            ? value.map((item) => item[prop])
            : value;

          return new Set(values).size === values.length;
        },
        defaultMessage(args: ValidationArguments) {
          return `${args.property} must contain unique items`;
        },
      },
    });
  };
}

// Usage
export class CreateOrderDto {
  @IsArray()
  @ArrayDistinct('productId', { message: 'Duplicate products not allowed' })
  @ValidateNested({ each: true })
  @Type(() => OrderItemDto)
  items: OrderItemDto[];
}
```

## Module Setup for Async Validators

```typescript
// common/validation/validation.module.ts
import { Module } from '@nestjs/common';
import { IsUniqueConstraint } from './validators/is-unique.validator';
import { UserExistsConstraint } from './validators/user-exists.validator';
import { UsersModule } from '../modules/users/users.module';

@Module({
  imports: [UsersModule],
  providers: [
    IsUniqueConstraint,
    UserExistsConstraint,
  ],
  exports: [
    IsUniqueConstraint,
    UserExistsConstraint,
  ],
})
export class ValidationModule {}

// app.module.ts
import { useContainer } from 'class-validator';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Enable DI in class-validator
  useContainer(app.select(AppModule), { fallbackOnErrors: true });

  await app.listen(3000);
}
```

## Best Practices

1. **Reusability**: Create generic validators
2. **Clear naming**: IsXxx convention
3. **Descriptive messages**: Help users fix issues
4. **Async awareness**: Use async validators for DB checks
5. **DI integration**: useContainer for service injection
6. **Test validators**: Unit test validation logic

## Checklist

- [ ] Custom validators for business rules
- [ ] Async validators for DB checks
- [ ] Cross-field validation
- [ ] useContainer configured for DI
- [ ] Validators registered in module
- [ ] Clear error messages
- [ ] Validators unit tested
