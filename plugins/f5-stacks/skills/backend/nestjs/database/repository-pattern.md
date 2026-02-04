---
name: nestjs-repository-pattern
description: Repository pattern implementation in NestJS
applies_to: nestjs
category: database
---

# Repository Pattern in NestJS

## Overview

The Repository pattern abstracts data access logic, providing a clean separation
between domain logic and data access. It enables easier testing and flexibility
to change data sources.

## When to Use

- Complex domain logic requiring clean separation
- Multiple data sources (SQL, NoSQL, APIs)
- Need for comprehensive unit testing
- Clean Architecture or DDD projects

## Generic Repository Interface

```typescript
// common/repositories/repository.interface.ts
export interface IRepository<T, ID = string> {
  findById(id: ID): Promise<T | null>;
  findAll(): Promise<T[]>;
  findMany(options?: FindManyOptions<T>): Promise<PaginatedResult<T>>;
  create(data: CreateData<T>): Promise<T>;
  update(id: ID, data: UpdateData<T>): Promise<T>;
  delete(id: ID): Promise<void>;
  exists(id: ID): Promise<boolean>;
}

export interface FindManyOptions<T> {
  where?: Partial<T>;
  orderBy?: { [K in keyof T]?: 'ASC' | 'DESC' };
  page?: number;
  limit?: number;
  relations?: string[];
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export type CreateData<T> = Omit<T, 'id' | 'createdAt' | 'updatedAt'>;
export type UpdateData<T> = Partial<CreateData<T>>;
```

## Base Repository Implementation (TypeORM)

```typescript
// common/repositories/base.repository.ts
import { Repository, DeepPartial, FindOptionsWhere } from 'typeorm';
import { IRepository, FindManyOptions, PaginatedResult } from './repository.interface';

export abstract class BaseRepository<T extends { id: string }> implements IRepository<T> {
  constructor(protected readonly repo: Repository<T>) {}

  async findById(id: string): Promise<T | null> {
    return this.repo.findOne({
      where: { id } as FindOptionsWhere<T>,
    });
  }

  async findAll(): Promise<T[]> {
    return this.repo.find();
  }

  async findMany(options: FindManyOptions<T> = {}): Promise<PaginatedResult<T>> {
    const { page = 1, limit = 10, where, orderBy, relations } = options;

    const [items, total] = await this.repo.findAndCount({
      where: where as FindOptionsWhere<T>,
      order: orderBy as any,
      relations,
      skip: (page - 1) * limit,
      take: limit,
    });

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
      hasNext: page < Math.ceil(total / limit),
      hasPrevious: page > 1,
    };
  }

  async create(data: DeepPartial<T>): Promise<T> {
    const entity = this.repo.create(data);
    return this.repo.save(entity);
  }

  async update(id: string, data: DeepPartial<T>): Promise<T> {
    await this.repo.update(id, data as any);
    const updated = await this.findById(id);
    if (!updated) {
      throw new Error(`Entity with id ${id} not found`);
    }
    return updated;
  }

  async delete(id: string): Promise<void> {
    await this.repo.softDelete(id);
  }

  async hardDelete(id: string): Promise<void> {
    await this.repo.delete(id);
  }

  async exists(id: string): Promise<boolean> {
    const count = await this.repo.count({
      where: { id } as FindOptionsWhere<T>,
    });
    return count > 0;
  }

  async count(where?: Partial<T>): Promise<number> {
    return this.repo.count({
      where: where as FindOptionsWhere<T>,
    });
  }
}
```

## Domain-Specific Repository

