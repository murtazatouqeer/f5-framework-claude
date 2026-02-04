# NestJS Performance Optimization

Performance patterns and optimization strategies for NestJS applications.

## Caching Strategies

### In-Memory Cache

```typescript
// app.module.ts
import { CacheModule } from '@nestjs/cache-manager';

@Module({
  imports: [
    CacheModule.register({
      ttl: 60,      // seconds
      max: 100,     // max items in cache
      isGlobal: true,
    }),
  ],
})
export class AppModule {}

// Using cache in service
@Injectable()
export class UserService {
  constructor(
    @Inject(CACHE_MANAGER)
    private cacheManager: Cache,
    private readonly userRepository: UserRepository,
  ) {}

  async findById(id: string): Promise<User> {
    const cacheKey = `user:${id}`;

    // Check cache first
    const cached = await this.cacheManager.get<User>(cacheKey);
    if (cached) {
      return cached;
    }

    // Fetch from database
    const user = await this.userRepository.findById(id);
    if (user) {
      await this.cacheManager.set(cacheKey, user, 300); // 5 min TTL
    }

    return user;
  }

  async update(id: string, dto: UpdateUserDto): Promise<User> {
    const user = await this.userRepository.update(id, dto);

    // Invalidate cache
    await this.cacheManager.del(`user:${id}`);

    return user;
  }
}
```

### Redis Cache

```typescript
// app.module.ts
import * as redisStore from 'cache-manager-redis-store';

@Module({
  imports: [
    CacheModule.registerAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        store: redisStore,
        host: config.get('REDIS_HOST'),
        port: config.get('REDIS_PORT'),
        password: config.get('REDIS_PASSWORD'),
        ttl: 60,
      }),
    }),
  ],
})
export class AppModule {}
```

### Cache Interceptor

```typescript
// Auto-cache controller responses
@Controller('products')
@UseInterceptors(CacheInterceptor)
export class ProductsController {
  @Get()
  @CacheTTL(300) // 5 minutes
  @CacheKey('all-products')
  findAll(): Promise<Product[]> {
    return this.productsService.findAll();
  }
}

// Custom cache key generator
@Injectable()
export class CustomCacheInterceptor extends CacheInterceptor {
  trackBy(context: ExecutionContext): string | undefined {
    const request = context.switchToHttp().getRequest();
    const { method, url, query, user } = request;

    // Include user ID in cache key for user-specific data
    return `${method}-${url}-${JSON.stringify(query)}-${user?.id || 'anon'}`;
  }
}
```

## Queue Processing

### Bull Queue Setup

```typescript
// app.module.ts
import { BullModule } from '@nestjs/bull';

@Module({
  imports: [
    BullModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        redis: {
          host: config.get('REDIS_HOST'),
          port: config.get('REDIS_PORT'),
        },
        defaultJobOptions: {
          attempts: 3,
          backoff: {
            type: 'exponential',
            delay: 1000,
          },
          removeOnComplete: true,
          removeOnFail: false,
        },
      }),
    }),
    BullModule.registerQueue(
      { name: 'email' },
      { name: 'notification' },
      { name: 'report' },
    ),
  ],
})
export class AppModule {}
```

### Queue Producer

```typescript
// services/email.service.ts
@Injectable()
export class EmailService {
  constructor(
    @InjectQueue('email')
    private readonly emailQueue: Queue,
  ) {}

  async sendWelcomeEmail(user: User): Promise<void> {
    await this.emailQueue.add('welcome', {
      to: user.email,
      name: user.name,
    }, {
      priority: 1,
      delay: 0,
    });
  }

  async sendBulkEmails(users: User[], template: string): Promise<void> {
    const jobs = users.map((user) => ({
      name: 'bulk',
      data: { to: user.email, template },
      opts: { priority: 2 },
    }));

    await this.emailQueue.addBulk(jobs);
  }

  async scheduleEmail(email: EmailDto, sendAt: Date): Promise<void> {
    const delay = sendAt.getTime() - Date.now();
    await this.emailQueue.add('scheduled', email, { delay });
  }
}
```

