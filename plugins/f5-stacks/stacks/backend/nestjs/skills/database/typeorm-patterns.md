---
name: nestjs-typeorm-patterns
description: TypeORM patterns and best practices in NestJS
applies_to: nestjs
category: database
---

# TypeORM Patterns in NestJS

## Setup

```bash
npm install @nestjs/typeorm typeorm pg
```

```typescript
// app.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule, ConfigService } from '@nestjs/config';

@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        host: config.get('DB_HOST'),
        port: config.get('DB_PORT'),
        username: config.get('DB_USERNAME'),
        password: config.get('DB_PASSWORD'),
        database: config.get('DB_DATABASE'),
        entities: [__dirname + '/**/*.entity{.ts,.js}'],
        synchronize: false, // Use migrations in production
        logging: config.get('NODE_ENV') === 'development',
        ssl: config.get('DB_SSL') === 'true' ? { rejectUnauthorized: false } : false,
      }),
    }),
  ],
})
export class AppModule {}
```

## Entity Patterns

### Base Entity

```typescript
// common/entities/base.entity.ts
import {
  PrimaryGeneratedColumn,
  CreateDateColumn,
  UpdateDateColumn,
  DeleteDateColumn,
  BaseEntity as TypeOrmBaseEntity,
} from 'typeorm';

export abstract class BaseEntity extends TypeOrmBaseEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  @DeleteDateColumn({ name: 'deleted_at' })
  deletedAt?: Date;
}
```

### Entity with Relations

```typescript
// modules/orders/entities/order.entity.ts
import {
  Entity,
  Column,
  ManyToOne,
  OneToMany,
  JoinColumn,
  Index,
  BeforeInsert,
} from 'typeorm';
import { BaseEntity } from '../../../common/entities/base.entity';
import { Customer } from '../../customers/entities/customer.entity';
import { OrderItem } from './order-item.entity';
import { nanoid } from 'nanoid';

export enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  PAID = 'paid',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
}

@Entity('orders')
@Index(['customerId', 'status'])
@Index(['orderNumber'], { unique: true })
export class Order extends BaseEntity {
  @Column({ name: 'order_number', unique: true })
  orderNumber: string;

  @Column({ type: 'decimal', precision: 12, scale: 2 })
  totalAmount: number;

  @Column({ type: 'enum', enum: OrderStatus, default: OrderStatus.PENDING })
  status: OrderStatus;

  @Column({ type: 'text', nullable: true })
  notes?: string;

  // Many-to-One
  @ManyToOne(() => Customer, (customer) => customer.orders, {
    onDelete: 'RESTRICT',
  })
  @JoinColumn({ name: 'customer_id' })
  customer: Customer;

  @Column({ name: 'customer_id' })
  @Index()
  customerId: string;

  // One-to-Many with cascade
  @OneToMany(() => OrderItem, (item) => item.order, {
    cascade: true,
    eager: false,
  })
  items: OrderItem[];

  // Embedded entity
  @Column(() => ShippingAddress, { prefix: 'shipping_' })
  shippingAddress: ShippingAddress;

  // JSON column
  @Column({ type: 'jsonb', nullable: true })
  metadata?: Record<string, any>;

  @BeforeInsert()
  generateOrderNumber() {
    this.orderNumber = `ORD-${Date.now()}-${nanoid(6).toUpperCase()}`;
  }
}

// Embedded entity (no table, stored in parent)
import { Column } from 'typeorm';

export class ShippingAddress {
  @Column()
  street: string;

  @Column()
  city: string;

  @Column({ name: 'postal_code' })
  postalCode: string;

  @Column()
  country: string;
}

// modules/orders/entities/order-item.entity.ts
@Entity('order_items')
export class OrderItem extends BaseEntity {
  @ManyToOne(() => Order, (order) => order.items, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'order_id' })
  order: Order;

  @Column({ name: 'order_id' })
  orderId: string;

  @ManyToOne(() => Product)
  @JoinColumn({ name: 'product_id' })
  product: Product;

  @Column({ name: 'product_id' })
  productId: string;

  @Column()
  quantity: number;

  @Column({ type: 'decimal', precision: 10, scale: 2, name: 'unit_price' })
  unitPrice: number;

  @Column({ type: 'decimal', precision: 10, scale: 2, name: 'total_price' })
  totalPrice: number;

  @BeforeInsert()
  calculateTotal() {
    this.totalPrice = this.quantity * this.unitPrice;
  }
}
```

