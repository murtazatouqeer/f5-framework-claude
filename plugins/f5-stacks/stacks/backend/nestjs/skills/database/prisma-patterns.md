---
name: nestjs-prisma-patterns
description: Prisma ORM patterns and best practices in NestJS
applies_to: nestjs
category: database
---

# Prisma Patterns in NestJS

## Setup

```bash
npm install @prisma/client
npm install -D prisma

# Initialize Prisma
npx prisma init
```

## Prisma Service

```typescript
// prisma/prisma.service.ts
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  constructor() {
    super({
      log: process.env.NODE_ENV === 'development'
        ? ['query', 'info', 'warn', 'error']
        : ['error'],
    });
  }

  async onModuleInit() {
    await this.$connect();
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }

  // Middleware for soft delete
  async enableSoftDelete() {
    this.$use(async (params, next) => {
      if (params.model === 'User' || params.model === 'Order') {
        if (params.action === 'delete') {
          params.action = 'update';
          params.args['data'] = { deletedAt: new Date() };
        }
        if (params.action === 'deleteMany') {
          params.action = 'updateMany';
          if (params.args.data !== undefined) {
            params.args.data['deletedAt'] = new Date();
          } else {
            params.args['data'] = { deletedAt: new Date() };
          }
        }
        // Filter out soft-deleted records
        if (params.action === 'findUnique' || params.action === 'findFirst') {
          params.action = 'findFirst';
          params.args.where['deletedAt'] = null;
        }
        if (params.action === 'findMany') {
          if (!params.args) params.args = {};
          if (!params.args.where) params.args.where = {};
          params.args.where['deletedAt'] = null;
        }
      }
      return next(params);
    });
  }

  // Clean database for testing
  async cleanDatabase() {
    if (process.env.NODE_ENV !== 'test') {
      throw new Error('cleanDatabase can only be called in test environment');
    }

    const tablenames = await this.$queryRaw<
      Array<{ tablename: string }>
    >`SELECT tablename FROM pg_tables WHERE schemaname='public'`;

    const tables = tablenames
      .map(({ tablename }) => tablename)
      .filter((name) => name !== '_prisma_migrations')
      .map((name) => `"public"."${name}"`)
      .join(', ');

    try {
      await this.$executeRawUnsafe(`TRUNCATE TABLE ${tables} CASCADE;`);
    } catch (error) {
      console.log({ error });
    }
  }
}

// prisma/prisma.module.ts
import { Global, Module } from '@nestjs/common';
import { PrismaService } from './prisma.service';

@Global()
@Module({
  providers: [PrismaService],
  exports: [PrismaService],
})
export class PrismaModule {}
```

## Prisma Schema

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
  previewFeatures = ["fullTextSearch", "fullTextIndex"]
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// Enums
enum OrderStatus {
  PENDING
  CONFIRMED
  PAID
  SHIPPED
  DELIVERED
  CANCELLED
}

enum UserRole {
  USER
  ADMIN
  MODERATOR
}

// Models
model User {
  id            String    @id @default(uuid())
  email         String    @unique
  name          String
  passwordHash  String    @map("password_hash")
  role          UserRole  @default(USER)
  isActive      Boolean   @default(true) @map("is_active")
  createdAt     DateTime  @default(now()) @map("created_at")
  updatedAt     DateTime  @updatedAt @map("updated_at")
  deletedAt     DateTime? @map("deleted_at")

  // Relations
  orders        Order[]
  profile       UserProfile?

  @@map("users")
  @@index([email])
}

model UserProfile {
  id        String   @id @default(uuid())
  userId    String   @unique @map("user_id")
  bio       String?
  avatarUrl String?  @map("avatar_url")
  phone     String?

  user      User     @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@map("user_profiles")
}

model Order {
  id            String      @id @default(uuid())
  orderNumber   String      @unique @map("order_number")
  userId        String      @map("user_id")
  status        OrderStatus @default(PENDING)
  totalAmount   Decimal     @map("total_amount") @db.Decimal(12, 2)
  notes         String?
  shippingAddress Json      @map("shipping_address")
  createdAt     DateTime    @default(now()) @map("created_at")
  updatedAt     DateTime    @updatedAt @map("updated_at")
  deletedAt     DateTime?   @map("deleted_at")

  // Relations
  user          User        @relation(fields: [userId], references: [id])
  items         OrderItem[]

  @@map("orders")
  @@index([userId, status])
  @@index([createdAt])
}

model OrderItem {
  id          String  @id @default(uuid())
  orderId     String  @map("order_id")
  productId   String  @map("product_id")
  quantity    Int
  unitPrice   Decimal @map("unit_price") @db.Decimal(10, 2)
  totalPrice  Decimal @map("total_price") @db.Decimal(10, 2)

  // Relations
  order       Order   @relation(fields: [orderId], references: [id], onDelete: Cascade)
  product     Product @relation(fields: [productId], references: [id])

  @@map("order_items")
}

