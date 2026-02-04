---
name: nestjs-repository
description: NestJS repository pattern template
applies_to: nestjs
category: template
---

# NestJS Repository Template

## Repository Interface

```typescript
// modules/{{module}}/interfaces/{{entity}}-repository.interface.ts
import { {{Entity}} } from '../entities/{{entity}}.entity';
import { Create{{Entity}}Dto } from '../dto/create-{{entity}}.dto';
import { Update{{Entity}}Dto } from '../dto/update-{{entity}}.dto';
import { Query{{Entity}}Dto } from '../dto/query-{{entity}}.dto';

export interface I{{Entity}}Repository {
  create(data: Create{{Entity}}Dto): Promise<{{Entity}}>;
  findById(id: string): Promise<{{Entity}} | null>;
  findAll(query: Query{{Entity}}Dto): Promise<{
    items: {{Entity}}[];
    total: number;
  }>;
  update(id: string, data: Update{{Entity}}Dto): Promise<{{Entity}}>;
  delete(id: string): Promise<void>;
  exists(id: string): Promise<boolean>;
}

export const {{ENTITY}}_REPOSITORY = Symbol('{{ENTITY}}_REPOSITORY');
```

## TypeORM Repository Implementation

```typescript
// modules/{{module}}/repositories/{{entity}}.repository.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, FindOptionsWhere, ILike } from 'typeorm';
import { {{Entity}} } from '../entities/{{entity}}.entity';
import { I{{Entity}}Repository } from '../interfaces/{{entity}}-repository.interface';
import { Create{{Entity}}Dto } from '../dto/create-{{entity}}.dto';
import { Update{{Entity}}Dto } from '../dto/update-{{entity}}.dto';
import { Query{{Entity}}Dto } from '../dto/query-{{entity}}.dto';

@Injectable()
export class {{Entity}}Repository implements I{{Entity}}Repository {
  constructor(
    @InjectRepository({{Entity}})
    private readonly repository: Repository<{{Entity}}>,
  ) {}

  async create(data: Create{{Entity}}Dto): Promise<{{Entity}}> {
    const entity = this.repository.create(data);
    return this.repository.save(entity);
  }

  async findById(id: string): Promise<{{Entity}} | null> {
    return this.repository.findOne({
      where: { id },
      relations: ['{{relation}}'],
    });
  }

  async findByField(field: string, value: any): Promise<{{Entity}} | null> {
    return this.repository.findOne({
      where: { [field]: value } as FindOptionsWhere<{{Entity}}>,
    });
  }

  async findAll(query: Query{{Entity}}Dto): Promise<{
    items: {{Entity}}[];
    total: number;
  }> {
    const { page = 1, limit = 10, search, sortBy, sortOrder } = query;
    const skip = (page - 1) * limit;

    const queryBuilder = this.repository.createQueryBuilder('{{entity}}');

    // Add search
    if (search) {
      queryBuilder.where(
        '{{entity}}.{{searchField}} ILIKE :search',
        { search: `%${search}%` },
      );
    }

    // Add sorting
    if (sortBy) {
      queryBuilder.orderBy(
        `{{entity}}.${sortBy}`,
        sortOrder?.toUpperCase() as 'ASC' | 'DESC',
      );
    }

    // Add pagination
    queryBuilder.skip(skip).take(limit);

    // Add relations
    queryBuilder.leftJoinAndSelect('{{entity}}.{{relation}}', '{{relation}}');

    const [items, total] = await queryBuilder.getManyAndCount();

    return { items, total };
  }

  async update(id: string, data: Update{{Entity}}Dto): Promise<{{Entity}}> {
    await this.repository.update(id, data);
    return this.findById(id);
  }

  async delete(id: string): Promise<void> {
    await this.repository.softDelete(id);
  }

  async hardDelete(id: string): Promise<void> {
    await this.repository.delete(id);
  }

  async exists(id: string): Promise<boolean> {
    const count = await this.repository.count({ where: { id } });
    return count > 0;
  }

  async count(where?: FindOptionsWhere<{{Entity}}>): Promise<number> {
    return this.repository.count({ where });
  }

  async findByIds(ids: string[]): Promise<{{Entity}}[]> {
    return this.repository.findByIds(ids);
  }

  async bulkCreate(data: Create{{Entity}}Dto[]): Promise<{{Entity}}[]> {
    const entities = this.repository.create(data);
    return this.repository.save(entities);
  }

  async bulkUpdate(
    ids: string[],
    data: Partial<Update{{Entity}}Dto>,
  ): Promise<void> {
    await this.repository
      .createQueryBuilder()
      .update({{Entity}})
      .set(data)
      .whereInIds(ids)
      .execute();
  }
}
```

