# NestJS Database Patterns

Database integration patterns for TypeORM and Prisma.

## Table of Contents

1. [TypeORM Setup](#typeorm-setup)
2. [TypeORM Patterns](#typeorm-patterns)
3. [Prisma Setup](#prisma-setup)
4. [Prisma Patterns](#prisma-patterns)
5. [Migrations](#migrations)
6. [Performance](#performance)

---

## TypeORM Setup

### Installation

```bash
npm install @nestjs/typeorm typeorm pg
```

### Configuration

```typescript
// app.module.ts
@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        host: config.get('DB_HOST'),
        port: config.get('DB_PORT', 5432),
        username: config.get('DB_USERNAME'),
        password: config.get('DB_PASSWORD'),
        database: config.get('DB_NAME'),
        entities: [__dirname + '/**/*.entity{.ts,.js}'],
        synchronize: config.get('NODE_ENV') !== 'production',
        logging: config.get('NODE_ENV') === 'development',
        migrations: [__dirname + '/migrations/*{.ts,.js}'],
      }),
      inject: [ConfigService],
    }),
  ],
})
export class AppModule {}
```

### DataSource Configuration

```typescript
// typeorm.config.ts (for CLI)
import { DataSource } from 'typeorm';
import { config } from 'dotenv';

config();

export default new DataSource({
  type: 'postgres',
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT, 10) || 5432,
  username: process.env.DB_USERNAME,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  entities: ['src/**/*.entity.ts'],
  migrations: ['src/migrations/*.ts'],
});
```

---

## TypeORM Patterns

### Entity with Relations

```typescript
// entities/user.entity.ts
@Entity('users')
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  email: string;

  @Column()
  name: string;

  @Column({ type: 'enum', enum: UserStatus, default: UserStatus.ACTIVE })
  status: UserStatus;

  @OneToMany(() => Order, (order) => order.user)
  orders: Order[];

  @OneToOne(() => Profile, (profile) => profile.user, { cascade: true })
  @JoinColumn()
  profile: Profile;

  @ManyToMany(() => Role, (role) => role.users)
  @JoinTable({ name: 'user_roles' })
  roles: Role[];

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @DeleteDateColumn()
  deletedAt: Date; // Soft delete
}

// entities/order.entity.ts
@Entity('orders')
@Index(['userId', 'status'])
@Index(['createdAt'])
export class Order {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  userId: string;

  @ManyToOne(() => User, (user) => user.orders)
  @JoinColumn({ name: 'userId' })
  user: User;

  @OneToMany(() => OrderItem, (item) => item.order, { cascade: true })
  items: OrderItem[];

  @Column({ type: 'enum', enum: OrderStatus, default: OrderStatus.PENDING })
  status: OrderStatus;

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  total: number;

  @CreateDateColumn()
  createdAt: Date;
}
```

### Repository Pattern

```typescript
// user/user.repository.ts
@Injectable()
export class UserRepository {
  constructor(
    @InjectRepository(User)
    private readonly repo: Repository<User>,
  ) {}

  async findById(id: string): Promise<User | null> {
    return this.repo.findOne({
      where: { id },
      relations: ['profile', 'roles'],
    });
  }

  async findByEmail(email: string): Promise<User | null> {
    return this.repo.findOne({ where: { email } });
  }

  async findWithPagination(
    query: QueryUserDto,
  ): Promise<PaginatedResult<User>> {
    const { page = 1, limit = 10, search, status } = query;
    const skip = (page - 1) * limit;

    const qb = this.repo
      .createQueryBuilder('user')
      .leftJoinAndSelect('user.profile', 'profile');

    if (search) {
      qb.andWhere(
        '(user.name ILIKE :search OR user.email ILIKE :search)',
        { search: `%${search}%` },
      );
    }

    if (status) {
      qb.andWhere('user.status = :status', { status });
    }

    const [data, total] = await qb
      .orderBy('user.createdAt', 'DESC')
      .skip(skip)
      .take(limit)
      .getManyAndCount();

    return {
      data,
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async createWithProfile(dto: CreateUserDto): Promise<User> {
    const user = this.repo.create({
      ...dto,
      profile: { bio: dto.bio },
    });
    return this.repo.save(user);
  }

  async softDelete(id: string): Promise<void> {
    await this.repo.softDelete(id);
  }

  async restore(id: string): Promise<void> {
    await this.repo.restore(id);
  }
}
```

### Transaction Example

```typescript
// order/order.service.ts
@Injectable()
export class OrderService {
  constructor(
    private dataSource: DataSource,
    @InjectRepository(Order)
    private orderRepo: Repository<Order>,
    @InjectRepository(Product)
    private productRepo: Repository<Product>,
  ) {}

  async createOrder(dto: CreateOrderDto): Promise<Order> {
    const queryRunner = this.dataSource.createQueryRunner();
    await queryRunner.connect();
    await queryRunner.startTransaction();

    try {
      // Create order
      const order = queryRunner.manager.create(Order, {
        userId: dto.userId,
        status: OrderStatus.PENDING,
        total: 0,
      });
      await queryRunner.manager.save(order);

      let total = 0;

      // Create order items and update stock
      for (const item of dto.items) {
        const product = await queryRunner.manager.findOne(Product, {
          where: { id: item.productId },
          lock: { mode: 'pessimistic_write' },
        });

        if (!product || product.stock < item.quantity) {
          throw new BadRequestException('Insufficient stock');
        }

        // Update stock
        product.stock -= item.quantity;
        await queryRunner.manager.save(product);

        // Create order item
        const orderItem = queryRunner.manager.create(OrderItem, {
          orderId: order.id,
          productId: item.productId,
          quantity: item.quantity,
          price: product.price,
        });
        await queryRunner.manager.save(orderItem);

        total += Number(product.price) * item.quantity;
      }

      // Update order total
      order.total = total;
      await queryRunner.manager.save(order);

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

### Query Builder Advanced

```typescript
// Advanced query examples
@Injectable()
export class ReportRepository {
  constructor(
    @InjectRepository(Order)
    private readonly repo: Repository<Order>,
  ) {}

  async getOrderSummary(startDate: Date, endDate: Date) {
    return this.repo
      .createQueryBuilder('order')
      .select('DATE(order.createdAt)', 'date')
      .addSelect('COUNT(*)', 'count')
      .addSelect('SUM(order.total)', 'total')
      .where('order.createdAt BETWEEN :startDate AND :endDate', {
        startDate,
        endDate,
      })
      .andWhere('order.status = :status', { status: OrderStatus.COMPLETED })
      .groupBy('DATE(order.createdAt)')
      .orderBy('date', 'DESC')
      .getRawMany();
  }

  async getTopCustomers(limit: number = 10) {
    return this.repo
      .createQueryBuilder('order')
      .select('order.userId', 'userId')
      .addSelect('user.name', 'userName')
      .addSelect('COUNT(*)', 'orderCount')
      .addSelect('SUM(order.total)', 'totalSpent')
      .innerJoin('order.user', 'user')
      .where('order.status = :status', { status: OrderStatus.COMPLETED })
      .groupBy('order.userId')
      .addGroupBy('user.name')
      .orderBy('totalSpent', 'DESC')
      .limit(limit)
      .getRawMany();
  }

  async getProductSales() {
    return this.repo
      .createQueryBuilder('order')
      .innerJoin('order.items', 'item')
      .innerJoin('item.product', 'product')
      .select('product.id', 'productId')
      .addSelect('product.name', 'productName')
      .addSelect('SUM(item.quantity)', 'totalQuantity')
      .addSelect('SUM(item.quantity * item.price)', 'totalRevenue')
      .where('order.status = :status', { status: OrderStatus.COMPLETED })
      .groupBy('product.id')
      .addGroupBy('product.name')
      .orderBy('totalRevenue', 'DESC')
      .getRawMany();
  }
}
```

---

## Prisma Setup

### Installation

```bash
npm install @prisma/client
npm install -D prisma
npx prisma init
```

### Schema

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String     @id @default(uuid())
  email     String     @unique
  name      String
  password  String
  status    UserStatus @default(ACTIVE)
  profile   Profile?
  orders    Order[]
  roles     Role[]     @relation("UserRoles")
  createdAt DateTime   @default(now())
  updatedAt DateTime   @updatedAt
  deletedAt DateTime?

  @@index([email])
  @@map("users")
}

model Profile {
  id     String  @id @default(uuid())
  bio    String?
  avatar String?
  userId String  @unique
  user   User    @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@map("profiles")
}

model Order {
  id        String      @id @default(uuid())
  userId    String
  user      User        @relation(fields: [userId], references: [id])
  items     OrderItem[]
  status    OrderStatus @default(PENDING)
  total     Decimal     @db.Decimal(10, 2)
  createdAt DateTime    @default(now())

  @@index([userId, status])
  @@index([createdAt])
  @@map("orders")
}

model OrderItem {
  id        String  @id @default(uuid())
  orderId   String
  order     Order   @relation(fields: [orderId], references: [id], onDelete: Cascade)
  productId String
  product   Product @relation(fields: [productId], references: [id])
  quantity  Int
  price     Decimal @db.Decimal(10, 2)

  @@map("order_items")
}

model Product {
  id          String      @id @default(uuid())
  name        String
  description String?
  price       Decimal     @db.Decimal(10, 2)
  stock       Int         @default(0)
  orderItems  OrderItem[]
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt

  @@map("products")
}

enum UserStatus {
  ACTIVE
  INACTIVE
  BANNED
}

enum OrderStatus {
  PENDING
  CONFIRMED
  SHIPPED
  DELIVERED
  CANCELLED
}
```

### Prisma Service

```typescript
// prisma/prisma.service.ts
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

  // Soft delete extension
  async enableSoftDelete() {
    this.$use(async (params, next) => {
      // Intercept delete operations
      if (params.action === 'delete') {
        params.action = 'update';
        params.args['data'] = { deletedAt: new Date() };
      }
      if (params.action === 'deleteMany') {
        params.action = 'updateMany';
        params.args['data'] = { deletedAt: new Date() };
      }

      // Filter out soft-deleted records on find
      if (params.action === 'findUnique' || params.action === 'findFirst') {
        params.action = 'findFirst';
        params.args.where = { ...params.args.where, deletedAt: null };
      }
      if (params.action === 'findMany') {
        if (!params.args) params.args = {};
        if (!params.args.where) params.args.where = {};
        params.args.where.deletedAt = null;
      }

      return next(params);
    });
  }
}
```

---

## Prisma Patterns

### Repository with Prisma

```typescript
// user/user.repository.ts
@Injectable()
export class UserRepository {
  constructor(private prisma: PrismaService) {}

  async findById(id: string): Promise<User | null> {
    return this.prisma.user.findUnique({
      where: { id, deletedAt: null },
      include: { profile: true, roles: true },
    });
  }

  async findWithPagination(query: QueryUserDto) {
    const { page = 1, limit = 10, search, status } = query;
    const skip = (page - 1) * limit;

    const where: Prisma.UserWhereInput = {
      deletedAt: null,
      ...(search && {
        OR: [
          { name: { contains: search, mode: 'insensitive' } },
          { email: { contains: search, mode: 'insensitive' } },
        ],
      }),
      ...(status && { status }),
    };

    const [data, total] = await Promise.all([
      this.prisma.user.findMany({
        where,
        include: { profile: true },
        skip,
        take: limit,
        orderBy: { createdAt: 'desc' },
      }),
      this.prisma.user.count({ where }),
    ]);

    return {
      data,
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async createWithProfile(dto: CreateUserDto): Promise<User> {
    return this.prisma.user.create({
      data: {
        email: dto.email,
        name: dto.name,
        password: dto.password,
        profile: {
          create: { bio: dto.bio },
        },
      },
      include: { profile: true },
    });
  }

  async upsert(dto: UpsertUserDto): Promise<User> {
    return this.prisma.user.upsert({
      where: { email: dto.email },
      update: { name: dto.name },
      create: {
        email: dto.email,
        name: dto.name,
        password: dto.password,
      },
    });
  }
}
```

### Transaction with Prisma

```typescript
// order/order.service.ts
@Injectable()
export class OrderService {
  constructor(private prisma: PrismaService) {}

  async createOrder(dto: CreateOrderDto): Promise<Order> {
    return this.prisma.$transaction(async (tx) => {
      // Create order
      const order = await tx.order.create({
        data: {
          userId: dto.userId,
          status: 'PENDING',
          total: 0,
        },
      });

      let total = 0;

      // Process items
      for (const item of dto.items) {
        const product = await tx.product.findUnique({
          where: { id: item.productId },
        });

        if (!product || product.stock < item.quantity) {
          throw new BadRequestException('Insufficient stock');
        }

        // Update stock atomically
        await tx.product.update({
          where: { id: item.productId },
          data: { stock: { decrement: item.quantity } },
        });

        // Create order item
        await tx.orderItem.create({
          data: {
            orderId: order.id,
            productId: item.productId,
            quantity: item.quantity,
            price: product.price,
          },
        });

        total += Number(product.price) * item.quantity;
      }

      // Update order total
      return tx.order.update({
        where: { id: order.id },
        data: { total },
        include: { items: { include: { product: true } } },
      });
    }, {
      maxWait: 5000,
      timeout: 10000,
      isolationLevel: Prisma.TransactionIsolationLevel.Serializable,
    });
  }
}
```

### Prisma with Raw Queries

```typescript
// For complex queries not easily expressed with Prisma Client
async getOrderStatistics(startDate: Date, endDate: Date) {
  return this.prisma.$queryRaw`
    SELECT
      DATE(created_at) as date,
      COUNT(*)::int as count,
      SUM(total)::decimal as total
    FROM orders
    WHERE created_at BETWEEN ${startDate} AND ${endDate}
      AND status = 'COMPLETED'
    GROUP BY DATE(created_at)
    ORDER BY date DESC
  `;
}

// Type-safe raw queries
interface OrderStats {
  date: Date;
  count: number;
  total: number;
}

async getTypedStats(): Promise<OrderStats[]> {
  return this.prisma.$queryRaw<OrderStats[]>`...`;
}
```

---

## Migrations

### TypeORM Migrations

```bash
# Generate migration
npm run typeorm migration:generate -- -n CreateUserTable

# Run migrations
npm run typeorm migration:run

# Revert last migration
npm run typeorm migration:revert

# Show migrations
npm run typeorm migration:show
```

```typescript
// migrations/1234567890-CreateUserTable.ts
export class CreateUserTable1234567890 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(
      new Table({
        name: 'users',
        columns: [
          {
            name: 'id',
            type: 'uuid',
            isPrimary: true,
            generationStrategy: 'uuid',
            default: 'uuid_generate_v4()',
          },
          { name: 'email', type: 'varchar', isUnique: true },
          { name: 'name', type: 'varchar' },
          { name: 'password', type: 'varchar' },
          {
            name: 'status',
            type: 'enum',
            enum: ['ACTIVE', 'INACTIVE', 'BANNED'],
            default: "'ACTIVE'",
          },
          { name: 'created_at', type: 'timestamp', default: 'now()' },
          { name: 'updated_at', type: 'timestamp', default: 'now()' },
          { name: 'deleted_at', type: 'timestamp', isNullable: true },
        ],
      }),
    );

    await queryRunner.createIndex(
      'users',
      new TableIndex({ columnNames: ['email'] }),
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('users');
  }
}
```

### Prisma Migrations

```bash
# Create migration
npx prisma migrate dev --name init

# Apply migrations (production)
npx prisma migrate deploy

# Reset database
npx prisma migrate reset

# Generate client
npx prisma generate

# View migration status
npx prisma migrate status
```

---

## Performance

### Query Optimization

```typescript
// Select only needed fields
const users = await this.repo.find({
  select: ['id', 'name', 'email'],
  where: { status: 'ACTIVE' },
});

// Prisma select
const users = await this.prisma.user.findMany({
  select: { id: true, name: true, email: true },
  where: { status: 'ACTIVE' },
});

// Use indexes
@Entity()
@Index(['email', 'status'])
@Index(['createdAt'])
export class User {
  // ...
}

// Avoid N+1 with eager loading
const orders = await this.orderRepo.find({
  relations: ['items', 'items.product'],
  where: { userId },
});

// Prisma include
const orders = await this.prisma.order.findMany({
  include: { items: { include: { product: true } } },
  where: { userId },
});
```

### Batch Operations

```typescript
// TypeORM bulk insert
await this.repo
  .createQueryBuilder()
  .insert()
  .into(User)
  .values(users)
  .execute();

// TypeORM bulk update
await this.repo
  .createQueryBuilder()
  .update(User)
  .set({ status: UserStatus.INACTIVE })
  .whereInIds(userIds)
  .execute();

// Prisma createMany
await this.prisma.user.createMany({
  data: users,
  skipDuplicates: true,
});

// Prisma updateMany
await this.prisma.user.updateMany({
  where: { id: { in: userIds } },
  data: { status: 'INACTIVE' },
});
```

### Caching

```typescript
// With TypeORM query cache
const user = await this.repo.findOne({
  where: { id },
  cache: {
    id: `user_${id}`,
    milliseconds: 60000,
  },
});

// With Redis cache (manual)
@Injectable()
export class CachedUserRepository {
  constructor(
    private prisma: PrismaService,
    @Inject(CACHE_MANAGER) private cache: Cache,
  ) {}

  async findById(id: string): Promise<User | null> {
    const cacheKey = `user:${id}`;

    const cached = await this.cache.get<User>(cacheKey);
    if (cached) return cached;

    const user = await this.prisma.user.findUnique({ where: { id } });
    if (user) {
      await this.cache.set(cacheKey, user, 60000);
    }
    return user;
  }

  async invalidate(id: string): Promise<void> {
    await this.cache.del(`user:${id}`);
  }
}
```

### Connection Pooling

```typescript
// TypeORM
TypeOrmModule.forRoot({
  // ...
  extra: {
    max: 20,              // Max connections
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
  },
});

// Prisma - configure in connection string
// DATABASE_URL="postgresql://user:pass@host:5432/db?connection_limit=20&pool_timeout=30"
```

## F5 Quality Gates Mapping

| Gate | Database Deliverable |
|------|---------------------|
| D3 | Entity relationships, schema design |
| D4 | Repository interfaces, migration plan |
| G3 | Repository unit tests, transaction tests |
| G4 | Database performance tests, load tests |