### Many-to-Many Relationship

```typescript
// products/entities/product.entity.ts
@Entity('products')
export class Product extends BaseEntity {
  @Column()
  name: string;

  @ManyToMany(() => Category, (category) => category.products)
  @JoinTable({
    name: 'product_categories',
    joinColumn: { name: 'product_id' },
    inverseJoinColumn: { name: 'category_id' },
  })
  categories: Category[];
}

// categories/entities/category.entity.ts
@Entity('categories')
export class Category extends BaseEntity {
  @Column()
  name: string;

  @ManyToMany(() => Product, (product) => product.categories)
  products: Product[];
}
```

## Repository Pattern

### Custom Repository

```typescript
// modules/orders/repositories/orders.repository.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, SelectQueryBuilder } from 'typeorm';
import { Order, OrderStatus } from '../entities/order.entity';

export interface OrderFilters {
  customerId?: string;
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
  sortOrder?: 'ASC' | 'DESC';
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

@Injectable()
export class OrdersRepository {
  constructor(
    @InjectRepository(Order)
    private readonly repo: Repository<Order>,
  ) {}

  async findById(id: string): Promise<Order | null> {
    return this.repo.findOne({
      where: { id },
      relations: ['items', 'items.product', 'customer'],
    });
  }

  async findByOrderNumber(orderNumber: string): Promise<Order | null> {
    return this.repo.findOne({
      where: { orderNumber },
      relations: ['items', 'customer'],
    });
  }

  async findByCustomer(
    customerId: string,
    pagination: PaginationOptions,
  ): Promise<PaginatedResult<Order>> {
    const { page, limit, sortBy = 'createdAt', sortOrder = 'DESC' } = pagination;

    const [items, total] = await this.repo.findAndCount({
      where: { customerId },
      relations: ['items'],
      order: { [sortBy]: sortOrder },
      skip: (page - 1) * limit,
      take: limit,
    });

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async findWithFilters(
    filters: OrderFilters,
    pagination: PaginationOptions,
  ): Promise<PaginatedResult<Order>> {
    const qb = this.createFilteredQueryBuilder(filters);

    // Pagination
    const { page, limit, sortBy = 'createdAt', sortOrder = 'DESC' } = pagination;
    qb.orderBy(`order.${sortBy}`, sortOrder)
      .skip((page - 1) * limit)
      .take(limit);

    const [items, total] = await qb.getManyAndCount();

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  private createFilteredQueryBuilder(
    filters: OrderFilters,
  ): SelectQueryBuilder<Order> {
    const qb = this.repo
      .createQueryBuilder('order')
      .leftJoinAndSelect('order.items', 'items')
      .leftJoinAndSelect('order.customer', 'customer');

    if (filters.customerId) {
      qb.andWhere('order.customerId = :customerId', {
        customerId: filters.customerId,
      });
    }

    if (filters.status) {
      qb.andWhere('order.status = :status', { status: filters.status });
    }

    if (filters.dateFrom) {
      qb.andWhere('order.createdAt >= :dateFrom', { dateFrom: filters.dateFrom });
    }

    if (filters.dateTo) {
      qb.andWhere('order.createdAt <= :dateTo', { dateTo: filters.dateTo });
    }

    if (filters.minAmount) {
      qb.andWhere('order.totalAmount >= :minAmount', {
        minAmount: filters.minAmount,
      });
    }

    if (filters.maxAmount) {
      qb.andWhere('order.totalAmount <= :maxAmount', {
        maxAmount: filters.maxAmount,
      });
    }

    if (filters.search) {
      qb.andWhere(
        '(order.orderNumber ILIKE :search OR customer.name ILIKE :search)',
        { search: `%${filters.search}%` },
      );
    }

    return qb;
  }

  async save(order: Order): Promise<Order> {
    return this.repo.save(order);
  }

  async saveMany(orders: Order[]): Promise<Order[]> {
    return this.repo.save(orders);
  }

  async softDelete(id: string): Promise<void> {
    await this.repo.softDelete(id);
  }

  async restore(id: string): Promise<void> {
    await this.repo.restore(id);
  }

  async hardDelete(id: string): Promise<void> {
    await this.repo.delete(id);
  }

  // Aggregate queries
  async getTotalsByStatus(): Promise<{ status: string; count: number; total: number }[]> {
    return this.repo
      .createQueryBuilder('order')
      .select('order.status', 'status')
      .addSelect('COUNT(*)', 'count')
      .addSelect('SUM(order.totalAmount)', 'total')
      .groupBy('order.status')
      .getRawMany();
  }

  async getCustomerOrderStats(customerId: string): Promise<{
    totalOrders: number;
    totalSpent: number;
    averageOrderValue: number;
  }> {
    const result = await this.repo
      .createQueryBuilder('order')
      .select('COUNT(*)', 'totalOrders')
      .addSelect('SUM(order.totalAmount)', 'totalSpent')
      .addSelect('AVG(order.totalAmount)', 'averageOrderValue')
      .where('order.customerId = :customerId', { customerId })
      .andWhere('order.status != :cancelled', { cancelled: OrderStatus.CANCELLED })
      .getRawOne();

    return {
      totalOrders: parseInt(result.totalOrders) || 0,
      totalSpent: parseFloat(result.totalSpent) || 0,
      averageOrderValue: parseFloat(result.averageOrderValue) || 0,
    };
  }
}
```