### Queue Consumer

```typescript
// processors/email.processor.ts
@Processor('email')
export class EmailProcessor {
  private readonly logger = new Logger(EmailProcessor.name);

  constructor(
    private readonly mailerService: MailerService,
  ) {}

  @Process('welcome')
  async handleWelcomeEmail(job: Job<WelcomeEmailData>): Promise<void> {
    const { to, name } = job.data;

    try {
      await this.mailerService.sendMail({
        to,
        subject: 'Welcome!',
        template: 'welcome',
        context: { name },
      });

      this.logger.log(`Welcome email sent to ${to}`);
    } catch (error) {
      this.logger.error(`Failed to send email to ${to}`, error);
      throw error; // Will trigger retry
    }
  }

  @Process('bulk')
  async handleBulkEmail(job: Job<BulkEmailData>): Promise<void> {
    // Process with rate limiting
    await this.mailerService.sendMail(job.data);
  }

  @OnQueueCompleted()
  onCompleted(job: Job): void {
    this.logger.debug(`Job ${job.id} completed`);
  }

  @OnQueueFailed()
  onFailed(job: Job, error: Error): void {
    this.logger.error(`Job ${job.id} failed: ${error.message}`);
  }
}
```

## Database Optimization

### Connection Pooling

```typescript
// TypeORM
TypeOrmModule.forRoot({
  type: 'postgres',
  // ... other options
  extra: {
    max: 20,           // max connections in pool
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
  },
})

// Prisma
// In prisma/schema.prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  connectionLimit = 20
}
```

### Query Optimization

```typescript
// Use select to fetch only needed fields
async findUsers(): Promise<UserSummary[]> {
  return this.repo
    .createQueryBuilder('user')
    .select(['user.id', 'user.name', 'user.email'])
    .getMany();
}

// Use pagination for large datasets
async findAll(pagination: PaginationDto): Promise<[User[], number]> {
  return this.repo.findAndCount({
    skip: (pagination.page - 1) * pagination.limit,
    take: pagination.limit,
    order: { createdAt: 'DESC' },
  });
}

// Use indexes
@Entity()
@Index(['status', 'createdAt'])
@Index(['email'], { unique: true })
export class User {}

// Batch operations
async updateMany(ids: string[], data: Partial<User>): Promise<void> {
  await this.repo
    .createQueryBuilder()
    .update(User)
    .set(data)
    .whereInIds(ids)
    .execute();
}
```

## Response Optimization

### Compression

```typescript
// main.ts
import compression from 'compression';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.use(compression({
    level: 6,
    threshold: 1024, // Only compress responses > 1KB
    filter: (req, res) => {
      if (req.headers['x-no-compression']) {
        return false;
      }
      return compression.filter(req, res);
    },
  }));

  await app.listen(3000);
}
```

### Response Serialization

```typescript
// common/interceptors/transform.interceptor.ts
@Injectable()
export class TransformInterceptor<T>
  implements NestInterceptor<T, Response<T>>
{
  intercept(
    context: ExecutionContext,
    next: CallHandler,
  ): Observable<Response<T>> {
    return next.handle().pipe(
      map((data) => ({
        data,
        timestamp: new Date().toISOString(),
      })),
    );
  }
}

// Exclude fields from response
export class UserResponseDto {
  @Expose()
  id: string;

  @Expose()
  email: string;

  @Exclude()
  passwordHash: string; // Never sent to client
}

// Usage with ClassSerializerInterceptor
@UseInterceptors(ClassSerializerInterceptor)
@SerializeOptions({ excludeExtraneousValues: true })
@Get(':id')
findOne(@Param('id') id: string): Promise<UserResponseDto> {
  return this.userService.findOne(id);
}
```

## Async Processing

### Event Emitter