model Product {
  id          String      @id @default(uuid())
  name        String
  description String?
  price       Decimal     @db.Decimal(10, 2)
  stock       Int         @default(0)
  isActive    Boolean     @default(true) @map("is_active")
  createdAt   DateTime    @default(now()) @map("created_at")
  updatedAt   DateTime    @updatedAt @map("updated_at")

  // Relations
  orderItems  OrderItem[]
  categories  CategoriesOnProducts[]

  @@map("products")
  @@index([name])
}

model Category {
  id        String    @id @default(uuid())
  name      String    @unique
  products  CategoriesOnProducts[]

  @@map("categories")
}

// Many-to-Many join table
model CategoriesOnProducts {
  productId   String   @map("product_id")
  categoryId  String   @map("category_id")
  assignedAt  DateTime @default(now()) @map("assigned_at")

  product     Product  @relation(fields: [productId], references: [id], onDelete: Cascade)
  category    Category @relation(fields: [categoryId], references: [id], onDelete: Cascade)

  @@id([productId, categoryId])
  @@map("product_categories")
}
```

## Repository Pattern with Prisma

```typescript
// modules/orders/repositories/orders.repository.ts
import { Injectable } from '@nestjs/common';
import { Prisma, Order, OrderStatus } from '@prisma/client';
import { PrismaService } from '../../../prisma/prisma.service';

export interface OrderFilters {
  userId?: string;
  status?: OrderStatus;
  dateFrom?: Date;
  dateTo?: Date;
  minAmount?: number;
  maxAmount?: number;
  search?: string;
}

export interface PaginationOptions {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// Type for order with relations
type OrderWithRelations = Prisma.OrderGetPayload<{
  include: { items: { include: { product: true } }; user: true };
}>;

@Injectable()
export class OrdersRepository {
  constructor(private readonly prisma: PrismaService) {}

  async findById(id: string): Promise<OrderWithRelations | null> {
    return this.prisma.order.findUnique({
      where: { id },
      include: {
        items: {
          include: { product: true },
        },
        user: true,
      },
    });
  }

  async findByOrderNumber(orderNumber: string): Promise<OrderWithRelations | null> {
    return this.prisma.order.findUnique({
      where: { orderNumber },
      include: {
        items: { include: { product: true } },
        user: true,
      },
    });
  }

