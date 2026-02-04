# NestJS Module Template

## Module Structure

```
src/modules/{{module-name}}/
├── {{module-name}}.module.ts
├── {{module-name}}.controller.ts
├── {{module-name}}.service.ts
├── dto/
│   ├── create-{{entity}}.dto.ts
│   ├── update-{{entity}}.dto.ts
│   └── {{entity}}-response.dto.ts
├── entities/
│   └── {{entity}}.entity.ts
├── interfaces/
│   └── {{entity}}.interface.ts
└── __tests__/
    ├── {{module-name}}.controller.spec.ts
    └── {{module-name}}.service.spec.ts
```

## Module Definition

```typescript
// {{module-name}}.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { {{EntityName}}Controller } from './{{module-name}}.controller';
import { {{EntityName}}Service } from './{{module-name}}.service';
import { {{EntityName}} } from './entities/{{entity}}.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([{{EntityName}}]),
  ],
  controllers: [{{EntityName}}Controller],
  providers: [{{EntityName}}Service],
  exports: [{{EntityName}}Service],
})
export class {{ModuleName}}Module {}
```

## Entity Definition

```typescript
// entities/{{entity}}.entity.ts
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  DeleteDateColumn,
  Index,
} from 'typeorm';

@Entity('{{table_name}}')
export class {{EntityName}} {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  // Add your columns here
  @Column()
  @Index()
  name: string;

  @Column({ nullable: true })
  description?: string;

  @Column({ default: true })
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @DeleteDateColumn()
  deletedAt?: Date;
}
```

## DTOs

### Create DTO
```typescript
// dto/create-{{entity}}.dto.ts
import { IsString, IsNotEmpty, IsOptional, IsBoolean, MaxLength } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class Create{{EntityName}}Dto {
  @ApiProperty({ description: 'Name of the {{entity}}', maxLength: 255 })
  @IsString()
  @IsNotEmpty()
  @MaxLength(255)
  name: string;

  @ApiPropertyOptional({ description: 'Description' })
  @IsString()
  @IsOptional()
  @MaxLength(1000)
  description?: string;

  @ApiPropertyOptional({ description: 'Active status', default: true })
  @IsBoolean()
  @IsOptional()
  isActive?: boolean;
}
```

### Update DTO
```typescript
// dto/update-{{entity}}.dto.ts
import { PartialType } from '@nestjs/swagger';
import { Create{{EntityName}}Dto } from './create-{{entity}}.dto';

export class Update{{EntityName}}Dto extends PartialType(Create{{EntityName}}Dto) {}
```

### Response DTO
```typescript
// dto/{{entity}}-response.dto.ts
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { Exclude, Expose } from 'class-transformer';

@Exclude()
export class {{EntityName}}ResponseDto {
  @Expose()
  @ApiProperty()
  id: string;

  @Expose()
  @ApiProperty()
  name: string;

  @Expose()
  @ApiPropertyOptional()
  description?: string;

  @Expose()
  @ApiProperty()
  isActive: boolean;

  @Expose()
  @ApiProperty()
  createdAt: Date;

  @Expose()
  @ApiProperty()
  updatedAt: Date;

  constructor(partial: Partial<{{EntityName}}ResponseDto>) {
    Object.assign(this, partial);
  }
}
```

## Service

```typescript
// {{module-name}}.service.ts
import { Injectable, NotFoundException, ConflictException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, FindOptionsWhere } from 'typeorm';
import { {{EntityName}} } from './entities/{{entity}}.entity';
import { Create{{EntityName}}Dto } from './dto/create-{{entity}}.dto';
import { Update{{EntityName}}Dto } from './dto/update-{{entity}}.dto';
import { {{EntityName}}ResponseDto } from './dto/{{entity}}-response.dto';

export interface PaginationOptions {
  page?: number;
  limit?: number;
  search?: string;
}

export interface PaginatedResult<T> {
  items: T[];
  meta: {
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  };
}

@Injectable()
export class {{EntityName}}Service {
  constructor(
    @InjectRepository({{EntityName}})
    private readonly repository: Repository<{{EntityName}}>,
  ) {}

  async create(dto: Create{{EntityName}}Dto): Promise<{{EntityName}}ResponseDto> {
    // Check for duplicates if needed
    const existing = await this.repository.findOne({
      where: { name: dto.name },
    });
    if (existing) {
      throw new ConflictException('{{EntityName}} with this name already exists');
    }

    const entity = this.repository.create(dto);
    const saved = await this.repository.save(entity);
    return new {{EntityName}}ResponseDto(saved);
  }

  async findAll(options: PaginationOptions = {}): Promise<PaginatedResult<{{EntityName}}ResponseDto>> {
    const { page = 1, limit = 10, search } = options;

    const queryBuilder = this.repository.createQueryBuilder('entity');

    if (search) {
      queryBuilder.where('entity.name ILIKE :search', { search: `%${search}%` });
    }

    queryBuilder
      .orderBy('entity.createdAt', 'DESC')
      .skip((page - 1) * limit)
      .take(limit);

    const [items, total] = await queryBuilder.getManyAndCount();

    return {
      items: items.map(item => new {{EntityName}}ResponseDto(item)),
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async findOne(id: string): Promise<{{EntityName}}ResponseDto> {
    const entity = await this.repository.findOne({ where: { id } });
    if (!entity) {
      throw new NotFoundException(`{{EntityName}} with ID ${id} not found`);
    }
    return new {{EntityName}}ResponseDto(entity);
  }

  async findByName(name: string): Promise<{{EntityName}}ResponseDto | null> {
    const entity = await this.repository.findOne({ where: { name } });
    return entity ? new {{EntityName}}ResponseDto(entity) : null;
  }

  async update(id: string, dto: Update{{EntityName}}Dto): Promise<{{EntityName}}ResponseDto> {
    const entity = await this.repository.findOne({ where: { id } });
    if (!entity) {
      throw new NotFoundException(`{{EntityName}} with ID ${id} not found`);
    }

    // Check for duplicates if name is being updated
    if (dto.name && dto.name !== entity.name) {
      const existing = await this.repository.findOne({
        where: { name: dto.name },
      });
      if (existing) {
        throw new ConflictException('{{EntityName}} with this name already exists');
      }
    }

    Object.assign(entity, dto);
    const saved = await this.repository.save(entity);
    return new {{EntityName}}ResponseDto(saved);
  }

  async remove(id: string): Promise<void> {
    const result = await this.repository.softDelete(id);
    if (result.affected === 0) {
      throw new NotFoundException(`{{EntityName}} with ID ${id} not found`);
    }
  }

  async hardRemove(id: string): Promise<void> {
    const result = await this.repository.delete(id);
    if (result.affected === 0) {
      throw new NotFoundException(`{{EntityName}} with ID ${id} not found`);
    }
  }
}
```