## Custom Query Methods

```typescript
// modules/{{module}}/repositories/{{entity}}.repository.ts (extended)

// Add to repository class
async findActive(): Promise<{{Entity}}[]> {
  return this.repository.find({
    where: { isActive: true },
    order: { createdAt: 'DESC' },
  });
}

async findByDateRange(
  startDate: Date,
  endDate: Date,
): Promise<{{Entity}}[]> {
  return this.repository
    .createQueryBuilder('{{entity}}')
    .where('{{entity}}.createdAt BETWEEN :startDate AND :endDate', {
      startDate,
      endDate,
    })
    .getMany();
}

async findWithStats(): Promise<any[]> {
  return this.repository
    .createQueryBuilder('{{entity}}')
    .select('{{entity}}.status', 'status')
    .addSelect('COUNT(*)', 'count')
    .groupBy('{{entity}}.status')
    .getRawMany();
}

async findWithPagination(
  page: number,
  limit: number,
  filters?: Partial<{{Entity}}>,
): Promise<{ items: {{Entity}}[]; meta: PaginationMeta }> {
  const skip = (page - 1) * limit;

  const queryBuilder = this.repository.createQueryBuilder('{{entity}}');

  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        queryBuilder.andWhere(`{{entity}}.${key} = :${key}`, {
          [key]: value,
        });
      }
    });
  }

  const [items, total] = await queryBuilder
    .skip(skip)
    .take(limit)
    .getManyAndCount();

  return {
    items,
    meta: {
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
      hasNext: page * limit < total,
      hasPrevious: page > 1,
    },
  };
}
```

## Module Registration

```typescript
// modules/{{module}}/{{module}}.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { {{Entity}} } from './entities/{{entity}}.entity';
import { {{Entity}}Repository } from './repositories/{{entity}}.repository';
import { {{ENTITY}}_REPOSITORY } from './interfaces/{{entity}}-repository.interface';
import { {{Entity}}Service } from './{{entity}}.service';

@Module({
  imports: [TypeOrmModule.forFeature([{{Entity}}])],
  providers: [
    {{Entity}}Repository,
    {
      provide: {{ENTITY}}_REPOSITORY,
      useClass: {{Entity}}Repository,
    },
    {{Entity}}Service,
  ],
  exports: [{{ENTITY}}_REPOSITORY, {{Entity}}Service],
})
export class {{Module}}Module {}
```

## Service Using Repository

```typescript
// modules/{{module}}/{{entity}}.service.ts
import { Injectable, Inject, NotFoundException } from '@nestjs/common';
import {
  I{{Entity}}Repository,
  {{ENTITY}}_REPOSITORY,
} from './interfaces/{{entity}}-repository.interface';
import { Create{{Entity}}Dto } from './dto/create-{{entity}}.dto';
import { Update{{Entity}}Dto } from './dto/update-{{entity}}.dto';

@Injectable()
export class {{Entity}}Service {
  constructor(
    @Inject({{ENTITY}}_REPOSITORY)
    private readonly repository: I{{Entity}}Repository,
  ) {}

  async create(data: Create{{Entity}}Dto) {
    return this.repository.create(data);
  }

  async findById(id: string) {
    const entity = await this.repository.findById(id);
    if (!entity) {
      throw new NotFoundException(`{{Entity}} with ID ${id} not found`);
    }
    return entity;
  }

  async update(id: string, data: Update{{Entity}}Dto) {
    await this.findById(id); // Verify exists
    return this.repository.update(id, data);
  }

  async delete(id: string) {
    await this.findById(id); // Verify exists
    return this.repository.delete(id);
  }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{module}}` | Module name (lowercase) | users |
| `{{Module}}` | Module name (PascalCase) | Users |
| `{{entity}}` | Entity name (lowercase) | user |
| `{{Entity}}` | Entity name (PascalCase) | User |
| `{{ENTITY}}` | Entity name (UPPERCASE) | USER |
| `{{relation}}` | Related entity name | profile |
| `{{searchField}}` | Field to search | name |