## Transaction Patterns

### Using QueryRunner

```typescript
@Injectable()
export class OrdersService {
  constructor(
    private readonly dataSource: DataSource,
    private readonly ordersRepository: OrdersRepository,
  ) {}

  async createOrderWithPayment(dto: CreateOrderDto): Promise<Order> {
    const queryRunner = this.dataSource.createQueryRunner();
    await queryRunner.connect();
    await queryRunner.startTransaction();

    try {
      // Create order
      const order = queryRunner.manager.create(Order, {
        customerId: dto.customerId,
        shippingAddress: dto.shippingAddress,
        items: dto.items.map(item =>
          queryRunner.manager.create(OrderItem, {
            productId: item.productId,
            quantity: item.quantity,
            unitPrice: item.unitPrice,
          }),
        ),
      });

      // Calculate total
      order.totalAmount = order.items.reduce(
        (sum, item) => sum + item.quantity * item.unitPrice,
        0,
      );

      await queryRunner.manager.save(order);

      // Create payment record
      const payment = queryRunner.manager.create(Payment, {
        orderId: order.id,
        amount: order.totalAmount,
        status: PaymentStatus.PENDING,
      });
      await queryRunner.manager.save(payment);

      // Update inventory
      for (const item of dto.items) {
        await queryRunner.manager.decrement(
          Product,
          { id: item.productId },
          'stock',
          item.quantity,
        );
      }

      await queryRunner.commitTransaction();
      return order;
    } catch (error) {
      await queryRunner.rollbackTransaction();
      throw error;
    } finally {
      await queryRunner.release();
    }
  }
}
```

### Using DataSource.transaction

```typescript
async transferMoney(
  fromAccountId: string,
  toAccountId: string,
  amount: number,
): Promise<void> {
  await this.dataSource.transaction(async (manager) => {
    // Debit from account
    await manager.decrement(Account, { id: fromAccountId }, 'balance', amount);

    // Credit to account
    await manager.increment(Account, { id: toAccountId }, 'balance', amount);

    // Create transaction records
    await manager.save(Transaction, [
      { accountId: fromAccountId, amount: -amount, type: 'debit' },
      { accountId: toAccountId, amount: amount, type: 'credit' },
    ]);
  });
}
```

## Query Optimization

### Select Specific Fields

```typescript
// Only select needed fields
const orders = await this.repo
  .createQueryBuilder('order')
  .select(['order.id', 'order.orderNumber', 'order.status', 'order.totalAmount'])
  .where('order.customerId = :customerId', { customerId })
  .getMany();

// Raw query for complex aggregations
const stats = await this.repo.query(`
  SELECT
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as order_count,
    SUM(total_amount) as revenue
  FROM orders
  WHERE created_at >= $1
  GROUP BY DATE_TRUNC('month', created_at)
  ORDER BY month DESC
`, [startDate]);
```

### Eager vs Lazy Loading