```typescript
// modules/orders/repositories/orders.repository.interface.ts
import { Order, OrderStatus } from '../entities/order.entity';
import { IRepository, PaginatedResult } from '../../../common/repositories/repository.interface';

export interface OrderFilters {
  customerId?: string;
  status?: OrderStatus;
  dateFrom?: Date;
  dateTo?: Date;
  minAmount?: number;
  maxAmount?: number;
}

export interface IOrdersRepository extends IRepository<Order> {
  findByOrderNumber(orderNumber: string): Promise<Order | null>;
  findByCustomer(customerId: string, page: number, limit: number): Promise<PaginatedResult<Order>>;
  findWithFilters(filters: OrderFilters, page: number, limit: number): Promise<PaginatedResult<Order>>;
  getCustomerStats(customerId: string): Promise<CustomerOrderStats>;
  getRevenueByPeriod(from: Date, to: Date): Promise<number>;
}

export interface CustomerOrderStats {
  totalOrders: number;
  totalSpent: number;
  averageOrderValue: number;
  lastOrderDate: Date | null;
}

export const ORDERS_REPOSITORY = Symbol('IOrdersRepository');

// modules/orders/repositories/orders.repository.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Between, MoreThanOrEqual, LessThanOrEqual } from 'typeorm';
import { BaseRepository } from '../../../common/repositories/base.repository';
import { Order, OrderStatus } from '../entities/order.entity';
import {
  IOrdersRepository,
  OrderFilters,
  CustomerOrderStats,
} from './orders.repository.interface';
import { PaginatedResult } from '../../../common/repositories/repository.interface';

@Injectable()
export class OrdersRepository
  extends BaseRepository<Order>
  implements IOrdersRepository
{
  constructor(
    @InjectRepository(Order)
    repo: Repository<Order>,
  ) {
    super(repo);
  }

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
    page: number,
    limit: number,
  ): Promise<PaginatedResult<Order>> {
    const [items, total] = await this.repo.findAndCount({
      where: { customerId },
      relations: ['items'],
      order: { createdAt: 'DESC' },
      skip: (page - 1) * limit,
      take: limit,
    });

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
      hasNext: page < Math.ceil(total / limit),
      hasPrevious: page > 1,
    };
  }

  async findWithFilters(
    filters: OrderFilters,
    page: number,
    limit: number,
  ): Promise<PaginatedResult<Order>> {
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

    const [items, total] = await qb
      .orderBy('order.createdAt', 'DESC')
      .skip((page - 1) * limit)
      .take(limit)
      .getManyAndCount();

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
      hasNext: page < Math.ceil(total / limit),
      hasPrevious: page > 1,
    };
  }

  async getCustomerStats(customerId: string): Promise<CustomerOrderStats> {
    const result = await this.repo
      .createQueryBuilder('order')
      .select('COUNT(*)', 'totalOrders')
      .addSelect('COALESCE(SUM(order.totalAmount), 0)', 'totalSpent')
      .addSelect('COALESCE(AVG(order.totalAmount), 0)', 'averageOrderValue')
      .addSelect('MAX(order.createdAt)', 'lastOrderDate')
      .where('order.customerId = :customerId', { customerId })
      .andWhere('order.status != :cancelled', { cancelled: OrderStatus.CANCELLED })
      .getRawOne();

    return {
      totalOrders: parseInt(result.totalOrders) || 0,
      totalSpent: parseFloat(result.totalSpent) || 0,
      averageOrderValue: parseFloat(result.averageOrderValue) || 0,
      lastOrderDate: result.lastOrderDate ? new Date(result.lastOrderDate) : null,
    };
  }

  async getRevenueByPeriod(from: Date, to: Date): Promise<number> {
    const result = await this.repo
      .createQueryBuilder('order')
      .select('COALESCE(SUM(order.totalAmount), 0)', 'revenue')
      .where('order.createdAt BETWEEN :from AND :to', { from, to })
      .andWhere('order.status NOT IN (:...excluded)', {
        excluded: [OrderStatus.CANCELLED, OrderStatus.PENDING],
      })
      .getRawOne();

    return parseFloat(result.revenue) || 0;
  }
}
```

## Module Configuration

```typescript
// modules/orders/orders.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Order } from './entities/order.entity';
import { OrderItem } from './entities/order-item.entity';
import { OrdersRepository } from './repositories/orders.repository';
import { ORDERS_REPOSITORY } from './repositories/orders.repository.interface';
import { OrdersService } from './orders.service';
import { OrdersController } from './orders.controller';

@Module({
  imports: [TypeOrmModule.forFeature([Order, OrderItem])],
  controllers: [OrdersController],
  providers: [
    OrdersService,
    {
      provide: ORDERS_REPOSITORY,
      useClass: OrdersRepository,
    },
  ],
  exports: [ORDERS_REPOSITORY],
})
export class OrdersModule {}
```

## Service Using Repository

