---
name: nestjs-modular-architecture
description: NestJS Modular Architecture patterns and best practices
applies_to: nestjs
category: architecture
---

# NestJS Modular Architecture

## Overview

NestJS modules are the fundamental building blocks for organizing application code.
Each module encapsulates a closely related set of capabilities.

## When to Use

- Default architecture for most NestJS projects
- Small to medium applications
- Teams familiar with Angular patterns
- Projects needing clear separation of concerns

## Module Organization Patterns

### Pattern 1: Feature Module

Each feature has its own module containing all related code.

```typescript
// src/modules/users/users.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';
import { UsersRepository } from './users.repository';
import { User } from './entities/user.entity';

@Module({
  imports: [TypeOrmModule.forFeature([User])],
  controllers: [UsersController],
  providers: [UsersService, UsersRepository],
  exports: [UsersService], // Export for other modules
})
export class UsersModule {}
```

**Structure:**
```
src/modules/users/
├── users.module.ts
├── users.controller.ts
├── users.service.ts
├── users.repository.ts
├── dto/
│   ├── create-user.dto.ts
│   ├── update-user.dto.ts
│   └── user-response.dto.ts
├── entities/
│   └── user.entity.ts
├── interfaces/
│   └── user.interface.ts
└── __tests__/
    ├── users.controller.spec.ts
    └── users.service.spec.ts
```

### Pattern 2: Shared Module

Common utilities shared across features.

```typescript
// src/common/common.module.ts
import { Global, Module } from '@nestjs/common';
import { LoggerService } from './services/logger.service';
import { CacheService } from './services/cache.service';

@Global() // Available everywhere without importing
@Module({
  providers: [LoggerService, CacheService],
  exports: [LoggerService, CacheService],
})
export class CommonModule {}
```

### Pattern 3: Core Module

Application-wide singletons (config, database connection).

```typescript
// src/core/core.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: `.env.${process.env.NODE_ENV}`,
    }),
    TypeOrmModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        host: config.get('DB_HOST'),
        port: config.get('DB_PORT'),
        username: config.get('DB_USERNAME'),
        password: config.get('DB_PASSWORD'),
        database: config.get('DB_DATABASE'),
        autoLoadEntities: true,
        synchronize: config.get('NODE_ENV') === 'development',
      }),
    }),
  ],
})
export class CoreModule {}
```

### Pattern 4: Dynamic Module

Configurable modules with factory providers.

```typescript
// src/common/email/email.module.ts
import { Module, DynamicModule } from '@nestjs/common';
import { EmailService } from './email.service';

export interface EmailModuleOptions {
  provider: 'sendgrid' | 'mailgun' | 'ses';
  apiKey: string;
  from: string;
}

@Module({})
export class EmailModule {
  static forRoot(options: EmailModuleOptions): DynamicModule {
    return {
      module: EmailModule,
      global: true,
      providers: [
        {
          provide: 'EMAIL_OPTIONS',
          useValue: options,
        },
        EmailService,
      ],
      exports: [EmailService],
    };
  }

  static forRootAsync(options: {
    useFactory: (...args: any[]) => EmailModuleOptions | Promise<EmailModuleOptions>;
    inject?: any[];
  }): DynamicModule {
    return {
      module: EmailModule,
      global: true,
      providers: [
        {
          provide: 'EMAIL_OPTIONS',
          useFactory: options.useFactory,
          inject: options.inject || [],
        },
        EmailService,
      ],
      exports: [EmailService],
    };
  }
}

// Usage
@Module({
  imports: [
    EmailModule.forRootAsync({
      useFactory: (config: ConfigService) => ({
        provider: config.get('EMAIL_PROVIDER'),
        apiKey: config.get('EMAIL_API_KEY'),
        from: config.get('EMAIL_FROM'),
      }),
      inject: [ConfigService],
    }),
  ],
})
export class AppModule {}
```

## Module Communication

### Via Exports/Imports

```typescript
// OrdersModule needs UsersService
@Module({
  imports: [UsersModule], // Import the module
  controllers: [OrdersController],
  providers: [OrdersService],
})
export class OrdersModule {}

// In OrdersService
@Injectable()
export class OrdersService {
  constructor(private usersService: UsersService) {} // Inject exported service
}
```