```typescript
// Eager - always load relation (use sparingly)
@OneToMany(() => OrderItem, (item) => item.order, { eager: true })
items: OrderItem[];

// Lazy - load on access (requires active connection)
@OneToMany(() => OrderItem, (item) => item.order)
items: Promise<OrderItem[]>;

// Explicit loading - recommended
const order = await this.repo.findOne({
  where: { id },
  relations: ['items', 'customer'], // Specify what to load
});
```

### Using QueryBuilder for Complex Queries

```typescript
// Subquery example
const subQuery = this.repo
  .createQueryBuilder('order')
  .select('order.customerId')
  .where('order.status = :status', { status: OrderStatus.CANCELLED })
  .groupBy('order.customerId')
  .having('COUNT(*) > 3');

const problematicCustomers = await this.customerRepo
  .createQueryBuilder('customer')
  .where(`customer.id IN (${subQuery.getQuery()})`)
  .setParameters(subQuery.getParameters())
  .getMany();
```

## Migrations

### Generate Migration

```bash
# Generate migration from entity changes
npm run typeorm migration:generate -- -n CreateOrdersTable

# Create empty migration
npm run typeorm migration:create -- -n AddIndexToOrders
```

### Migration Example

```typescript
// migrations/1234567890-CreateOrdersTable.ts
import { MigrationInterface, QueryRunner, Table, TableForeignKey, TableIndex } from 'typeorm';

export class CreateOrdersTable1234567890 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Create enum type
    await queryRunner.query(`
      CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'paid', 'shipped', 'delivered', 'cancelled')
    `);

    // Create table
    await queryRunner.createTable(
      new Table({
        name: 'orders',
        columns: [
          {
            name: 'id',
            type: 'uuid',
            isPrimary: true,
            default: 'uuid_generate_v4()',
          },
          {
            name: 'order_number',
            type: 'varchar',
            isUnique: true,
          },
          {
            name: 'customer_id',
            type: 'uuid',
          },
          {
            name: 'total_amount',
            type: 'decimal',
            precision: 12,
            scale: 2,
          },
          {
            name: 'status',
            type: 'order_status',
            default: "'pending'",
          },
          {
            name: 'shipping_street',
            type: 'varchar',
          },
          {
            name: 'shipping_city',
            type: 'varchar',
          },
          {
            name: 'shipping_postal_code',
            type: 'varchar',
          },
          {
            name: 'shipping_country',
            type: 'varchar',
          },
          {
            name: 'metadata',
            type: 'jsonb',
            isNullable: true,
          },
          {
            name: 'created_at',
            type: 'timestamp',
            default: 'CURRENT_TIMESTAMP',
          },
          {
            name: 'updated_at',
            type: 'timestamp',
            default: 'CURRENT_TIMESTAMP',
          },
          {
            name: 'deleted_at',
            type: 'timestamp',
            isNullable: true,
          },
        ],
      }),
    );

    // Add foreign key
    await queryRunner.createForeignKey(
      'orders',
      new TableForeignKey({
        columnNames: ['customer_id'],
        referencedTableName: 'customers',
        referencedColumnNames: ['id'],
        onDelete: 'RESTRICT',
      }),
    );

    // Add indexes
    await queryRunner.createIndex(
      'orders',
      new TableIndex({
        name: 'IDX_orders_customer_status',
        columnNames: ['customer_id', 'status'],
      }),
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('orders');
    await queryRunner.query('DROP TYPE order_status');
  }
}
```

### Run Migrations

```bash
# Run pending migrations
npm run typeorm migration:run

# Revert last migration
npm run typeorm migration:revert

# Show migration status
npm run typeorm migration:show
```

## Best Practices

1. **Use migrations** in production, never synchronize
2. **Index frequently queried columns**
3. **Soft delete** for audit trail
4. **Use transactions** for multiple operations
5. **Avoid N+1** with eager loading or joins
6. **Use QueryBuilder** for complex queries
7. **Keep entities simple** - avoid business logic

## Checklist

- [ ] Base entity with common fields
- [ ] Proper column types and constraints
- [ ] Relations defined correctly
- [ ] Indexes on query columns
- [ ] Migrations for schema changes
- [ ] Repository pattern for data access
- [ ] Transactions for multi-step operations
- [ ] Soft delete where needed