## Controller

```typescript
// {{module-name}}.controller.ts
import {
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Body,
  Param,
  Query,
  HttpCode,
  HttpStatus,
  UseGuards,
  ParseUUIDPipe,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBearerAuth,
  ApiParam,
  ApiQuery,
} from '@nestjs/swagger';
import { JwtAuthGuard } from '@/auth/guards/jwt-auth.guard';
import { {{EntityName}}Service, PaginationOptions, PaginatedResult } from './{{module-name}}.service';
import { Create{{EntityName}}Dto } from './dto/create-{{entity}}.dto';
import { Update{{EntityName}}Dto } from './dto/update-{{entity}}.dto';
import { {{EntityName}}ResponseDto } from './dto/{{entity}}-response.dto';

@ApiTags('{{module-name}}')
@Controller('{{module-name}}')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class {{EntityName}}Controller {
  constructor(private readonly service: {{EntityName}}Service) {}

  @Post()
  @ApiOperation({ summary: 'Create a new {{entity}}' })
  @ApiResponse({ status: 201, description: 'Created', type: {{EntityName}}ResponseDto })
  @ApiResponse({ status: 400, description: 'Validation error' })
  @ApiResponse({ status: 409, description: 'Conflict' })
  async create(@Body() dto: Create{{EntityName}}Dto): Promise<{{EntityName}}ResponseDto> {
    return this.service.create(dto);
  }

  @Get()
  @ApiOperation({ summary: 'Get all {{entity}}s' })
  @ApiQuery({ name: 'page', required: false, type: Number, example: 1 })
  @ApiQuery({ name: 'limit', required: false, type: Number, example: 10 })
  @ApiQuery({ name: 'search', required: false, type: String })
  @ApiResponse({ status: 200, description: 'List of {{entity}}s' })
  async findAll(
    @Query('page') page?: number,
    @Query('limit') limit?: number,
    @Query('search') search?: string,
  ): Promise<PaginatedResult<{{EntityName}}ResponseDto>> {
    return this.service.findAll({ page, limit, search });
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get {{entity}} by ID' })
  @ApiParam({ name: 'id', type: String, format: 'uuid' })
  @ApiResponse({ status: 200, description: 'Found', type: {{EntityName}}ResponseDto })
  @ApiResponse({ status: 404, description: 'Not found' })
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<{{EntityName}}ResponseDto> {
    return this.service.findOne(id);
  }

  @Put(':id')
  @ApiOperation({ summary: 'Update {{entity}}' })
  @ApiParam({ name: 'id', type: String, format: 'uuid' })
  @ApiResponse({ status: 200, description: 'Updated', type: {{EntityName}}ResponseDto })
  @ApiResponse({ status: 404, description: 'Not found' })
  async update(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: Update{{EntityName}}Dto,
  ): Promise<{{EntityName}}ResponseDto> {
    return this.service.update(id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Delete {{entity}}' })
  @ApiParam({ name: 'id', type: String, format: 'uuid' })
  @ApiResponse({ status: 204, description: 'Deleted' })
  @ApiResponse({ status: 404, description: 'Not found' })
  async remove(@Param('id', ParseUUIDPipe) id: string): Promise<void> {
    return this.service.remove(id);
  }
}
```

## Checklist

- [ ] Entity with proper decorators
- [ ] DTOs with validation
- [ ] Service with CRUD operations
- [ ] Controller with OpenAPI docs
- [ ] Module registration
- [ ] Unit tests
- [ ] E2E tests