### Via Events (Decoupled)

```typescript
// Event-based communication
import { EventEmitter2 } from '@nestjs/event-emitter';

@Injectable()
export class OrdersService {
  constructor(private eventEmitter: EventEmitter2) {}

  async createOrder(dto: CreateOrderDto) {
    const order = await this.ordersRepository.save(dto);

    // Emit event - other modules can listen
    this.eventEmitter.emit('order.created', new OrderCreatedEvent(order));

    return order;
  }
}

// In NotificationsModule
@Injectable()
export class NotificationsListener {
  @OnEvent('order.created')
  handleOrderCreated(event: OrderCreatedEvent) {
    // Send notification
  }
}
```

### Handling Circular Dependencies

```typescript
// When A needs B and B needs A
// Use forwardRef()

// users.module.ts
@Module({
  imports: [forwardRef(() => OrdersModule)],
  providers: [UsersService],
  exports: [UsersService],
})
export class UsersModule {}

// orders.module.ts
@Module({
  imports: [forwardRef(() => UsersModule)],
  providers: [OrdersService],
  exports: [OrdersService],
})
export class OrdersModule {}

// In service
@Injectable()
export class OrdersService {
  constructor(
    @Inject(forwardRef(() => UsersService))
    private usersService: UsersService,
  ) {}
}
```

## Best Practices

### DO

1. **Single Responsibility**: Each module handles one feature/domain
2. **Explicit Dependencies**: Import only what you need
3. **Export Carefully**: Only export what other modules need
4. **Use Lazy Loading**: For large modules that aren't always needed

```typescript
// Lazy loading example
@Module({
  imports: [
    RouterModule.register([
      {
        path: 'admin',
        module: AdminModule,
      },
    ]),
  ],
})
export class AppModule {}
```

5. **Group Related Features**: Keep related functionality together

### DON'T

1. **God Module**: One module with everything
2. **Over-Exporting**: Exposing internal implementation
3. **Deep Nesting**: Modules importing modules importing modules
4. **Skipping Module Boundaries**: Direct file imports across modules
5. **Circular Dependencies**: Use events or restructure instead

## Module Checklist

### Before Creating Module
- [ ] Does this feature deserve its own module?
- [ ] What are the dependencies?
- [ ] What needs to be exported?
- [ ] Can it be a dynamic module for flexibility?

### After Creating Module
- [ ] Module registered in parent/app module?
- [ ] No circular dependencies?
- [ ] Tests in place?
- [ ] Documentation updated?
- [ ] Exports minimal and intentional?

## Example: Complete Feature Module

```typescript
// src/modules/products/products.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { CacheModule } from '@nestjs/cache-manager';

// Controllers
import { ProductsController } from './controllers/products.controller';
import { ProductCategoriesController } from './controllers/product-categories.controller';

// Services
import { ProductsService } from './services/products.service';
import { ProductCategoriesService } from './services/product-categories.service';
import { ProductSearchService } from './services/product-search.service';

// Repositories
import { ProductsRepository } from './repositories/products.repository';
import { ProductCategoriesRepository } from './repositories/product-categories.repository';

// Entities
import { Product } from './entities/product.entity';
import { ProductCategory } from './entities/product-category.entity';
import { ProductImage } from './entities/product-image.entity';

// Event handlers
import { ProductEventHandler } from './events/product-event.handler';

@Module({
  imports: [
    TypeOrmModule.forFeature([Product, ProductCategory, ProductImage]),
    CacheModule.register({
      ttl: 300, // 5 minutes cache
    }),
  ],
  controllers: [
    ProductsController,
    ProductCategoriesController,
  ],
  providers: [
    // Services
    ProductsService,
    ProductCategoriesService,
    ProductSearchService,

    // Repositories
    ProductsRepository,
    ProductCategoriesRepository,

    // Event handlers
    ProductEventHandler,
  ],
  exports: [
    ProductsService,
    ProductCategoriesService,
  ],
})
export class ProductsModule {}
```
