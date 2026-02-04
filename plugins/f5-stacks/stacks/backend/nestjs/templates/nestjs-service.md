# NestJS Service Template

A production-ready service template for NestJS applications.

## Basic Service Structure

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, DataSource } from 'typeorm';
import { EventEmitter2 } from '@nestjs/event-emitter';

@Injectable()
export class {{ServiceName}}Service {
  private readonly logger = new Logger({{ServiceName}}Service.name);

  constructor(
    @InjectRepository({{Entity}})
    private readonly repository: Repository<{{Entity}}>,
    private readonly dataSource: DataSource,
    private readonly eventEmitter: EventEmitter2,
  ) {}

  // Implementation methods
}
```

## Common Patterns

### Transaction Pattern
```typescript
async createWithRelations(dto: CreateDto): Promise<Entity> {
  const queryRunner = this.dataSource.createQueryRunner();
  await queryRunner.connect();
  await queryRunner.startTransaction();

  try {
    const entity = queryRunner.manager.create(Entity, dto);
    const saved = await queryRunner.manager.save(entity);

    // Create related entities
    const related = queryRunner.manager.create(RelatedEntity, {
      entityId: saved.id,
      ...dto.related,
    });
    await queryRunner.manager.save(related);

    await queryRunner.commitTransaction();
    this.eventEmitter.emit('entity.created', saved);
    return saved;
  } catch (error) {
    await queryRunner.rollbackTransaction();
    this.logger.error(`Failed to create entity: ${error.message}`, error.stack);
    throw error;
  } finally {
    await queryRunner.release();
  }
}
```

### Bulk Operations
```typescript
async createMany(dtos: CreateDto[]): Promise<Entity[]> {
  const entities = this.repository.create(dtos);
  return this.repository.save(entities, { chunk: 100 });
}

async updateMany(ids: string[], updates: Partial<Entity>): Promise<void> {
  await this.repository
    .createQueryBuilder()
    .update(Entity)
    .set(updates)
    .whereInIds(ids)
    .execute();
}
```

### Query Builder Pattern
```typescript
async findWithFilters(filters: FilterDto): Promise<PaginatedResult<Entity>> {
  const qb = this.repository.createQueryBuilder('e');

  // Dynamic filters
  if (filters.status) {
    qb.andWhere('e.status = :status', { status: filters.status });
  }

  if (filters.search) {
    qb.andWhere('(e.name ILIKE :search OR e.description ILIKE :search)', {
      search: `%${filters.search}%`,
    });
  }

  if (filters.dateFrom) {
    qb.andWhere('e.createdAt >= :dateFrom', { dateFrom: filters.dateFrom });
  }

  if (filters.dateTo) {
    qb.andWhere('e.createdAt <= :dateTo', { dateTo: filters.dateTo });
  }

  // Sorting
  const sortField = filters.sortBy || 'createdAt';
  const sortOrder = filters.sortOrder || 'DESC';
  qb.orderBy(`e.${sortField}`, sortOrder);

  // Pagination
  const page = filters.page || 1;
  const limit = filters.limit || 10;
  qb.skip((page - 1) * limit).take(limit);

  // Relations
  if (filters.includeRelations) {
    qb.leftJoinAndSelect('e.relations', 'relations');
  }

  const [items, total] = await qb.getManyAndCount();

  return {
    items,
    meta: { total, page, limit, totalPages: Math.ceil(total / limit) },
  };
}
```

### Caching Pattern
```typescript
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';

@Injectable()
export class CachedService {
  constructor(
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
    private readonly repository: Repository<Entity>,
  ) {}

  async findOne(id: string): Promise<Entity> {
    const cacheKey = `entity:${id}`;

    // Try cache first
    const cached = await this.cacheManager.get<Entity>(cacheKey);
    if (cached) return cached;

    // Fetch from database
    const entity = await this.repository.findOne({ where: { id } });
    if (!entity) throw new NotFoundException();

    // Store in cache (TTL: 5 minutes)
    await this.cacheManager.set(cacheKey, entity, 300_000);
    return entity;
  }

  async invalidateCache(id: string): Promise<void> {
    await this.cacheManager.del(`entity:${id}`);
  }
}
```

### Event-Driven Pattern
```typescript
// Service emitting events
async create(dto: CreateDto): Promise<Entity> {
  const entity = await this.repository.save(this.repository.create(dto));

  this.eventEmitter.emit('entity.created', {
    id: entity.id,
    timestamp: new Date(),
    data: entity,
  });

  return entity;
}

// Event listener
@Injectable()
export class EntityListener {
  private readonly logger = new Logger(EntityListener.name);

  @OnEvent('entity.created')
  async handleEntityCreated(payload: EntityCreatedEvent) {
    this.logger.log(`Entity created: ${payload.id}`);
    // Perform side effects (notifications, audit, etc.)
  }
}
```

### Retry Pattern
```typescript
import { retry } from 'rxjs/operators';
import { defer, lastValueFrom } from 'rxjs';

async callExternalService(data: any): Promise<any> {
  return lastValueFrom(
    defer(() => this.httpService.post('/api/external', data)).pipe(
      retry({
        count: 3,
        delay: (error, retryCount) => {
          this.logger.warn(`Retry attempt ${retryCount}: ${error.message}`);
          return timer(Math.pow(2, retryCount) * 1000); // Exponential backoff
        },
      }),
    ),
  );
}
```

### Soft Delete Pattern
```typescript
async softDelete(id: string): Promise<void> {
  const result = await this.repository.softDelete(id);
  if (result.affected === 0) {
    throw new NotFoundException();
  }
}

async restore(id: string): Promise<void> {
  const result = await this.repository.restore(id);
  if (result.affected === 0) {
    throw new NotFoundException();
  }
}

async findAllIncludingDeleted(): Promise<Entity[]> {
  return this.repository.find({ withDeleted: true });
}
```

## Service Testing Template

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { DataSource } from 'typeorm';

describe('{{ServiceName}}Service', () => {
  let service: {{ServiceName}}Service;
  let repository: jest.Mocked<Repository<Entity>>;
  let eventEmitter: jest.Mocked<EventEmitter2>;

  const mockRepository = {
    create: jest.fn(),
    save: jest.fn(),
    findOne: jest.fn(),
    findAndCount: jest.fn(),
    delete: jest.fn(),
    softDelete: jest.fn(),
    createQueryBuilder: jest.fn(() => ({
      where: jest.fn().mockReturnThis(),
      andWhere: jest.fn().mockReturnThis(),
      orderBy: jest.fn().mockReturnThis(),
      skip: jest.fn().mockReturnThis(),
      take: jest.fn().mockReturnThis(),
      getManyAndCount: jest.fn(),
    })),
  };

  const mockEventEmitter = {
    emit: jest.fn(),
  };

  const mockDataSource = {
    createQueryRunner: jest.fn(() => ({
      connect: jest.fn(),
      startTransaction: jest.fn(),
      commitTransaction: jest.fn(),
      rollbackTransaction: jest.fn(),
      release: jest.fn(),
      manager: {
        create: jest.fn(),
        save: jest.fn(),
      },
    })),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        {{ServiceName}}Service,
        { provide: getRepositoryToken(Entity), useValue: mockRepository },
        { provide: EventEmitter2, useValue: mockEventEmitter },
        { provide: DataSource, useValue: mockDataSource },
      ],
    }).compile();

    service = module.get({{ServiceName}}Service);
    repository = module.get(getRepositoryToken(Entity));
    eventEmitter = module.get(EventEmitter2);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  // Add specific test cases
});
```