  async findMany(
    filters: OrderFilters,
    pagination: PaginationOptions,
  ): Promise<PaginatedResult<OrderWithRelations>> {
    const { page, limit, sortBy = 'createdAt', sortOrder = 'desc' } = pagination;

    const where = this.buildWhereClause(filters);

    const [items, total] = await Promise.all([
      this.prisma.order.findMany({
        where,
        include: {
          items: { include: { product: true } },
          user: true,
        },
        orderBy: { [sortBy]: sortOrder },
        skip: (page - 1) * limit,
        take: limit,
      }),
      this.prisma.order.count({ where }),
    ]);

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  private buildWhereClause(filters: OrderFilters): Prisma.OrderWhereInput {
    const where: Prisma.OrderWhereInput = {
      deletedAt: null,
    };

    if (filters.userId) {
      where.userId = filters.userId;
    }

    if (filters.status) {
      where.status = filters.status;
    }

    if (filters.dateFrom || filters.dateTo) {
      where.createdAt = {};
      if (filters.dateFrom) {
        where.createdAt.gte = filters.dateFrom;
      }
      if (filters.dateTo) {
        where.createdAt.lte = filters.dateTo;
      }
    }

    if (filters.minAmount || filters.maxAmount) {
      where.totalAmount = {};
      if (filters.minAmount) {
        where.totalAmount.gte = filters.minAmount;
      }
      if (filters.maxAmount) {
        where.totalAmount.lte = filters.maxAmount;
      }
    }

    if (filters.search) {
      where.OR = [
        { orderNumber: { contains: filters.search, mode: 'insensitive' } },
        { user: { name: { contains: filters.search, mode: 'insensitive' } } },
      ];
    }

    return where;
  }

  async create(data: Prisma.OrderCreateInput): Promise<Order> {
    return this.prisma.order.create({
      data,
      include: {
        items: { include: { product: true } },
      },
    });
  }

  async update(id: string, data: Prisma.OrderUpdateInput): Promise<Order> {
    return this.prisma.order.update({
      where: { id },
      data,
      include: {
        items: { include: { product: true } },
      },
    });
  }

  async softDelete(id: string): Promise<void> {
    await this.prisma.order.update({
      where: { id },
      data: { deletedAt: new Date() },
    });
  }

  async hardDelete(id: string): Promise<void> {
    await this.prisma.order.delete({ where: { id } });
  }

  // Aggregate queries
  async getStatsByStatus(): Promise<{ status: OrderStatus; count: number; total: number }[]> {
    const result = await this.prisma.order.groupBy({
      by: ['status'],
      _count: { id: true },
      _sum: { totalAmount: true },
      where: { deletedAt: null },
    });

    return result.map(r => ({
      status: r.status,
      count: r._count.id,
      total: Number(r._sum.totalAmount) || 0,
    }));
  }

  async getUserStats(userId: string): Promise<{
    totalOrders: number;
    totalSpent: number;
    averageOrderValue: number;
  }> {
    const result = await this.prisma.order.aggregate({
      where: {
        userId,
        status: { not: 'CANCELLED' },
        deletedAt: null,
      },
      _count: { id: true },
      _sum: { totalAmount: true },
      _avg: { totalAmount: true },
    });

    return {
      totalOrders: result._count.id || 0,
      totalSpent: Number(result._sum.totalAmount) || 0,
      averageOrderValue: Number(result._avg.totalAmount) || 0,
    };
  }
}
```

## Transaction Patterns

```typescript
// Interactive transaction
async createOrderWithPayment(dto: CreateOrderDto): Promise<Order> {
  return this.prisma.$transaction(async (tx) => {
    // Create order
    const order = await tx.order.create({
      data: {
        orderNumber: generateOrderNumber(),
        userId: dto.userId,
        shippingAddress: dto.shippingAddress,
        totalAmount: 0,
        items: {
          create: dto.items.map(item => ({
            productId: item.productId,
            quantity: item.quantity,
            unitPrice: item.unitPrice,
            totalPrice: item.quantity * item.unitPrice,
          })),
        },
      },
      include: { items: true },
    });

    // Calculate total
    const totalAmount = order.items.reduce(
      (sum, item) => sum + Number(item.totalPrice),
      0,
    );

    // Update order total
    await tx.order.update({
      where: { id: order.id },
      data: { totalAmount },
    });

    // Update inventory
    for (const item of dto.items) {
      await tx.product.update({
        where: { id: item.productId },
        data: { stock: { decrement: item.quantity } },
      });
    }

    // Create payment record
    await tx.payment.create({
      data: {
        orderId: order.id,
        amount: totalAmount,
        status: 'PENDING',
      },
    });

    return order;
  });
}

// Sequential transaction with timeout
async bulkUpdateOrders(updates: { id: string; status: OrderStatus }[]): Promise<void> {
  await this.prisma.$transaction(
    updates.map(update =>
      this.prisma.order.update({
        where: { id: update.id },
        data: { status: update.status },
      }),
    ),
    {
      timeout: 10000, // 10 seconds
      maxWait: 5000,  // 5 seconds
    },
  );
}
```

## Raw Queries

```typescript
// Raw query for complex operations
async getMonthlyRevenue(year: number): Promise<{ month: number; revenue: number }[]> {
  const result = await this.prisma.$queryRaw<{ month: number; revenue: number }[]>`
    SELECT
      EXTRACT(MONTH FROM created_at) as month,
      SUM(total_amount)::float as revenue
    FROM orders
    WHERE
      EXTRACT(YEAR FROM created_at) = ${year}
      AND status NOT IN ('CANCELLED')
      AND deleted_at IS NULL
    GROUP BY EXTRACT(MONTH FROM created_at)
    ORDER BY month
  `;

  return result;
}

// Raw query with parameters
async searchProducts(query: string, limit: number): Promise<Product[]> {
  return this.prisma.$queryRaw<Product[]>`
    SELECT * FROM products
    WHERE
      to_tsvector('english', name || ' ' || COALESCE(description, ''))
      @@ plainto_tsquery('english', ${query})
    LIMIT ${limit}
  `;
}
```

## Migrations

```bash
# Create migration
npx prisma migrate dev --name add_orders_table

# Apply migrations in production
npx prisma migrate deploy

# Reset database (development only)
npx prisma migrate reset

# Generate Prisma Client
npx prisma generate
```

## Best Practices

1. **Use transactions** for multiple related operations
2. **Index frequently queried columns** in schema
3. **Use select** to fetch only needed fields
4. **Implement soft delete** with middleware
5. **Use Prisma Client extensions** for reusable logic
6. **Keep schema organized** with comments

## Checklist

- [ ] PrismaService with lifecycle hooks
- [ ] Global PrismaModule
- [ ] Proper schema with indexes
- [ ] Repository pattern implementation
- [ ] Transaction handling
- [ ] Soft delete middleware
- [ ] Type-safe queries