```typescript
// modules/orders/orders.service.ts
import { Injectable, Inject, NotFoundException } from '@nestjs/common';
import {
  IOrdersRepository,
  ORDERS_REPOSITORY,
  OrderFilters,
} from './repositories/orders.repository.interface';
import { CreateOrderDto } from './dto/create-order.dto';
import { UpdateOrderDto } from './dto/update-order.dto';
import { Order } from './entities/order.entity';
import { PaginatedResult } from '../../common/repositories/repository.interface';

@Injectable()
export class OrdersService {
  constructor(
    @Inject(ORDERS_REPOSITORY)
    private readonly ordersRepository: IOrdersRepository,
  ) {}

  async create(dto: CreateOrderDto): Promise<Order> {
    return this.ordersRepository.create({
      customerId: dto.customerId,
      shippingAddress: dto.shippingAddress,
      items: dto.items,
    });
  }

  async findById(id: string): Promise<Order> {
    const order = await this.ordersRepository.findById(id);
    if (!order) {
      throw new NotFoundException(`Order ${id} not found`);
    }
    return order;
  }

  async findByOrderNumber(orderNumber: string): Promise<Order> {
    const order = await this.ordersRepository.findByOrderNumber(orderNumber);
    if (!order) {
      throw new NotFoundException(`Order ${orderNumber} not found`);
    }
    return order;
  }

  async findWithFilters(
    filters: OrderFilters,
    page: number,
    limit: number,
  ): Promise<PaginatedResult<Order>> {
    return this.ordersRepository.findWithFilters(filters, page, limit);
  }

  async update(id: string, dto: UpdateOrderDto): Promise<Order> {
    await this.findById(id); // Ensure exists
    return this.ordersRepository.update(id, dto);
  }

  async delete(id: string): Promise<void> {
    await this.findById(id); // Ensure exists
    await this.ordersRepository.delete(id);
  }

  async getCustomerStats(customerId: string) {
    return this.ordersRepository.getCustomerStats(customerId);
  }
}
```

## Testing with Mock Repository

```typescript
// modules/orders/__tests__/orders.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { OrdersService } from '../orders.service';
import {
  IOrdersRepository,
  ORDERS_REPOSITORY,
} from '../repositories/orders.repository.interface';
import { Order, OrderStatus } from '../entities/order.entity';

describe('OrdersService', () => {
  let service: OrdersService;
  let repository: jest.Mocked<IOrdersRepository>;

  const mockOrder: Order = {
    id: 'order-1',
    orderNumber: 'ORD-001',
    customerId: 'customer-1',
    status: OrderStatus.PENDING,
    totalAmount: 100,
    items: [],
    createdAt: new Date(),
    updatedAt: new Date(),
  } as Order;

  beforeEach(async () => {
    const mockRepository: Partial<jest.Mocked<IOrdersRepository>> = {
      findById: jest.fn(),
      findByOrderNumber: jest.fn(),
      findWithFilters: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
      getCustomerStats: jest.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        OrdersService,
        {
          provide: ORDERS_REPOSITORY,
          useValue: mockRepository,
        },
      ],
    }).compile();

    service = module.get<OrdersService>(OrdersService);
    repository = module.get(ORDERS_REPOSITORY);
  });

  describe('findById', () => {
    it('should return order when found', async () => {
      repository.findById.mockResolvedValue(mockOrder);

      const result = await service.findById('order-1');

      expect(result).toEqual(mockOrder);
      expect(repository.findById).toHaveBeenCalledWith('order-1');
    });

    it('should throw NotFoundException when not found', async () => {
      repository.findById.mockResolvedValue(null);

      await expect(service.findById('order-1')).rejects.toThrow(
        'Order order-1 not found',
      );
    });
  });

  describe('create', () => {
    it('should create and return order', async () => {
      const createDto = {
        customerId: 'customer-1',
        items: [],
        shippingAddress: { street: '123 Main St', city: 'NYC' },
      };

      repository.create.mockResolvedValue(mockOrder);

      const result = await service.create(createDto);

      expect(result).toEqual(mockOrder);
      expect(repository.create).toHaveBeenCalled();
    });
  });
});
```

## Benefits

1. **Testability**: Easy to mock for unit tests
2. **Flexibility**: Can swap implementations (TypeORM → Prisma)
3. **Single Responsibility**: Data access logic isolated
4. **Domain Focus**: Services focus on business logic
5. **Type Safety**: Strong typing with interfaces

## Checklist

- [ ] Generic repository interface defined
- [ ] Base repository with common operations
- [ ] Domain-specific repository interfaces
- [ ] Repository implementations registered in module
- [ ] Services inject repository via interface
- [ ] Unit tests with mocked repositories