```typescript
// app.module.ts
import { EventEmitterModule } from '@nestjs/event-emitter';

@Module({
  imports: [
    EventEmitterModule.forRoot({
      wildcard: true,
      maxListeners: 10,
    }),
  ],
})
export class AppModule {}

// Publishing events
@Injectable()
export class OrderService {
  constructor(private eventEmitter: EventEmitter2) {}

  async createOrder(dto: CreateOrderDto): Promise<Order> {
    const order = await this.orderRepository.create(dto);

    // Fire and forget - don't await
    this.eventEmitter.emit('order.created', new OrderCreatedEvent(order));

    return order;
  }
}

// Listening to events
@Injectable()
export class NotificationListener {
  @OnEvent('order.created')
  async handleOrderCreated(event: OrderCreatedEvent): Promise<void> {
    await this.notificationService.sendOrderConfirmation(event.order);
  }

  @OnEvent('order.**') // Wildcard listener
  async handleAllOrderEvents(event: any): Promise<void> {
    await this.analyticsService.trackOrderEvent(event);
  }
}
```

## Microservices Scaling

### Horizontal Scaling

```typescript
// main.ts - Running multiple instances
async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Use sticky sessions or stateless design
  app.use(
    session({
      store: new RedisStore({ client: redisClient }),
      // ...
    }),
  );

  // Health check for load balancer
  app.get('/health', (req, res) => {
    res.status(200).send('OK');
  });

  await app.listen(process.env.PORT || 3000);
}
```

### Request Timeout

```typescript
// Custom timeout interceptor
@Injectable()
export class TimeoutInterceptor implements NestInterceptor {
  constructor(
    @Inject('TIMEOUT_VALUE')
    private readonly timeout: number = 30000,
  ) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      timeout(this.timeout),
      catchError((err) => {
        if (err instanceof TimeoutError) {
          throw new RequestTimeoutException('Request timeout');
        }
        throw err;
      }),
    );
  }
}
```

## Performance Monitoring

### Metrics with Prometheus

```typescript
// metrics/metrics.service.ts
import { Injectable } from '@nestjs/common';
import { Counter, Histogram, Registry } from 'prom-client';

@Injectable()
export class MetricsService {
  private readonly registry: Registry;
  private readonly httpRequestDuration: Histogram;
  private readonly httpRequestTotal: Counter;

  constructor() {
    this.registry = new Registry();

    this.httpRequestDuration = new Histogram({
      name: 'http_request_duration_seconds',
      help: 'Duration of HTTP requests in seconds',
      labelNames: ['method', 'route', 'status_code'],
      buckets: [0.1, 0.3, 0.5, 1, 3, 5, 10],
      registers: [this.registry],
    });

    this.httpRequestTotal = new Counter({
      name: 'http_requests_total',
      help: 'Total number of HTTP requests',
      labelNames: ['method', 'route', 'status_code'],
      registers: [this.registry],
    });
  }

  recordRequest(method: string, route: string, statusCode: number, duration: number): void {
    this.httpRequestDuration.observe(
      { method, route, status_code: statusCode.toString() },
      duration / 1000,
    );
    this.httpRequestTotal.inc({ method, route, status_code: statusCode.toString() });
  }

  getMetrics(): Promise<string> {
    return this.registry.metrics();
  }
}
```

## Performance Checklist

### Application Level
- [ ] Enable response compression (gzip/brotli)
- [ ] Implement caching (Redis for production)
- [ ] Use connection pooling
- [ ] Enable keep-alive connections
- [ ] Set appropriate timeouts

### Database Level
- [ ] Add indexes for frequently queried columns
- [ ] Use pagination for large datasets
- [ ] Select only required fields
- [ ] Use batch operations for bulk updates
- [ ] Implement query caching

### Async Processing
- [ ] Use queues for heavy operations
- [ ] Implement event-driven architecture
- [ ] Offload non-critical tasks

### Monitoring
- [ ] Set up APM (New Relic, Datadog)
- [ ] Implement health checks
- [ ] Track response times
- [ ] Monitor error rates

## F5 Quality Gate Integration

| Gate | Performance Requirement |
|------|------------------------|
| G3 | Response time < 200ms for 95th percentile |
| G4 | Load test: 1000 concurrent users |
| G4 | Memory usage < 512MB under load |
